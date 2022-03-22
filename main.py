import re

from pandas.api import types

from pd_anonymizer import HashableDataFrame
from pd_anonymizer.anonymizers import KAnonymizer


def anonymize(df, qids):
    print("Running PD anonymize....")
    # Figure out numeric column names
    numeric_names = ['age', 'zip', 'zipcode', 'year', 'dob']
    numeric_names_regex = '^(' + '|'.join(numeric_names) + ')$'
    num_columns = [
        colname for colname, series in df.items() if (
                colname in qids
                and re.match(numeric_names_regex, colname, flags=re.IGNORECASE)
                and (
                        series.dtype in [int, float, complex]
                        or types.is_numeric_dtype(series.dtype)
                )
        )
    ]

    cat_columns = list(set(qids) - set(num_columns))
    k_target = 30
    test_hdf = HashableDataFrame(df)

    anonymizer = KAnonymizer(
        cat_columns=cat_columns,
        num_columns=num_columns,
        k_target=k_target
    ).fit(test_hdf)

    return anonymizer.transform(test_hdf.copy())
