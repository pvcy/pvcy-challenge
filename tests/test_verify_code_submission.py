from pandas import DataFrame

from main import main


def test_output_valid_dataframe():
    output_df = main()
    assert isinstance(output_df, DataFrame), "Output from main() is not a valid pandas DataFrame"
