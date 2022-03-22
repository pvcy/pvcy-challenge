show: cat main.py
worker: git clone https://${GH_PA_TOKEN}@github.com/pvcy/pvcy-challenge-service.git && cp pvcy-challenge-service/tests/data/*.csv data/ && pip install git+https://${GH_PA_TOKEN}@github.com/pvcy/pvcy-challenge-service.git requests && python pvcy_challenge_runtime/orchestrate.py
web: python runtime.py