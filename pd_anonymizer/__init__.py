from functools import lru_cache
from sys import float_info

import numpy as np
import pandas as pd
from fastkde import fastKDE
from pandas import DataFrame, Series


class HashableSeries(Series):
    uuid = __import__('uuid')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hash = None
        self.reset_hash()

    def reset_hash(self):
        self.hash = self.uuid.uuid4().int

    def __hash__(self):
        return self.hash

    def uniqueness(self):
        """
        Cardinality / row count
        """
        return 0 if len(self) == 0 else self.nunique(dropna=False) / len(self)

    @staticmethod
    def _mvalue_impl(series):
        """
        Statistical measure of data 'choppiness'
        """
        # If columns are all NaNs, m-value ~= 0
        if series.isnull().all():
            return float_info.epsilon

        # If range collapses, m-value ~= 0
        if series.min(skipna=True) == series.max(skipna=True):
            return float_info.epsilon

        frequencies, _ = fastKDE.pdf(series.dropna())  # Get KDE estimate
        diffs = np.diff(frequencies)  # Calculate differences between adjacent frequencies
        mvalue = np.abs(diffs).sum() / frequencies.max()

        return mvalue

    @lru_cache(maxsize=1)
    def mvalue(self):
        """
        "Public" mvalue function. Memoizes and handles datatype conversion
        """
        if pd.api.types.is_string_dtype(self):
            return self._mvalue_impl(
                self.astype(pd.api.types.CategoricalDtype()).cat.codes
            )

        if pd.api.types.is_datetime64tz_dtype(self):
            return self._mvalue_impl(
                self.dt.tz_convert(None)  # Convert to UTC and drop tz
            )

        return self._mvalue_impl(self)

    def nullity(self):
        """
        Percentage of null values
        """
        return self.isna().sum() / float(len(self))

    @staticmethod
    def safe_log(x):
        return np.log(x) if x > 0 else np.log(float_info.epsilon)

    def features(self):
        return [
            self.safe_log(x)
            for x in (self.nullity(), self.uniqueness(), self.mvalue())
        ]

    @lru_cache(maxsize=1)
    def nunique(self, dropna=True):
        return super().nunique(dropna)


class HashableDataFrame(DataFrame):
    """
    DataFrame subclass that implements hash, for use in memoization.
    Hash must be manually reset following mutate ops!
    TODO Does this constructor make a copy of the DataFrame?
    """

    @property
    def _constructor_expanddim(self):
        return super()._constructor_expanddim(self)

    @property
    def _constructor(self):
        return HashableDataFrame

    @property
    def _constructor_sliced(self):
        return HashableSeries

    uuid = __import__('uuid')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hash = None
        self.reset_hash()

    def reset_hash(self):
        self.hash = self.uuid.uuid4().int

    def __hash__(self):
        return self.hash

    def features(self):
        return self.apply(lambda s: s.features()).T
