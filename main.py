import os

from pandas import read_csv


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
