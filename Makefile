PY := python3

.PHONY: all build trips clean site

all: build trips

build:
	$(PY) src/run_01_build.py

trips:
	$(PY) src/run_02_trips.py

# Regenerate the GitHub Pages page from README.md. Needs `pip install markdown`.
site:
	$(PY) tools/site.py

clean:
	rm -f figures/*.png output/*.csv data/processed/*
