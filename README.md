### Welcome to the 2022 Privacy Dynamics Privacy Challenge

## Introduction

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sit amet mattis vulputate enim. Consectetur adipiscing elit pellentesque habitant morbi tristique senectus. Tristique sollicitudin nibh sit amet commodo. Convallis aenean et tortor at risus viverra adipiscing at. Eget mauris pharetra et ultrices neque. Sed viverra tellus in hac habitasse. Id donec ultrices tincidunt arcu. Mattis vulputate enim nulla aliquet porttitor. Lacus sed viverra tellus in hac habitasse. Quis vel eros donec ac odio tempor orci dapibus. Id neque aliquam vestibulum morbi blandit cursus risus at. Odio morbi quis commodo odio aenean. Est velit egestas dui id ornare arcu odio ut sem. Amet tellus cras adipiscing enim. Auctor neque vitae tempus quam. Malesuada fames ac turpis egestas sed tempus urna. Cum sociis natoque penatibus et magnis dis parturient montes nascetur. Amet nulla facilisi morbi tempus iaculis. Vel elit scelerisque mauris pellentesque pulvinar.

## How to Play
1. Checkout this repository and initialize your local development environment by running `pip install -r requirements.txt`
2. Implement your anonymization on the dataset found in `data/2018_Central_Park_Squirrel_Census_-_Squirrel_Data.csv` within `main()` function in `main.py`.
3. Submit a new branch to this branch with your implementation.  We'll review and score your submission and post it on the dashboard at the Privacy Dynamics booth.

## Rules
1. Submit as many entries as you wish. If you wish to submit more than once, please submit a second branch.
2. Your main implementation must be in `main()` in `main.py`.  Feel free to introduce any additional files or libraries in `requirements.txt` as you see fit.
3. We ask that you don't use any outbound HTTP calls.  Please don't use any HTTP client libraries like `urllib` or python `requests`.
4. Other adding your own libraries, you should only edit `main.py` and `requirements.txt`. If any edits beyond these two files are made, your submission will be disqualified.

## Verification

We've provided a suite of `pytest` tests that you can run against your submission to make sure it passes some simple submission rules as well as ensure the output of your implementation is scorable.  To run these tests, run the following from the root of the repository:

`python -m pytest tests\`
