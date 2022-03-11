import pytest
import requests


def test_no_requests():
    import pvcy_challenge.scoring
    with pytest.raises(AssertionError):
        requests.get('https://google.com')
