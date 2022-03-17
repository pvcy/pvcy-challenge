import os
import statistics
from pathlib import Path

import pvcy_challenge.scoring
import requests
import timing
from pandas import read_csv

from main import anonymize

_TIME = timing.get_timing_group(__name__)

quasi_ids = ['Hectare', 'Date', 'Age', 'Primary Fur Color', 'Highlight Fur Color', 'Location']


def run_score_submit_submission():
    p_scores = []
    d_scores = []
    times = []

    directory = f'{os.path.dirname(os.path.abspath(__file__))}/../data'
    files = Path(directory).glob('*.csv')
    print("Running orchestrate...")
    for file in files:
        print(f"Processing dataset from ${file}")

        # Iniital DataFrame
        df_before = read_csv(file)

        # Run main function
        timer = _TIME.start('treatment')
        df_result = anonymize(df_before, qids=quasi_ids)
        timer.stop()

        times.append(round(_TIME.summary['treatment']['mean'] * 1000, 3))

        # Score Privacy
        p_scores.append(pvcy_challenge.scoring.score_privacy(df_result, quasi_ids=quasi_ids))

        # Score distortion
        d_scores.append(pvcy_challenge.scoring.score_distortion(df_before=df_before, df_after=df_result, quasi_ids=quasi_ids))

    # Submit to submission service
    privacy_score = round(statistics.mean(p_scores), 3)
    distortion_score = round(statistics.mean(d_scores), 3)
    time_in_millis = statistics.mean(times)

    resp = requests.post(
        f"https://{os.getenv('PVCY_CHALLENGE_SERVICE_DOMAIN')}/submission?u={os.getenv('USER_NAME', 'testing')}&ps={privacy_score}&us={distortion_score}&t={time_in_millis}")
    print(resp.status_code)


if __name__ == "__main__":
    run_score_submit_submission()
