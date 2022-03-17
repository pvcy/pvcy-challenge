from pandas import DataFrame

from main import anonymize

quasi_ids = []


def test_output_valid_dataframe():
    output_df = anonymize(DataFrame(), quasi_ids)
    assert isinstance(output_df, DataFrame), "Output from main() is not a valid pandas DataFrame"
