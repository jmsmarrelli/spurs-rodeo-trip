"""Paths, constants and the handful of knobs the pipeline exposes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"
OUT = ROOT / "output"

for d in (RAW, PROC, FIG, OUT):
    d.mkdir(parents=True, exist_ok=True)

# Season label is the year the season ends: 2023 == 2022-23. The public
# play-by-play and box score mirror this project reads stops there.
FIRST_SEASON = 2004
LAST_SEASON = 2023
SEASONS = list(range(FIRST_SEASON, LAST_SEASON + 1))

TEAM = "SA"                 # the abbreviation the source feed uses
TEAM_NAME = "San Antonio Spurs"

# The trip is never announced in the data. It is found: the longest unbroken run
# of road games each team plays inside this window, which for San Antonio is the
# stretch the rodeo takes over the arena and for everyone else is whatever their
# schedule happened to hand them.
TRIP_WINDOW = ("01-20", "03-20")
MIN_TRIP_GAMES = 4

# The 2019-20 restart was twenty-two teams in one Florida complex with no travel
# and no crowd. It is not a road trip and it is not a home stand.
BUBBLE_CITY = "Lake Buena Vista"

N_BOOT = 5000
SEED = 20240117
