import os

import pvcy_challenge.scoring
import requests
import timing
from pandas import read_csv

from main import main

_TIME = timing.get_timing_group(__name__)

quasi_ids = ['Hectare', 'Date', 'Age', 'Primary Fur Color', 'Highlight Fur Color', 'Location']


def run_score_submit_submission():
    # Iniital DataFrame
    df_before = read_csv(
        f'{os.path.dirname(os.path.abspath(__file__))}/../data/2018_Central_Park_Squirrel_Census_-_Squirrel_Data.csv')

    # Run main function
    timer = _TIME.start('treatment')
    df_result = main()
    timer.stop()

    time_in_millis = round(_TIME.summary['treatment']['mean'] * 1000, 3)

    # Score Privacy
    privacy_score = pvcy_challenge.scoring.score_privacy(df_result, quasi_ids=quasi_ids)

    # Score distortion
    distortion_score = pvcy_challenge.scoring.score_distortion(df_before=df_before, df_after=df_result, quasi_ids=quasi_ids)

    # Submit to submission service
    resp = requests.post(
        f"https://{os.getenv('PVCY_CHALLENGE_SERVICE_DOMAIN')}/submission?u={os.getenv('USER_NAME', 'testing')}&ps={privacy_score}&us={distortion_score}&t={time_in_millis}")
    print(resp.status_code)


if __name__ == "__main__":
    run_score_submit_submission()
