import os

from pandas import read_csv, DataFrame, Series


def anonymize(df: DataFrame, qids, suppress_percent=0.05):
    """
    Simplistic anonymizer.
    """
    # Randonly shuffle column values
    anon_df = df.copy()
    for colname in qids:
        anon_df[colname] = Series(
            anon_df[colname].sample(len(anon_df), replace=True).values,
            index=anon_df.index
        )
    # Suppress arbitrary percent of rows at random
    return anon_df.drop(
        labels=anon_df.sample(frac=suppress_percent).index,
        axis=0
    )


def main():
    '''
    The main implementation of your anonymization implementation.
    :return: A valid pandas DataFrame with your anonymized data
    '''
    print("Running main")

    # This is the data you must anonymize.
    data_frame = read_csv(
        f'{os.path.dirname(os.path.abspath(__file__))}/data/2018_Central_Park_Squirrel_Census_-_Squirrel_Data.csv')

    # Replace this code with your own, returning your anonymized data as a pandas DataFrome
    return data_frame


if __name__ == "__main__":
    main()
