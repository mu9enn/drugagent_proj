.PHONY: check check-static test-contracts test-active

PYTHON ?= python

check: check-static test-contracts test-active

check-static:
	$(PYTHON) scripts/check_repo.py

test-contracts:
	$(PYTHON) -m unittest discover -s tests/contracts -p 'test_*.py' -v

test-active:
	cd mol-pipeline && $(PYTHON) -m unittest discover -s pipeline/postprocess/tests -p 'test_*.py' -v
	cd molclaw-kg && PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v
	cd slime && $(PYTHON) -m unittest discover -s drug_agent/tests -p 'test_*.py' -v
	cd slime && $(PYTHON) drug_agent/toolrl/tests/run_toolrl_tests.py
	cd slime && $(PYTHON) -m unittest discover -s drug_agent/gad/tests -p 'test_*.py' -v
