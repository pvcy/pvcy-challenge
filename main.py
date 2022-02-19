import pandas as pd


def anonymize(df, qids):
    """
    The main implementation of your anonymization implementation.
    Trivial anonymizer included as an example.  Replace this code with your own.

    :param df: Untreated DataFrame
    :param qids: list of quasi-identifier columns
    :return: A valid Pandas DataFrame with your anonymized data
    """

    # Randomly shuffle column values
    anon_df = df.copy()
    for colname in qids:
        anon_df[colname] = pd.Series(
            anon_df[colname].sample(len(anon_df), replace=True).values,
            index=anon_df.index
        )
    # Suppress arbitrary percent of rows at random
    return anon_df.drop(
        labels=anon_df.sample(frac=0.5).index,
        axis=0
    )
