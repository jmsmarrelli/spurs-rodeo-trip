# San Antonio's rodeo road trip: performance and close games

The rodeo trip is a useful scheduling case study: a long sequence of road games recurs for one franchise across many seasons. This project identifies the longest uninterrupted San Antonio road stretch between January 20 and March 20 in each season, then compares trip games with other road games.

That rule is a schedule proxy for the trip; it is not an independently verified list of rodeo dates. The sample covers 2003–04 through 2022–23.

## Close-game comparison

{{table:close_games.csv}}

A close game is defined here as a final margin of five points or fewer, not the NBA's time-and-score definition of clutch play. The revised pipeline carries the original score margin throughout. Reconstructing margin from a floating-point efficiency statistic could turn exactly five into slightly more than five and wrongly exclude the game.

This comparison is descriptive. The close-game sample is small, and selecting games by final margin is not a causal test of travel or coaching.

## Adjusted trip association

{{table:trip_effect.csv}}

The regression controls for team-season strength and observed schedule features such as rest and travel. These adjustments do not randomize which games fall on the trip. Injuries, rotation changes, opponent availability and unmeasured travel differences can remain.

![Trips located in the schedule](figures/01_calendar.png)

The sensitivity results and expected-performance comparisons are retained alongside the headline tables. A historical win-rate difference does not by itself show that the trip creates team cohesion or causes a performance benefit.

## Basketball use

This is a reproducible example of turning a recurring scheduling question into a game-level comparison, checking the actual score boundaries, and distinguishing raw outcomes from model-adjusted associations. For operational use, add verified travel itineraries and availability information, then report a range of plausible burdens rather than a guaranteed win cost.


## Reproduce

The historical analysis used Python 3.12 with the pinned dependencies below. From this repository:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make fetch-data PY=python
make all PY=python
make report site PY=python
```

`make all` verifies source hashes before running the analyses in order. A missing or changed input stops the build. Data downloads need network access; article rendering uses the included result tables. See [the source manifest](data/source_manifest.json), [method notes](docs/method.md) and [current validation record](VALIDATION_CURRENT.md) for the distinction between a source rebuild and checks of delivered outputs.

Season keys in CSV files use the **ending year**: `2025` means 2024–25. Display tables use full season labels. The MIT license covers code; third-party data retain their providers' rights and terms.

[Portfolio](https://github.com/jmsmarrelli/basketball-analytics) · [AI assistance and provenance](PROVENANCE.md)
