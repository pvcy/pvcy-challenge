import numpy as np
import pandas as pd
from annoy import AnnoyIndex
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import RobustScaler


class LSHForest(TransformerMixin, BaseEstimator):
    """
    LSH forest for general data. It supports top-k query with various
    similarity metrics such as euclidean, hamming, cosine, etc.

    :param n_trees: affects the build time and index size in exchange for accuracy
    :param metric: The similarity metric to use, supports "angular",
        "euclidean", "manhattan", "hamming", or "dot"
    :param scale: Whether to scale input vectors note for hamming scale=False
    """
    def __init__(self, n_trees:int=10, metric:str="manhattan", scale:bool=True):
        # store all kwargs (needed for sklearn>=0.24 getparams)
        self.n_trees = n_trees
        self.metric = metric
        self.index = None
        self.scale = scale
        self._scaler = None

        if metric.lower() == "hamming":
            scale = False

        if scale:
            self._scaler = RobustScaler()

    def _add(self, key, vec):
        self.index.add_item(int(key), vec)

    def _index(self):
        self.index.build(self.n_trees)

    def _query(self, vec, n, search_k=-1, ret_dist=False):
        return self.index.get_nns_by_vector(vec, n=n, search_k=search_k, include_distances=ret_dist)

    def fit(self, X, y=None):
        """
        Fits LSH index to array or dataframe
        Args:
        :param X: array-like of shape (n_samples, n_features)
        :param y : None, Ignored.
        :returns : self (LSHNeighbors) fitted LSH index
        """
        # init
        self.index = AnnoyIndex(X.shape[1], self.metric)

        # handle data re-scaling
        if self._scaler:
            self._scaler = self._scaler.fit(X)
            X_enc = self._scaler.transform(X)
        else:
            X_enc = X.copy() if not isinstance(X, pd.DataFrame) else X.values.copy()

        # use proper index for dataframes
        iterator = X.index if isinstance(X, pd.DataFrame) else range(0, X.shape[0])

        # add items to index
        for i, key in enumerate(iterator):
            self._add(int(key), X_enc[i,:])

        # build index
        self._index()

        return self

    def fit_transform(self, X, y=None):
        """
        Same as LSHNeighbors.fit(X, y=None), use "kneighbors" to find nearest neighbors.
        """
        return self.fit(X, y=y)

    def kneighbors(self, X, n_neighbors=10, k=-1, return_distance=False):
        """
        Returns n_neighbors of approximate nearest neighbors.
        Args:
        X : array_like, shape (n_samples, n_features)
            List of n_features-dimensional data points.  Each row
            corresponds to a single query.
        n_neighbors : int, opitonal (default = 10)
            Number of neighbors required.
        k : int, optional
            Run-time trade-off for performance
        return_distance : bool, default = False:
            Whether to return distances or not
        Returns:
        Y : array, shape (n_samples, n_neighbors)
            Indices of the approximate nearest points in the population
            matrix.
        """
        # init
        rows = X.shape[0]
        Y = np.zeros((rows, n_neighbors), dtype=np.int32)

        if return_distance:
            D = np.zeros((rows, n_neighbors))

        # handle data re-scaling
        if self._scaler:
            X_enc = self._scaler.transform(X)
        else:
            X_enc = X.copy() if not isinstance(X, pd.DataFrame) else X.values.copy()

        # get neighbors for each row
        for i in range(0,rows):
            if return_distance:
                Y[i,:], D[i,:] = self._query(X_enc[i,:], n_neighbors, search_k=k, ret_dist=True)
            else:
                Y[i,:] = self._query(X_enc[i,:], n_neighbors, search_k=k, ret_dist=False)

        if return_distance:
            return Y, D

        return Y

class CategoricalLSHForest(LSHForest):
    """
    LSH forest for categorical data. It supports top-k query for nominal data

    Args:
        n_trees (int, default 40): affects the build time and index size
            in exchange for accuracy
    """
    def __init__(self, n_trees=40):
        super(CategoricalLSHForest, self).__init__(n_trees=n_trees, metric="hamming", scale=False)

class NumericalLSHForest(LSHForest):
    """
    LSH forest for numerical data. It supports top-k query for interval/ratio/count data

    Args:
        n_trees (int, default 40): affects the build time and index size
            in exchange for accuracy
        metric (str, optional): The similarity metric to use, supports
            "angular", "euclidean", "manhattan", or "dot"
        scale (bool, default true): Whether to scale input vectors
    """
    __supp_metrics = ["angular", "euclidean", "manhattan", "dot"]

    def __init__(self, n_trees=40, metric="manhattan", scale=True):
        supp_metrics = NumericalLSHForest.__supp_metrics

        if metric.lower() not in supp_metrics:
            raise ValueError(f"unsupported metric {metric}, must be one of {', '.join(supp_metrics)}")

        super(NumericalLSHForest, self).__init__(n_trees=n_trees, metric=metric, scale=scale)
