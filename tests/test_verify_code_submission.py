import os

from pandas import DataFrame, read_csv

from main import anonymize


def test_output_valid_dataframe():
    """
    Load local dataset and pass to anonymizer with corresponding QIDs.

    This will be done automatically for several datasets in the Privacy
    Challenge Test Bench.
    """
    data_frame = read_csv(
        f'{os.path.dirname(os.path.abspath(__file__))}/../'
        f'data/2018_Central_Park_Squirrel_Census_-_Squirrel_Data.csv'
    )
    quasi_ids = [
        'Hectare', 'Date', 'Age', 'Primary Fur Color',
        'Highlight Fur Color', 'Location'
    ]
    output_df = anonymize(data_frame, quasi_ids)

    assert isinstance(output_df, DataFrame), "Output from main() is not a valid pandas DataFrame"
    assert data_frame.columns.equals(data_frame.columns), "Result Dataframe contains different columns than input."
