import logging
import os
import statistics
from pathlib import Path

import pvcy_challenge.scoring
import requests
import timing
from pandas import read_csv

from main import anonymize

_TIME = timing.get_timing_group(__name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def run_score_submit_submission():
    p_scores = []
    u_scores = []
    times = []

    directory = f'{os.path.dirname(os.path.abspath(__file__))}/../data'
    files = Path(directory).glob('*.csv')
    logger.info("Running orchestrate...")
    for i, file in enumerate(files):
        logger.info(f"Processing dataset from ${file}")
        quasi_ids = pvcy_challenge.scoring.quasi_ids[file.name]

        # Iniital DataFrame
        df_before = read_csv(file)

        p_score_before = pvcy_challenge.scoring.score_privacy(df_before, quasi_ids=quasi_ids)

        # Run main function
        timer = _TIME.start('treatment')
        df_result = anonymize(df_before, qids=quasi_ids)
        timer.stop()

        times.append(round(_TIME['treatment'][i].elapsed * 1000, 3))

        # Score Privacy
        p_score_after = pvcy_challenge.scoring.score_privacy(df_result, quasi_ids=quasi_ids)
        p_scores.append((p_score_before - p_score_after) / p_score_before)

        # Score distortion
        u_scores.append(
            1 / pvcy_challenge.scoring.score_distortion(df_before=df_before, df_after=df_result,
                                                        quasi_ids=quasi_ids) * 10
        )

    # Submit to submission service
    privacy_score = round(statistics.mean(p_scores), 3) * 100
    utility_score = round(statistics.mean(u_scores), 3) * 2
    time_in_millis = statistics.mean(times)

    # Minimum time enforced here
    if time_in_millis < 2:
        time_in_millis = 2

    resp = requests.post(
        f"https://{os.getenv('PVCY_CHALLENGE_SERVICE_DOMAIN')}/submission?u={os.getenv('USER_NAME')}&ps={privacy_score}&us={utility_score}&t={time_in_millis}")
    print(resp.status_code)


if __name__ == "__main__":
    run_score_submit_submission()
