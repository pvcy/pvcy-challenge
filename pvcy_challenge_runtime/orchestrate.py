import os

import requests

from main import main


def run_score_submit_submission():
    # Run main function
    main()

    # Submit to submission service
    resp = requests.post(
        f"https://{os.getenv('PVCY_CHALLENGE_SERVICE_DOMAIN')}/submission?u=user1&ps=123&us=3456&t=12345")


if __name__ == "__main__":
    run_score_submit_submission()
