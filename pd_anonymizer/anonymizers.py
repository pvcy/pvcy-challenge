import logging
from dataclasses import dataclass
from functools import partial
from typing import Dict, List

import numpy as np
import pandas as pd
from category_encoders import CountEncoder
from sklearn.impute import SimpleImputer

from .neighbors import NumericalLSHForest

log = logging.getLogger(__name__)


# ==================================================================================
# Anonymizers
# ==================================================================================

class KAnonymizer:

    def __init__(
            self,
            cat_columns=None,
            num_columns=None,
            linked_columns=None,
            transform_exclude=None,
            ann_index_exclude=None,
            ann_index_exclude_child_columns=False,
            k_target=5,
            pu_col=None,
            n_trees=80):
        """
        K-Anonymity for mixed categorical/numerical vectors treating target columns as
        what defines equivalence classes, and seeks possible merges among eq. classes
        using a nearest neighbor index.

        :param cat_columns: Categorical columns
        :param num_columns: Numerical columns
        :param linked_columns: During transformation, linked columns will be populated
        with values from the row selected for the primary column.
        :param transform_exclude: Columns to leave unmodified during transformation
        :param ann_index_exclude: Columns to exclude from neighbor distance calculations
        :param ann_index_exclude_child_columns: Automatically exclude child columns defined
        in linked_columns from ANN index (keeping primary linked columns).
        :param k_target: The k-anonymity target
        :param pu_col: A column name representing the privacy unit
        :param n_trees: The number of trees in the NN index
        """
        self._init_column_targets(
            cat_columns, num_columns,
            linked_columns or {},
            transform_exclude or [],
            ann_index_exclude,
            ann_index_exclude_child_columns
        )
        self.pu_col = pu_col
        self.k_target = k_target
        self.n_trees = n_trees
        self._numlsh = NumericalLSHForest(n_trees=n_trees)
        self._num_imputer = SimpleImputer(strategy="median")
        self._cat_encoder = CountEncoder(normalize=True)
        self._eq_counts = None
        self._eq_encoded = None
        self._eq_lookup = None
        self._eq_groups = None

    @dataclass
    class Group:
        __slots__ = ['k_count', 'eq_classes']
        k_count: int
        eq_classes: list

    def _init_column_targets(
            self,
            cat_columns: list,
            num_columns: list,
            linked_columns: Dict[str, List[str]],
            transform_exclude: list, ann_index_exclude: list,
            ann_index_exclude_child_columns: bool):
        """
        Column config initializer
        """
        self.cat_columns = set(cat_columns or [])
        self.num_columns = set(num_columns or [])

        # Remove transform-excluded columns from class link config
        self.linked_columns = {}
        for k, v in linked_columns.items():
            v = [i for i in v if i not in transform_exclude]
            if v and k in transform_exclude:
                k, v = v[-1], v[:-1]  # Promote last value to key (assumes descending hierarchy)
            if v:
                self.linked_columns[k] = v

        # Child columns based on pre-exclusion link config
        self._child_columns = set(
            [c for cols in linked_columns.values() for c in cols]
            if linked_columns else []
        )

        self._eqclass_columns = self.cat_columns | self.num_columns

        if len(self._eqclass_columns) < (len(self.cat_columns) + len(self.num_columns)):
            raise ValueError("Category columns and numeric columns must contain"
                             " mutually exclusive values.")

        self._transform_columns = (self._eqclass_columns - set(transform_exclude or {}))
        self._ann_index_columns = (self._eqclass_columns - set(ann_index_exclude or {}))

        if ann_index_exclude_child_columns is True:
            self._ann_index_columns = self._ann_index_columns - self._child_columns

        if not self._ann_index_columns:
            raise ValueError("Must have at least one column for ANN index.")

        if not self._transform_columns:
            raise ValueError("Must have at least one column to transform.")

    def _init_eq_lookup(self, eq_counts: pd.DataFrame):
        """
        Construct Numpy record array index of EQClasses metadata.
        Row index maps to eqclass, row values are [original k_count, groupnum]
        """
        # eq_class index must be a 0-based range index
        assert (
                isinstance(eq_counts.index, pd.core.indexes.range.RangeIndex)
                and eq_counts.index.start == 0
                and eq_counts.index.step == 1
        )

        return pd.concat([
            eq_counts["k_count"],
            pd.Series(name="group", index=eq_counts.index),  # NB Group init => NaN
        ],
            axis=1).to_records(index=False)

    def _get_eq_counts(self, df: pd.DataFrame):
        # TODO Handle pu_col in _eqclass_columns
        index_func = (lambda x: x) if self.pu_col else pd.DataFrame.reset_index
        group_key = self.pu_col or "index"

        # Build index of EQ classes with counts
        # NB MultiIndex can't represent None, so it's coerced to np.nan
        eq_counts = (
            df.pipe(index_func)
                .groupby(list(self._eqclass_columns), sort=False, dropna=False)[group_key]
                .nunique()
                .reset_index()
                .rename(columns={group_key: "k_count"})
        )
        return eq_counts

    def _get_neighbors(self, idx):
        """
        Always queries k_target neighbors based on the worst case possibility
        that all neighboring eqclasses are k=1, and all of them need to be grouped
        to achieve k_target. (This overselects in most cases.)

        TODO Possible optimizations:
         - Factor in the size of the current group before querying
         - Query only for the number of neighbors needed such that the sum of their
          k_counts meets the target. What is the cost of querying iteratively vs
          in batches?
        """
        encoded = self._eq_encoded[idx, :].reshape(1, -1)
        nn_keys = self._numlsh.kneighbors(encoded, n_neighbors=self.k_target)[0]
        nn_keys = nn_keys[nn_keys != idx]  # Exclude self

        return nn_keys

    def _encode_data(self, df: pd.DataFrame, fit=True):
        """
        Preprocess data for ANN index
        """
        # Extract categorical/numerical data
        cat_arr = df[self.cat_columns & self._ann_index_columns].values
        num_arr = df[self.num_columns & self._ann_index_columns].values

        # Encode cat data as frequencies
        if cat_arr.shape[1] > 0:
            # CountEncoder ignores ints/floats
            cat_arr = cat_arr.astype(str)
            if fit:
                cat_arr = self._cat_encoder.fit_transform(cat_arr)
            else:
                cat_arr = self._cat_encoder.transform(cat_arr)

        # Impute NaNs for num data
        if num_arr.shape[1] > 0:
            if fit:
                num_arr = self._num_imputer.fit_transform(num_arr)
            else:
                num_arr = self._num_imputer.transform(num_arr)

        # Merge and return encoded eq. class data
        return np.concatenate([cat_arr, num_arr], axis=1)

    def fit(self, df: pd.DataFrame):
        """
        Build equivalence class merge-plan for input dataset.

        :param df: The dataframe to build a merge plan on
        :type df: pandas.DataFrame
        :return: Self
        :rtype: KAnonymizer

        TODO Reevaluate group index. Used to track group/k-count/eqclasses,
            but aren't needed in current impl.
        """
        if len(df) < self.k_target:
            raise ValueError("There are not enough rows to ensure k_target")

        # Initialize
        self._eq_counts = self._get_eq_counts(df)
        self._eq_lookup = self._init_eq_lookup(self._eq_counts)
        self._eq_groups = {}  # { group_number : Group }
        self._eq_encoded = self._encode_data(self._eq_counts, fit=True)  # TODO: This should be a numlsh concern

        # Build the NN index
        self._numlsh = self._numlsh.fit(self._eq_encoded)

        # Generate merge groups
        next_group = 0
        for this_idx, this_eqclass in enumerate(self._eq_lookup):

            # Skip eqclasses that meet criteria
            if (not np.isnan(this_eqclass.group)  # Already treated
                    or this_eqclass.k_count >= self.k_target):  # Safe eqclass
                continue

            nn_keys = self._get_neighbors(this_idx)  # Get neighbor keys (pre-sorted by distance ascending)
            neighbors = self._eq_lookup[nn_keys]
            group = [this_idx]
            group_k_current = this_eqclass.k_count

            for nn_idx, neighbor in zip(nn_keys, neighbors):

                # If there is a prior group, join it, it will meet the k_target
                if not np.isnan(neighbor.group):
                    neighbor_group = self._eq_groups[neighbor.group]
                    neighbor_group.eq_classes.append(this_idx)  # Add eqclass to group in group index
                    self._eq_lookup.group[this_idx] = neighbor.group  # Set new member's group in eqclass index
                    group_k_current = this_eqclass.k_count + neighbor_group.k_count
                    neighbor_group.k_count = group_k_current  # Update group k_count
                    break

                # Accumulate group
                group.append(nn_idx)
                group_k_current += neighbor.k_count  # NB We can assume neighbor is not grouped

                # Group meets req
                if group_k_current >= self.k_target:
                    self._eq_groups[next_group] = self.Group(group_k_current, group)  # Create group in group index
                    self._eq_lookup.group[group] = next_group  # Set all members' group in eqclass index
                    next_group += 1
                    break

        return self

    @staticmethod
    def mode_stable(s):
        """
        Returns a scalar for agg compatibility. If there are multiple modes,
        the first ascending value is returned. Use this if you need
        reproducibility (i.e. testing).
        """
        return s.mode(dropna=False).sort_values()[0]

    @staticmethod
    def mode_fair(s, index=False):
        """
        Returns a scalar for agg compatibility. If there are multiple modes,
        one is selected at random.
        """
        mode = np.random.choice(s.mode(dropna=False))
        if index:
            return s[s == mode].index[0]

        if pd.api.types.is_datetime64tz_dtype(s.dtype):
            # NB Work around https://github.com/pandas-dev/pandas/issues/41927
            return pd.Timestamp(mode, tz=s.dt.tz)
        else:
            return mode

    @staticmethod
    def median_single(s, index=False):
        """
        Similar to median(), but instead of taking the mean of the two middle
        values for even-length sequences, one is selected at random.
        NB Ignores nans
        """
        s_notnull = s.dropna()
        if s_notnull.empty:
            return np.nan

        n = len(s_notnull)
        if n % 2 == 0:
            mid = np.random.choice([int(n / 2), int(n / 2) - 1])
        else:
            mid = int(n / 2)
        idx = np.argsort(s_notnull.values)[mid]
        return s_notnull.index[idx] if index else s_notnull.iloc[idx]

    def default_agg_config(self):
        """
        Config defining functions used for choosing a replacement value for
        each column in a group. Linked column configs will replace primary
        column with index-based function and remove child/linked columns.
        """
        defaults = {
            **{col: self.median_single for col in self.num_columns & self._transform_columns},
            **{col: self.mode_fair for col in self.cat_columns & self._transform_columns}
        }
        # Handle linked columns
        for primary, linked in self.linked_columns.items():
            func = defaults.pop(primary)
            if func is not None:
                # Replace function with version that returns an index
                defaults[primary] = partial(func, index=True)
                # Exclude linked columns
                for col in linked:
                    if col in defaults: del defaults[col]

        return defaults

    def transform(self, df: pd.DataFrame):
        """
        Build replacement eqclasses for groups and reconstruct df.
        """
        self._eq_counts['group'] = self._eq_lookup['group']  # NB eq_lookup direct index mirrors eq_count labeled index
        agg_config = self.default_agg_config()
        treat_columns = self._transform_columns - self._child_columns

        # Build mapping of group => replacement eqclass values
        treated_groups = (
            self._eq_counts
                .drop(set(self._eqclass_columns) - treat_columns, axis='columns')
                .loc[self._eq_counts.index.repeat(self._eq_counts.k_count)]
                .drop(columns=['k_count'])
                .dropna(subset=['group'])
                .groupby('group', sort=False, dropna=False)
                .agg(agg_config)
        )

        # Lookup linked values based on primary col (key) and add to replacement eqclasses
        for primary, child in self.linked_columns.items():
            linked = [primary] + child
            treated_groups[linked] = (
                pd.merge(
                    treated_groups[[primary]].rename(columns={primary: 'eqclass_idx'}),
                    self._eq_counts,
                    how='left', left_on='eqclass_idx',
                    right_index=True
                )[linked]
            )

        # Build pseudo-index mapping input df index => group
        df_groups = (
            pd.merge(
                df.reset_index().fillna(np.nan),  # Conform None to nan to align with _eq_counts
                self._eq_counts,
                how="left",
                on=list(self._eqclass_columns)
            )['group']
        )

        # Preserve => keep original values from df
        preserve_columns = set(df.columns) - self._transform_columns

        # Build new df with replacement qid values
        df_treated_qids = (
            pd.merge(
                df_groups.reset_index(),
                treated_groups,
                on='group'
            )
                .drop(columns=preserve_columns, errors='ignore')
                .rename(columns={'index': None})
                .set_index(None)
        )

        # Join preserved columns to new df, remove group column TODO is this redundant with next step?
        df_treated_all = (
            pd.merge(
                df_treated_qids,
                df[preserve_columns],
                how='left',
                left_index=True,
                right_index=True
            )
                .drop(columns=['group'])
        )

        # Append untreated (safe) rows, reorder columns and rows
        df_combined = (
            pd.concat([
                df.loc[df.index.difference(df_treated_all.index)],
                df_treated_all
            ])[df.columns].sort_index()
        )

        return df_combined

    def fit_transform(self, df: pd.DataFrame):
        """
            Fit and then transform (anonymize) desired dataset.

            :param df: The dataframe to fit and apply to
            :type df: pandas.DataFrame
            :return: Modified dataframe
            :rtype: pandas.DataFrame
        """
        return self.fit(df).transform(df)
