import os

from pandas import read_csv, Series


def anonymize(df, qids):
    '''
    The main implementation of your anonymization implementation.
    :return: A valid pandas DataFrame with your anonymized data
    '''

    # Simplistic anonymizer as an example.  Replace this code with your own.

    # Randomly shuffle column values
    anon_df = df.copy()
    for colname in qids:
        anon_df[colname] = Series(
            anon_df[colname].sample(len(anon_df), replace=True).values,
            index=anon_df.index
        )
    return anon_df


if __name__ == "__main__":
    # Sample dataset to anonymize
    quasi_ids = ['Hectare', 'Date', 'Age', 'Primary Fur Color', 'Highlight Fur Color', 'Location']
    data_frame = read_csv(
        f'{os.path.dirname(os.path.abspath(__file__))}/data/2018_Central_Park_Squirrel_Census_-_Squirrel_Data.csv')
    print(anonymize(data_frame, quasi_ids))

