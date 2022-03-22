import os
import re

from pandas import read_csv
from pandas.api import types

from pd_anonymizer import HashableDataFrame
from pd_anonymizer.anonymizers import KAnonymizer


def anonymize(df, qids):
    # Figure out numeric column names
    numeric_names = ['age', 'zip', 'zipcode', 'year', 'dob']
    numeric_names_regex = '^(' + '|'.join(numeric_names) + ')$'
    num_columns = []

    for colname, series in df.items():
        if re.match(numeric_names_regex, colname, flags=re.IGNORECASE) and (
                series.dtype in [int, float, complex] or types.is_numeric_dtype(series.dtype)):
            num_columns.append(colname)

    cat_columns = qids

    k_target = 30
    test_hdf = HashableDataFrame(df)

    anonymizer = KAnonymizer(
        cat_columns=cat_columns,
        num_columns=num_columns,
        k_target=k_target
    ).fit(test_hdf)

    return anonymizer.transform(test_hdf.copy())


if __name__ == "__main__":
    # Sample dataset to anonymize
    quasi_ids = ['Hectare', 'Date', 'Age', 'Primary Fur Color', 'Highlight Fur Color', 'Location']
    data_frame = read_csv(
        f'{os.path.dirname(os.path.abspath(__file__))}/data/2018_Central_Park_Squirrel_Census_-_Squirrel_Data.csv')
    print(anonymize(data_frame, quasi_ids))
