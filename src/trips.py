"""Finding the trip, and pricing it.

Every February the San Antonio stock show and rodeo takes over the arena and the
Spurs leave town for two and a half weeks. It is the only recurring scheduling event
of its kind in the league, it has been happening since 2003, and it has produced
a durable piece of folklore: that the Spurs are *better* on it, because Popovich
uses it to build the team.

Nothing in the schedule file says "rodeo road trip". So it is not looked up, it
is found: the longest unbroken run of road games each team plays between late
January and mid-March, anchored on where the run starts and required to be at
least four games. For every other franchise that is whatever the schedule maker
handed them. For San Antonio it is the rodeo, every year, and the detection is
checked against that.

Pricing it is the same fixed-effects problem as any other schedule question. A
trip is not hard because it is a trip; it is hard because of who you play, where,
on how much rest. Strip those out and whatever is left is the trip itself.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def find_trips(panel: pd.DataFrame, window: tuple[str, str],
               min_games: int) -> pd.DataFrame:
    """The longest unbroken road run each team plays inside the window."""
    lo, hi = window
    rows = []
    for (season, team), block in panel.groupby(["season", "team"], sort=True):
        block = block.sort_values("date").reset_index(drop=True)
        month_day = block["date"].dt.strftime("%m-%d")
        inside = (month_day >= lo) & (month_day <= hi)
        away = block["is_home"] == 0

        best = None
        start = None
        for i in range(len(block)):
            if away.iloc[i]:
                if start is None:
                    start = i
            else:
                if start is not None:
                    best = _better(best, block, start, i - 1, inside)
                start = None
        if start is not None:
            best = _better(best, block, start, len(block) - 1, inside)
        if best is None:
            continue
        a, b = best
        run = block.iloc[a:b + 1]
        if len(run) < min_games:
            continue
        rows.append({
            "season": season, "team": team,
            "games": len(run),
            "start": run["date"].iloc[0], "end": run["date"].iloc[-1],
            "days": int((run["date"].iloc[-1] - run["date"].iloc[0]).days) + 1,
            "miles": float(run["miles"].sum()),
            "cities": run["city"].nunique(),
            "first_index": int(block.index[a]),
        })
    return pd.DataFrame(rows)


def _better(best, block, a, b, inside):
    """Keep the longest run that starts inside the window.

    Runs arrive in date order and a tie fails the strict comparison below, so a
    tie keeps the earlier run.
    """
    if not inside.iloc[a]:
        return best
    if best is None:
        return (a, b)
    if (b - a) > (best[1] - best[0]):
        return (a, b)
    return best


def label_games(panel: pd.DataFrame, trips: pd.DataFrame,
                after_games: int | None = None) -> pd.DataFrame:
    """Tag every team-game as on the trip, just after it, or neither.

    "Just after" is the next `after_games` games in date order, whatever venue
    they are at - in practice a returning team is mostly at home, but nothing
    here requires it. Passing None matches the length of the trip itself, which
    is the definition the headline uses; `run_02_trips.py` refits with fixed
    windows because the answer turns out to depend on the choice.
    """
    out = panel.sort_values(["season", "team", "date"]).copy()
    out["on_trip"] = 0
    out["after_trip"] = 0
    key = trips.set_index(["season", "team"])
    for (season, team), block in out.groupby(["season", "team"], sort=False):
        if (season, team) not in key.index:
            continue
        t = key.loc[(season, team)]
        on = (block["date"] >= t["start"]) & (block["date"] <= t["end"])
        out.loc[block.index[on], "on_trip"] = 1
        after = block["date"] > t["end"]
        n_after = int(on.sum()) if after_games is None else after_games
        idx = block.index[after][:n_after]
        out.loc[idx, "after_trip"] = 1
    return out


def trip_effect_design(games: pd.DataFrame, terms: list[str]):
    """Game-level design: team-season effects, season home advantage, schedule
    controls, and the trip indicators the question is about."""
    ts = pd.Index(sorted(set(games["ts_home"]) | set(games["ts_away"])))
    seasons = pd.Index(sorted(games["season"].unique()))
    n = len(games)
    X = np.zeros((n, len(ts) + len(seasons) + len(terms)))
    rows = np.arange(n)
    X[rows, ts.get_indexer(games["ts_home"])] += 1.0
    X[rows, ts.get_indexer(games["ts_away"])] -= 1.0
    X[rows, len(ts) + seasons.get_indexer(games["season"])] = 1.0
    for j, term in enumerate(terms):
        X[:, len(ts) + len(seasons) + j] = games[term].to_numpy()
    return X, games["net_h"].to_numpy(), ts, seasons


def bootstrap_mean(values: np.ndarray, n_boot: int, seed: int) -> tuple:
    rng = np.random.default_rng(seed)
    draws = np.array([rng.choice(values, len(values), replace=True).mean()
                      for _ in range(n_boot)])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    p = 2 * min((draws >= 0).mean(), (draws <= 0).mean())
    return float(values.mean()), float(lo), float(hi), float(p)
