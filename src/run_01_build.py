"""Stage 1 - build the game panel, with every schedule feature attached.

    python src/run_01_build.py

Joins the schedule to the team box scores, works out where each game was played,
and then walks each team's season in date order to compute what it arrived with:
days off, miles flown, time zones crossed, altitude gained, games in the past
week, and how deep into a road trip it was.

Writes data/processed/team_games.csv.gz and output/schedule_summary.csv.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import OUT, PROC, RAW, SEASONS  # noqa: E402
import venues as V  # noqa: E402

# Days of rest above three stop mattering, and the altitude effect is flat until
# the mountains. Both are re-derived in the sibling schedule project; here they
# are held fixed so the controls in this model match that one exactly.
REST_CAP = 3
HIGH_ALTITUDE_FT = 4000

SCHED_COLS = ["game_id", "season", "season_type", "neutral_site", "venue_address_city",
              "home_abbreviation", "away_abbreviation", "home_score", "away_score",
              "game_date", "status_type_completed"]
BOX_COLS = ["game_id", "season", "season_type", "team_id", "team_abbreviation",
            "team_home_away", "team_score", "field_goals_attempted",
            "free_throws_attempted", "offensive_rebounds", "turnovers"]


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    sched, box = [], []
    for s in SEASONS:
        sp, bp = RAW / f"nba_schedule_{s}.csv", RAW / f"team_box_{s}.csv.gz"
        if not (sp.exists() and bp.exists()):
            print(f"  missing raw files for {s}, skipping", file=sys.stderr)
            continue
        sched.append(pd.read_csv(sp, low_memory=False, usecols=SCHED_COLS))
        box.append(pd.read_csv(bp, low_memory=False, usecols=BOX_COLS,
                               compression="gzip"))
    if not sched:
        raise SystemExit("No raw files found. See data/README.md.")
    return pd.concat(sched, ignore_index=True), pd.concat(box, ignore_index=True)


def possessions(b: pd.DataFrame) -> pd.Series:
    """The standard estimator. At the level of a whole game the 0.44 is fine."""
    return (b["field_goals_attempted"] + 0.44 * b["free_throws_attempted"]
            - b["offensive_rebounds"] + b["turnovers"])


def build_games(sched: pd.DataFrame, box: pd.DataFrame) -> pd.DataFrame:
    sched = sched[(sched["season_type"] == 2) & sched["status_type_completed"].fillna(False)]
    sched = sched[sched["home_abbreviation"].isin(V.FRANCHISES)
                  & sched["away_abbreviation"].isin(V.FRANCHISES)]

    box = box[box["season_type"] == 2]
    box = box[box["team_abbreviation"].isin(V.FRANCHISES)]
    poss = box.assign(poss=possessions(box))
    wide = poss.pivot_table(index="game_id", columns="team_home_away",
                            values=["poss", "team_score"], aggfunc="first")
    wide.columns = [f"{a}_{b}" for a, b in wide.columns]
    g = sched.merge(wide, left_on="game_id", right_index=True, how="inner")

    g = g.rename(columns={"poss_home": "poss_h", "poss_away": "poss_a",
                          "team_score_home": "pts_h", "team_score_away": "pts_a"})
    g = g.dropna(subset=["poss_h", "poss_a", "pts_h", "pts_a"])
    g["poss"] = (g["poss_h"] + g["poss_a"]) / 2
    g = g[g["poss"] > 60]
    g["date"] = pd.to_datetime(g["game_date"])
    g["city"] = g["venue_address_city"].fillna(
        g["home_abbreviation"].map(V.HOME_CITY))
    unknown = ~g["city"].isin(V.CITIES)
    if unknown.any():
        print(f"  dropping {int(unknown.sum())} games at unmapped venues: "
              f"{sorted(g.loc[unknown, 'city'].dropna().unique())}", file=sys.stderr)
        g = g[~unknown]

    g["margin_h"] = g["pts_h"] - g["pts_a"]
    g["net_h"] = 100 * g["margin_h"] / g["poss"]
    return g.sort_values(["season", "date", "game_id"]).reset_index(drop=True)


def team_panel(g: pd.DataFrame) -> pd.DataFrame:
    """One row per team-game, which is the natural shape for walking a schedule."""
    home = g.assign(team=g["home_abbreviation"], opp=g["away_abbreviation"], is_home=1)
    away = g.assign(team=g["away_abbreviation"], opp=g["home_abbreviation"], is_home=0)
    cols = ["game_id", "season", "date", "city", "team", "opp", "is_home",
            "neutral_site", "poss", "net_h"]
    panel = pd.concat([home[cols], away[cols]], ignore_index=True)
    panel["net"] = np.where(panel["is_home"] == 1, panel["net_h"], -panel["net_h"])
    return panel.sort_values(["season", "team", "date"]).reset_index(drop=True)


def schedule_features(panel: pd.DataFrame) -> pd.DataFrame:
    loc = V.lookup(panel["city"])
    panel = pd.concat([panel, loc], axis=1)
    home_city = panel["team"].map(V.HOME_CITY)
    home_loc = V.lookup(home_city).add_prefix("home_")

    g = panel.groupby(["season", "team"], sort=False)
    prev_date = g["date"].shift(1)
    panel["rest"] = (panel["date"] - prev_date).dt.days - 1
    panel["rest"] = panel["rest"].clip(lower=0, upper=REST_CAP)
    panel["is_first_game"] = prev_date.isna()
    panel.loc[panel["is_first_game"], "rest"] = REST_CAP

    prev_lat, prev_lon = g["lat"].shift(1), g["lon"].shift(1)
    panel["miles"] = V.great_circle_miles(prev_lat, prev_lon, panel["lat"], panel["lon"])
    panel["miles"] = panel["miles"].fillna(0.0)
    prev_off = g["utc_offset"].shift(1)
    panel["tz_shift"] = (panel["utc_offset"] - prev_off).fillna(0.0)
    panel["tz_abs"] = panel["tz_shift"].abs()
    panel["tz_west"] = (-panel["tz_shift"]).clip(lower=0)   # travelling east loses hours
    panel["tz_east"] = panel["tz_shift"].clip(lower=0)

    # Altitude. A continuous per-foot term looks natural and does not survive
    # contact with the data: the effect is flat below about four thousand feet
    # and roughly the same size at Denver (5,280) and Salt Lake City (4,226).
    # The per-venue check is in the sibling schedule project. It enters here as a
    # threshold -
    # a team that lives at sea level playing in the mountains - not a slope.
    panel["alt_gain"] = ((panel["elev_ft"] - home_loc["home_elev_ft"].to_numpy())
                         .clip(lower=0) / 1000.0)
    panel["alt_high"] = ((panel["elev_ft"] >= HIGH_ALTITUDE_FT)
                         & (home_loc["home_elev_ft"].to_numpy() < HIGH_ALTITUDE_FT)
                         ).astype(float)

    # Games in the seven days ending today, this one included.
    def density(sub: pd.DataFrame) -> pd.Series:
        d = sub.set_index("date")["is_home"]
        return d.rolling("7D").count().to_numpy()

    panel["games_7d"] = np.concatenate(
        [density(sub) for _, sub in panel.groupby(["season", "team"], sort=False)])

    # How many consecutive road games this is, counting this one.
    away_flag = (panel["is_home"] == 0).astype(int)
    grp = panel.groupby(["season", "team"], sort=False)["is_home"]
    home_block = grp.transform(lambda s: (s == 1).cumsum())
    panel["road_game_no"] = (away_flag.groupby(
        [panel["season"], panel["team"], home_block]).cumsum() * away_flag)

    panel["b2b"] = (panel["rest"] == 0).astype(int)
    return panel


def main() -> None:
    sched, box = load_raw()
    games = build_games(sched, box)
    panel = schedule_features(team_panel(games))
    panel.to_csv(PROC / "team_games.csv.gz", index=False, compression="gzip")

    summary = panel.groupby("season").agg(
        team_games=("game_id", "size"),
        b2b_rate=("b2b", "mean"),
        mean_rest=("rest", "mean"),
        mean_miles=("miles", "mean"),
        miles_per_team=("miles", lambda s: s.sum() / 30),
        mean_games_7d=("games_7d", "mean"),
        high_altitude_trips=("alt_high", "sum"),
    ).round(4)
    summary.to_csv(OUT / "schedule_summary.csv")

    print(f"{len(games):,} games, {panel['season'].min()}-{panel['season'].max()}")
    print(f"{len(panel):,} team-games, {panel['team'].nunique()} franchises")
    print()
    print(summary.to_string())


if __name__ == "__main__":
    main()
