import os

import pvcy_challenge.scoring
import requests
import timing

from main import main

_TIME = timing.get_timing_group(__name__)


def run_score_submit_submission():
    # Run main function
    timer = _TIME.start('treatment')  # type: timing.Timing
    main()
    timer.stop()

    time_in_millis = round(_TIME.summary['treatment']['mean'] * 1000, 3)

    # Score Privacy
    privacy_score = pvcy_challenge.scoring.score_privacy()

    # Score distortion
    distortion_score = pvcy_challenge.scoring.score_distortion()

    # Submit to submission service
    resp = requests.post(
        f"https://{os.getenv('PVCY_CHALLENGE_SERVICE_DOMAIN')}/submission?u={os.getenv('USER_NAME', 'testing')}&ps={privacy_score}&us={distortion_score}&t={time_in_millis}")
    print(resp.status_code)


if __name__ == "__main__":
    run_score_submit_submission()
