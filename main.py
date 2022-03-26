import pandas as pd
import sklearn
import pandas as pd
import sklearn
import numpy as np
from sklearn import preprocessing
from sklearn_pandas import DataFrameMapper
from sklearn.cluster import KMeans
from kmodes.kprototypes import KPrototypes


def update_row(row, group_df, quasi_identifiers):
    label = row["label"]
    target = group_df.iloc[label, :]
    row[quasi_identifiers] = target[quasi_identifiers]
    return row


def anonymize(df, qids):
    """
    The main implementation of your anonymization implementation.
    Trivial anonymizer included as an example.  Replace this code with your own.

    :param df: Untreated DataFrame
    :param qids: list of quasi-identifier columns
    :return: A valid Pandas DataFrame with your anonymized data
    """
    # Clean data to train clustering
    data_clean = df.dropna(axis=1).drop(columns=["id"])
    # split into datatypes
    numeric_data = data_clean.select_dtypes(include=[np.number])
    categorical_data = data_clean.select_dtypes(exclude=[np.number])
    # one hote encode and scale data
    mapper = DataFrameMapper([(numeric_data.columns, preprocessing.StandardScaler())])
    scaled_features = mapper.fit_transform(numeric_data)
    scaled_features_df = pd.DataFrame(
        scaled_features, index=numeric_data.index, columns=numeric_data.columns
    )
    # merge encoded and scaled features
    training_data = pd.merge(
        categorical_data, scaled_features_df, left_index=True, right_index=True
    )
    # train and fit clustering
    # kmeans = KPrototypes(int(len(training_data)/5))
    kmeans = KPrototypes(3)

    clusters = kmeans.fit(
        training_data,
        categorical=[
            training_data.columns.get_loc(c) for c in categorical_data.columns
        ],
    )

    # add labels to dataframe
    training_data["label"] = clusters.labels_
    missing_cols = set(df.columns) - set(training_data.columns)
    for col in missing_cols:
        training_data[col] = df[col]
    identifiers = training_data[qids + ["label"]]
    # group by label and get max of each group
    grouped_df = identifiers.groupby("label").agg(lambda x: x.value_counts().index[0])
    # update original dataframe with new max values
    training_data = training_data.apply(update_row, axis=1, args=(grouped_df, qids))
    training_data["id"] = df["id"]
    training_data.drop(columns="label", inplace=True)
    return training_data
