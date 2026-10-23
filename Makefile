# Pipeline stages share generated inputs and must run in order.
.NOTPARALLEL:
PY ?= python3

.PHONY: all build trips clean site

all: verify-data build trips

build:
	$(PY) src/run_01_build.py

trips:
	$(PY) src/run_02_trips.py

# Regenerate the GitHub Pages page from README.md. Needs `pip install -r requirements.txt`.
site:
	$(PY) tools/site.py

clean:
	rm -f figures/*.png output/*.csv data/processed/*

.PHONY: test
test:
	$(PY) -m pytest -q tests

.PHONY: fetch-data verify-data
fetch-data:
	$(PY) tools/fetch_data.py

verify-data:
	$(PY) tools/fetch_data.py --check

.PHONY: report
report:
	$(PY) tools/report.py
