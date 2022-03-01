import os

import requests

from main import main


def run_score_submit_submission():
    # Run main function
    main()

    # Submit to submission service
    resp = requests.post(
        f"https://{os.getenv('PVCY_CHALLENGE_SERVICE_DOMAIN')}/submission?u={os.getenv('USER_NAME')}&ps=123&us=3456&t=12345")
    print(resp.status_code)


if __name__ == "__main__":
    run_score_submit_submission()
