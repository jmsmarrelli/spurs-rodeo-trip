"""Where every game was actually played.

Keying travel off the home team's city is the obvious shortcut and it is wrong
often enough to matter. The Hornets played 71 of their 80 home games in Oklahoma
City across 2005-06 and 2006-07. The Nets moved from East Rutherford to Newark
to Brooklyn. The Warriors crossed the bay in 2019-20. The Raptors spent 2020-21
in Tampa, and 88 games of 2019-20 were played in a single Florida hotel complex
with no travel at all.

So location comes from the schedule's venue city, not from the franchise, and
this table covers every city the league visited in twenty regular seasons.
Coordinates are city centers, which is accurate to a couple of miles on flights
measured in hundreds. Elevation is in feet. The UTC offset is the standard-time
one; it is used only to count time zones crossed, so daylight saving does not
enter.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# city -> (latitude, longitude, elevation in feet, standard UTC offset)
CITIES: dict[str, tuple[float, float, float, int]] = {
    "Atlanta":          (33.757, -84.396, 1050, -5),
    "Austin":           (30.265, -97.741, 489, -6),
    "Boston":           (42.366, -71.062, 20, -5),
    "Brooklyn":         (40.683, -73.975, 30, -5),
    "Charlotte":        (35.225, -80.839, 748, -5),
    "Chicago":          (41.881, -87.674, 594, -6),
    "Cleveland":        (41.496, -81.688, 653, -5),
    "Dallas":           (32.790, -96.810, 430, -6),
    "Denver":           (39.749, -105.008, 5280, -7),
    "Detroit":          (42.341, -83.055, 600, -5),
    "East Rutherford":  (40.812, -74.074, 20, -5),
    "Houston":          (29.751, -95.362, 50, -6),
    "Indianapolis":     (39.764, -86.156, 715, -5),
    "Lake Buena Vista": (28.375, -81.549, 92, -5),
    "Las Vegas":        (36.103, -115.174, 2030, -8),
    "London":           (51.556, -0.279, 66, 0),
    "Los Angeles":      (34.043, -118.267, 285, -8),
    "Memphis":          (35.138, -90.051, 260, -6),
    "Mexico City":      (19.404, -99.093, 7350, -6),
    "Miami":            (25.781, -80.187, 10, -5),
    "Milwaukee":        (43.045, -87.917, 617, -6),
    "Minneapolis":      (44.979, -93.276, 830, -6),
    "New Orleans":      (29.949, -90.082, 5, -6),
    "New York":         (40.751, -73.993, 30, -5),
    "Newark":           (40.733, -74.171, 20, -5),
    "Oakland":          (37.750, -122.203, 42, -8),
    "Oklahoma City":    (35.463, -97.515, 1201, -6),
    "Orlando":          (28.539, -81.384, 100, -5),
    "Paris":            (48.894, 2.359, 115, 1),
    "Philadelphia":     (39.901, -75.172, 20, -5),
    "Phoenix":          (33.446, -112.071, 1086, -7),
    "Portland":         (45.532, -122.667, 50, -8),
    "Sacramento":       (38.580, -121.500, 30, -8),
    "Salt Lake City":   (40.768, -111.901, 4226, -7),
    "San Antonio":      (29.427, -98.437, 650, -6),
    "San Francisco":    (37.768, -122.388, 10, -8),
    "Seattle":          (47.622, -122.354, 130, -8),
    "Tampa":            (27.943, -82.452, 15, -5),
    "Toronto":          (43.643, -79.379, 249, -5),
    "Washington":       (38.898, -77.021, 25, -5),
}

# Fallback when the schedule row has no venue city: the franchise's home city in
# that season. Only the ambiguous franchises need an entry.
HOME_CITY = {
    "ATL": "Atlanta", "BOS": "Boston", "BKN": "Brooklyn", "CHA": "Charlotte",
    "CHI": "Chicago", "CLE": "Cleveland", "DAL": "Dallas", "DEN": "Denver",
    "DET": "Detroit", "GS": "Oakland", "HOU": "Houston", "IND": "Indianapolis",
    "LAC": "Los Angeles", "LAL": "Los Angeles", "MEM": "Memphis", "MIA": "Miami",
    "MIL": "Milwaukee", "MIN": "Minneapolis", "NJ": "East Rutherford",
    "NO": "New Orleans", "NY": "New York", "OKC": "Oklahoma City",
    "ORL": "Orlando", "PHI": "Philadelphia", "PHX": "Phoenix", "POR": "Portland",
    "SA": "San Antonio", "SAC": "Sacramento", "SEA": "Seattle", "TOR": "Toronto",
    "UTAH": "Salt Lake City", "WSH": "Washington",
}

FRANCHISES = frozenset(HOME_CITY)

_TABLE = pd.DataFrame(
    [(c, *v) for c, v in CITIES.items()],
    columns=["city", "lat", "lon", "elev_ft", "utc_offset"],
).set_index("city")


def lookup(cities: pd.Series) -> pd.DataFrame:
    return _TABLE.reindex(cities.to_numpy()).set_index(cities.index)


def great_circle_miles(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Haversine. Flights are not great circles, but the error is a constant
    multiplier and the coefficient absorbs it."""
    r = 3958.8
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(lon2) - np.radians(lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
