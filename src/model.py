"""The estimator.

One row per game, from the home team's point of view. The outcome is the home
team's net rating - points per 100 possessions minus points allowed per 100.

    net_home  =  (team-season strength, home)  -  (team-season strength, away)
               +  home advantage for that season
               +  schedule terms, entered as home minus away
               +  error

Team-season fixed effects do the heavy lifting. They soak up every reason one
team beats another that has nothing to do with the calendar, which means the
schedule coefficients are identified off variation *within* a team's own season:
the same roster, some nights rested and some nights not.

Schedule terms are entered as differences rather than as separate home and away
coefficients. That imposes the symmetry that a day of rest is worth the same to
whoever has it, which is both plausible and worth two extra degrees of freedom
per term. It is testable, and the sibling schedule project tests it: fitting
home and away burdens separately there, none of their sums differs from zero at
conventional levels. This project takes the restriction as given.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TERMS = {
    "d_rest0": "No rest (back-to-back)",
    "d_rest1": "One day off",
    "d_rest2": "Two days off",
    "d_miles": "Travel, per 1,000 miles",
    "d_tz": "Time zones crossed",
    "d_games7": "Games in the past week",
    "d_alt": "Playing at altitude",
    "d_road": "Nth straight road game",
}
OWN = {
    "d_rest0": "rest0", "d_rest1": "rest1", "d_rest2": "rest2",
    "d_miles": "miles_k", "d_tz": "tz_abs", "d_games7": "games_7d",
    "d_alt": "alt_high", "d_road": "road_game_no",
}


def own_burden(panel: pd.DataFrame) -> pd.DataFrame:
    """The per-team-game variables the differenced terms are built from."""
    out = pd.DataFrame(index=panel.index)
    out["rest0"] = (panel["rest"] == 0).astype(float)
    out["rest1"] = (panel["rest"] == 1).astype(float)
    out["rest2"] = (panel["rest"] == 2).astype(float)
    out["miles_k"] = panel["miles"] / 1000.0
    out["tz_abs"] = panel["tz_abs"]
    out["games_7d"] = panel["games_7d"]
    out["alt_high"] = panel["alt_high"]
    out["road_game_no"] = panel["road_game_no"]
    return out


def build_design(games: pd.DataFrame):
    """Return X, y, and the column names, with team-season effects included."""
    ts = pd.Index(sorted(set(games["ts_home"]) | set(games["ts_away"])))
    seasons = pd.Index(sorted(games["season"].unique()))
    n = len(games)

    X = np.zeros((n, len(ts) + len(seasons) + len(TERMS)))
    rows = np.arange(n)
    X[rows, ts.get_indexer(games["ts_home"])] += 1.0
    X[rows, ts.get_indexer(games["ts_away"])] -= 1.0
    X[rows, len(ts) + seasons.get_indexer(games["season"])] = 1.0
    for j, term in enumerate(TERMS):
        X[:, len(ts) + len(seasons) + j] = games[term].to_numpy()

    names = ([f"ts::{v}" for v in ts]
             + [f"hca::{s}" for s in seasons]
             + list(TERMS))
    return X, games["net_h"].to_numpy(), names, ts, seasons


def ols(X: np.ndarray, y: np.ndarray):
    """Least squares with standard errors.

    Team-season effects are collinear as a block (adding a constant to every one
    changes nothing), so the normal equations are solved with a pseudo-inverse
    and the fixed effects are read as deviations rather than levels.
    """
    xtx = X.T @ X
    xty = X.T @ y
    inv = np.linalg.pinv(xtx)
    beta = inv @ xty
    resid = y - X @ beta
    dof = len(y) - np.linalg.matrix_rank(X)
    sigma2 = float(resid @ resid) / dof
    se = np.sqrt(np.clip(np.diag(inv) * sigma2, 0, None))
    r2 = 1 - resid.var() / y.var()
    return beta, se, r2, resid, dof
