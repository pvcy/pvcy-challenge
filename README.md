## Welcome to the 2022 Privacy Challenge with Privacy Dynamics

Compete against our software for an opportunity to win a revolutionary espresso machine! The Decent Espresso Machine (Model DE1 XL) pulls great shots of espresso, offers unparalleled extraction control and feedback, and makes other espresso machines feel primitive by comparison. Learn more about the prize [here](https://decentespresso.com/model?de1xl).

### Introduction
The objective of an anonymizer is to protect the identities of individuals in a dataset while maintaining the utility of the data as much as possible. 
In the Privacy Challenge, your objective is beat other contestants at maximizing privacy and utility. 
The winner will take home the world's most state-of-the art home espresso machine, designed and manufactured in Seattle, the home of Privacy Dynamics.

### How it works
* Contestants submit an anonymization function to the Privacy Challenge Test Bench.
* The anonymizer will be run on several pseudonymized datasets and scored for quality. We take the average of the scores.
* Quality is measured using three component scores:
    * Privacy -- This score represents re-identification risk. Generally, it is based on record-level k-anonymity. The actual score is computed by performing many simulated attacks and taking the average probability of re-identification.
    * Utility -- This scores how well the data has been preserved and is based on row-level and column-level distortion.
    * Time -- Very slow anonymizers will be penalized, but the reward for building a very fast anonymizer is limited, i.e. Mediocre privacy done extremely quickly will not receive a high score. The goal is to maximize privacy and utility in a reasonable amount of time. 

### How to Play
1. Checkout this repository.
2. Implement your anonymization algorithm within `anonymize()` function in `main.py`. The function must accept a Pandas DataFrame and a list of quasi-identifiers (QIDs) and return a DataFrame. 
3. The QIDs will map to column names in the input DataFrame. Selectively make changes to these values to reduce the row-level uniqueness of QIDs. More rows with matching QIDs - larger equivalence classes - will result in a higher privacy score, but as more cells are distorted, the utility score will decrease. The objective is to optimize privacy and utility.
4. You may also choose to suppress rows as part of your anonymization strategy. It is valid to replace suppressed values with a mask or drop rows entirely from the DataFrame.
5. Do not modify or reset values in the `id` column. This column is used in part to compute distortion, and changing it will negatively impact the utility score. Dropping rows is fine.
6. Do not drop any columns. Missing output columns will cause the Test Bench to fail.
7. We've included one of the Test Bench datasets in the repo for you to use in testing.
8. After completing your anonymizer, submit a new branch to this branch with your implementation.  We'll review your submission, and if it's approved it will be run against the Privacy Challenge Test Bench.
9. Results will be posted on the Privacy Challenge Dshboard at the Privacy Dynamics booth.
10. Come talk to us at the booth!

### Rules
1. Submit as many entries as you wish. If you wish to submit more than once, please submit an additional branch for each submission. New contestants will be given priority over additional submissions.
2. The entrypoint for your implementation must be in `anonymize()` in `main.py`, but you are free to add additional libraries and use other Python packages.
3. Define your dependencies in `requirements.txt`. The total installed size of all depedencies must not exceed 500 MB. 
4. All outbound HTTP calls are explicitly disallowed, i.e. You may not use any external services, even those called by installed packages. All computation must be done by code in your branch.
5. Only make changes in `main.py` and `requirements.txt`. If any edits beyond these two files are made, your submission will be rejected.  

### Verification

- We've provided `pytest` tests to ensure your anonmyzier passes basic submission rules. To setup an environment and run the tests:
    ```
    python -m venv venv
    pip install -r requirements.txt
    python -m pytest tests/
    ```
- Additional checks will be run automatically as part of the Test Bench, and the winning submission will be checked manually to ensure compliance with the rules. 
