export PYTHONPATH=src

PY=python3
VENV=.venv
PIP=$(VENV)/bin/pip
PYBIN=$(VENV)/bin/python
RUN=$(PYBIN)
RUFF=$(VENV)/bin/ruff
MYPY=$(VENV)/bin/mypy
PYTEST=$(VENV)/bin/pytest

setup:
	$(PY) -m venv $(VENV)
	$(PIP) install -r requirements.txt

fmt:
	$(RUFF) format .

lint:
	$(RUFF) check .

typecheck:
	$(MYPY) src examples

test:
	$(PYTEST) -q

demo.pass: setup
	$(RUN) -m proof_engine.orchestrator build-pcap --candidate examples/candidates/add_v1.py --out out/pcap.add.json
	$(RUN) -m proof_engine.verifier verify --pcap out/pcap.add.json

demo.fail: setup
	$(RUN) -m proof_engine.orchestrator build-pcap --candidate examples/candidates/add_buggy.py --out out/pcap.add.json
	$(RUN) -m proof_engine.verifier verify --pcap out/pcap.add.json