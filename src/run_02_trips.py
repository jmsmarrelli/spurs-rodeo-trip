"""Stage 2 - find every team's longest February road trip and price San Antonio's.

    python src/run_02_trips.py

Writes output/trips.csv, output/spurs_trips.csv, output/trip_effect.csv,
output/team_trips.csv, output/win_rates.csv, output/expected_net.csv,
output/close_games.csv, output/trip_context.csv, output/sensitivity.csv
and figures 01-05.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (BUBBLE_CITY, FIG, MIN_TRIP_GAMES, N_BOOT, OUT, PROC,  # noqa: E402
                    SEED, TEAM, TRIP_WINDOW)
import model as M  # noqa: E402
import style as S  # noqa: E402
import trips as T  # noqa: E402

CONTROLS = list(M.TERMS)


def game_frame(panel: pd.DataFrame) -> pd.DataFrame:
    """Fold the team-game panel to one row per game, with differenced controls."""
    burden = M.own_burden(panel)
    keep = ["game_id", "season", "team", "is_home", "net", "poss", "city",
            "on_trip", "after_trip", "margin_h"]
    p = pd.concat([panel[keep].reset_index(drop=True),
                   burden.reset_index(drop=True)], axis=1)
    home = p[p["is_home"] == 1].set_index("game_id")
    away = p[p["is_home"] == 0].set_index("game_id")
    common = home.index.intersection(away.index)
    home, away = home.loc[common], away.loc[common]

    g = pd.DataFrame({"season": home["season"], "net_h": home["net"],
                      "margin_h": home["margin_h"],
                      "home": home["team"], "away": away["team"]})
    for term, col in M.OWN.items():
        g[term] = home[col].to_numpy() - away[col].to_numpy()
    # A trip is something the away team is on. The home team is never on one.
    g["d_trip"] = -away["on_trip"].to_numpy().astype(float)
    g["d_after"] = (home["after_trip"].to_numpy().astype(float)
                    - away["after_trip"].to_numpy().astype(float))
    g["away_on_trip"] = away["on_trip"].to_numpy()
    g["ts_home"] = g["home"] + "_" + g["season"].astype(str)
    g["ts_away"] = g["away"] + "_" + g["season"].astype(str)
    return g.reset_index()


def fig_calendar(spurs: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.6, 6.2))
    y = np.arange(len(spurs))
    starts = spurs["start"].dt.dayofyear
    for i, r in enumerate(spurs.itertuples()):
        ax.barh(i, r.days, left=r.start.dayofyear, height=0.62,
                color=S.SPURS, zorder=2)
        ax.text(r.start.dayofyear + r.days + 1.2, i,
                f"{int(r.games)} games   {int(r.miles):,} mi", va="center",
                fontsize=8.4, color=S.INK_2)
    ax.set_yticks(y, [f"{int(s) - 1}-{str(int(s))[2:]}" for s in spurs["season"]])
    ax.set_ylim(-0.8, len(spurs) - 0.2)
    ax.grid(axis="y", visible=False)
    S.strip(ax, keep=("bottom",))
    ax.tick_params(axis="y", labelsize=8.6)
    ticks = [32, 46, 60, 74, 88]
    ax.set_xticks(ticks, ["1 Feb", "15 Feb", "1 Mar", "15 Mar", "29 Mar"])
    ax.set_xlim(24, 108)
    ax.set_xlabel("Day of the season")
    ax.set_title("Twenty rodeo road trips, found in the schedule rather than looked up",
                 loc="left")
    S.caption(fig, "The longest unbroken run of road games San Antonio played between 20 January "
                   "and 20 March in each season. No list of rodeo dates was used: the trip is "
                   "whatever the schedule makes it, and the schedule makes it every year.")
    fig.tight_layout()
    fig.savefig(FIG / "01_calendar.png")
    plt.close(fig)


def fig_league_trips(team_trips: pd.DataFrame) -> None:
    d = team_trips.sort_values("games")
    y = np.arange(len(d))
    colours = [S.SPURS if t == TEAM else S.SILVER for t in d["team"]]
    fig, ax = plt.subplots(figsize=(8.8, 0.3 * len(d) + 2.6))
    ax.barh(y, d["games"], color=colours, height=0.64, zorder=2)
    for i, r in enumerate(d.itertuples()):
        ax.text(r.games + 0.04, i, f"{r.games:.1f}", va="center", fontsize=8.6,
                color=S.INK_2)
    ax.set_yticks(y, [f"{t}  ({n})" for t, n in zip(d["team"], d["seasons"])])
    ax.set_ylim(-0.8, len(d) - 0.2)
    ax.set_xlim(0, d["games"].max() * 1.12)
    ax.grid(axis="y", visible=False)
    S.strip(ax, keep=("bottom",))
    ax.tick_params(axis="y", labelsize=8.8)
    ax.set_xlabel("Average length of the longest February road trip (games)")
    ax.set_title("Nobody else gets one this long, this reliably", loc="left")
    S.caption(fig, "Mean over the seasons each franchise appears, in brackets, 2003-04 to "
                   "2022-23. Every team has a longest February road trip. Somebody edges San "
                   "Antonio in six of the twenty seasons - the Clippers had eleven games in "
                   "2010-11 - but nobody else averages anything close. Seattle and Oklahoma "
                   "City are the same franchise either side of the move.")
    fig.tight_layout()
    fig.savefig(FIG / "02_league_trips.png")
    plt.close(fig)


def fig_effect(coef: pd.DataFrame) -> None:
    """Every schedule term in the model, with the two the project is about.

    Shown together on purpose. A null is only worth reading if the instrument
    that produced it can find things, and the same fit that puts the trip at
    zero puts a back-to-back at a point and a half.
    """
    d = coef.iloc[::-1].reset_index(drop=True)
    subject = d["term"].isin(["d_trip", "d_after"])
    fig, ax = plt.subplots(figsize=(9.4, 5.4))
    ax.barh(d.index, d["beta"], height=0.5, zorder=2,
            color=[S.SPURS if s_ else S.SILVER for s_ in subject])
    ax.errorbar(d["beta"], d.index, xerr=[d["beta"] - d["lo"], d["hi"] - d["beta"]],
                fmt="none", ecolor=S.INK_2, elinewidth=1.1, capsize=3.2, zorder=3)
    lo_min, hi_max = float(d["lo"].min()), float(d["hi"].max())
    span = hi_max - lo_min
    for i, r in d.iterrows():
        end = r["lo"] if r["beta"] < 0 else r["hi"]
        ax.text(end + np.sign(r["beta"] or 1) * 0.012 * span, i, f"{r['beta']:+.2f}",
                va="center", ha="left" if r["beta"] >= 0 else "right",
                fontsize=9.2, color=S.INK if subject[i] else S.INK_2,
                fontweight="semibold" if subject[i] else "normal")
    ax.axvline(0, color=S.INK_3, lw=0.9, zorder=4)
    ax.set_yticks(d.index, d["label"])
    for tick, flag in zip(ax.get_yticklabels(), subject):
        if flag:
            tick.set_fontweight("semibold")
            tick.set_color(S.INK)
    ax.set_xlim(lo_min - 0.22 * span, hi_max + 0.14 * span)
    ax.set_ylim(-0.7, len(d) - 0.3)
    ax.grid(axis="y", visible=False)
    S.strip(ax, keep=("bottom",))
    ax.tick_params(axis="y", labelsize=9.2)
    ax.set_xlabel("Association with net rating, points per 100 estimated possessions")
    ax.set_title("Trip associations and their uncertainty",
                 loc="left")
    S.caption(fig, 'Schedule coefficients with team-season effects and season-specific home advantage. Bars are 95% intervals. Intervals that include zero do not establish equivalence or an absence of a trip effect; observational confounding can remain.')
    fig.tight_layout()
    fig.savefig(FIG / "03_trip_effect.png")
    plt.close(fig)


def fig_by_season(spurs_games: pd.DataFrame, overall: float) -> None:
    d = (spurs_games.groupby("season")
         .agg(adj=("adj_net", "mean"), n=("adj_net", "size")).reset_index())
    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    colours = [S.SERIES[1] if v < 0 else S.SERIES[0] for v in d["adj"]]
    ax.bar(d["season"], d["adj"], color=colours, width=0.66, zorder=2)
    ax.axhline(0, color=S.INK_3, lw=0.9, zorder=3)
    ax.axhline(overall, color=S.SPURS, lw=1.5, ls=(0, (4, 3)), zorder=4)
    ax.text(d["season"].max() + 0.9, overall, f"  twenty-trip\n  average {overall:+.2f}",
            va="center", ha="left", color=S.SPURS, fontsize=8.8,
            fontweight="semibold", zorder=5,
            bbox=dict(facecolor=S.SURFACE, edgecolor="none", pad=1.5))
    S.strip(ax)
    ax.set_xlim(d["season"].min() - 0.9, d["season"].max() + 4.4)
    ax.set_xticks(range(2004, 2024, 3),
                  [f"{y - 1}-{str(y)[2:]}" for y in range(2004, 2024, 3)])
    ax.tick_params(axis="x", labelsize=8.8)
    ax.set_ylabel("Net rating on the trip, above expectation")
    ax.set_title("Trip by trip", loc="left")
    S.caption(fig, "Each bar is one rodeo trip: San Antonio's actual net rating in those games "
                   "minus what the model expects of anyone facing that opponent, in that "
                   "building, arriving that way. Blue is better than expected. Twenty bars, "
                   "five to nine games each.")
    fig.tight_layout()
    fig.savefig(FIG / "04_by_season.png")
    plt.close(fig)


SPECS = [
    # window, minimum length, controls to drop, games counted as "just after"
    (("01-20", "03-20"), 4, (), None),      # what the analysis uses
    (("01-20", "03-20"), 5, (), None),
    (("01-20", "03-20"), 6, (), None),
    (("01-15", "03-31"), 4, (), None),
    (("02-01", "03-10"), 4, (), None),
    (("01-01", "04-15"), 4, (), None),
    (("01-20", "03-20"), 4, ("d_road",), None),
    (("01-20", "03-20"), 4, (), 3),
    (("01-20", "03-20"), 4, (), 5),
]


def price_trip(panel: pd.DataFrame, window: tuple[str, str], min_games: int,
               drop: tuple[str, ...] = (), after_games: int | None = None) -> dict:
    """One full pass: detect, fit, and read off every number the project quotes."""
    tr = T.find_trips(panel, window, min_games)
    sa = tr[tr["team"] == TEAM]
    g = game_frame(T.label_games(panel, tr, after_games))
    terms = [t for t in CONTROLS if t not in drop] + ["d_trip", "d_after"]
    X, y, ts, seasons = T.trip_effect_design(g, terms)
    beta, se, _, _, _ = M.ols(X, y)
    k = len(ts) + len(seasons)
    trip_cols = [k + terms.index("d_trip"), k + terms.index("d_after")]
    keep = [i for i in range(X.shape[1]) if i not in trip_cols]
    exp_h = X[:, keep] @ beta[keep]
    on = (g["away"] == TEAM) & (g["away_on_trip"] == 1)
    off = (g["away"] == TEAM) & (g["away_on_trip"] == 0)
    sas = on.to_numpy()
    adj = (-g.loc[on, "net_h"].to_numpy()) - (-exp_h[sas])
    mean, lo, hi, _ = T.bootstrap_mean(adj, N_BOOT, SEED)
    j = k + terms.index("d_trip")
    return {
        "window": f"{window[0]} to {window[1]}", "min_games": min_games,
        "controls": "all" if not drop else "less " + ", ".join(drop),
        "after_window": "trip length" if after_games is None else f"{after_games} games",
        "trips": len(tr), "sa_seasons": len(sa), "sa_mean_games": sa["games"].mean(),
        "d_trip": beta[j], "d_trip_se": se[j],
        "d_after": beta[k + terms.index("d_after")],
        "d_after_se": se[k + terms.index("d_after")],
        "slate_gap": float(exp_h[off.to_numpy()].mean() - exp_h[sas].mean()),
        "sa_games": int(sas.sum()), "sa_adj_net": mean, "lo": lo, "hi": hi,
    }


def sensitivity(panel: pd.DataFrame) -> pd.DataFrame:
    """Refit everything under other definitions of "the February trip".

    The window, the minimum length and the control set are choices, and a choice
    that changes the answer is a finding about the choice rather than about the
    Spurs.
    """
    return pd.DataFrame([price_trip(panel, w, n, d, a) for w, n, d, a in SPECS])


def fig_anatomy(rates: pd.DataFrame, close: pd.DataFrame) -> None:
    """Where the folklore comes from, in two panels.

    Left: they really do win more on the trip, and all of the gap is in games
    decided by five points or fewer. Right: they did not play better - the point
    differential is the same to a tenth - and the slate was softer.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.4),
                                   gridspec_kw={"width_ratios": [1, 1.05]})
    trip, other = S.SPURS, S.SILVER
    w = 0.34

    groups = ["All road games", "Decided by 5\nor fewer"]
    on_vals = [close.loc[0, "win_pct"], close.loc[0, "close_win_pct"]]
    off_vals = [close.loc[1, "win_pct"], close.loc[1, "close_win_pct"]]
    x = np.arange(2)
    ax1.bar(x - w / 2, [100 * v for v in on_vals], w, color=trip,
            label="On the rodeo trip", zorder=2)
    ax1.bar(x + w / 2, [100 * v for v in off_vals], w, color=other,
            label="Other road games", zorder=2)
    for xi, v in zip(x - w / 2, on_vals):
        ax1.text(xi, 100 * v + 1.4, f"{100 * v:.1f}%", ha="center", fontsize=9.2,
                 color=S.INK, fontweight="semibold")
    for xi, v in zip(x + w / 2, off_vals):
        ax1.text(xi, 100 * v + 1.4, f"{100 * v:.1f}%", ha="center", fontsize=9.2,
                 color=S.INK_2, zorder=4,
                 bbox=dict(facecolor=S.SURFACE, edgecolor="none", pad=1.0))
    ax1.axhline(50, color=S.INK_3, lw=0.9, ls=(0, (3, 3)), zorder=3)
    ax1.set_xticks(x, groups)
    ax1.set_ylim(0, 72)
    ax1.set_yticks(range(0, 71, 10), [f"{v}%" for v in range(0, 71, 10)])
    ax1.set_ylabel("Win rate")
    ax1.set_title("They do win more on it", loc="left", fontsize=11)
    S.strip(ax1)
    ax1.grid(axis="x", visible=False)
    ax1.legend(frameon=False, fontsize=9, loc="upper right",
               bbox_to_anchor=(1.02, 1.06))

    labels = ["On the rodeo\ntrip", "Other road\ngames"]
    exp = rates.loc[:1, "expected_net"].to_numpy()
    act = rates.loc[:1, "actual_net"].to_numpy()
    x = np.arange(2)
    ax2.bar(x - w / 2, exp, w, color=S.NEUTRAL, label="Expected", zorder=2)
    ax2.bar(x + w / 2, act, w, color=trip, label="Actual", zorder=2)
    for xi, v in zip(np.r_[x - w / 2, x + w / 2], np.r_[exp, act]):
        ax2.text(xi, v + 0.09, f"{v:+.2f}", ha="center", fontsize=9.2, color=S.INK_2)
    ax2.axhline(0, color=S.INK_3, lw=0.9, zorder=3)
    ax2.set_xticks(x, labels)
    ax2.set_ylim(0, max(exp.max(), act.max()) * 1.32)
    ax2.set_ylabel("Net rating, points per 100")
    ax2.set_title("Performance relative to expectation", loc="left", fontsize=11)
    S.strip(ax2)
    ax2.grid(axis="x", visible=False)
    ax2.legend(frameon=False, fontsize=9, loc="upper right")

    S.caption(fig, 'Historical trip games and other San Antonio road games. Expected performance comes from the fitted model, not a prediction frozen before each game. Close games use original final score margins of five points or fewer; the exact counts and win rates are in output/close_games.csv.')
    fig.tight_layout()
    fig.savefig(FIG / "05_anatomy.png")
    plt.close(fig)


def main() -> None:
    panel = pd.read_csv(PROC / "team_games.csv.gz", low_memory=False)
    panel["date"] = pd.to_datetime(panel["date"])
    panel = panel[panel["city"] != BUBBLE_CITY].reset_index(drop=True)

    trips = T.find_trips(panel, TRIP_WINDOW, MIN_TRIP_GAMES)
    trips.to_csv(OUT / "trips.csv", index=False)
    spurs = trips[trips["team"] == TEAM].sort_values("season").reset_index(drop=True)
    spurs.to_csv(OUT / "spurs_trips.csv", index=False)

    team_trips = (trips.groupby("team")
                  .agg(seasons=("season", "size"), games=("games", "mean"),
                       days=("days", "mean"), miles=("miles", "mean"))
                  .reset_index())
    team_trips.round(3).to_csv(OUT / "team_trips.csv", index=False)

    labelled = T.label_games(panel, trips)
    g = game_frame(labelled)

    terms = CONTROLS + ["d_trip", "d_after"]
    X, y, ts, seasons = T.trip_effect_design(g, terms)
    beta, se, r2, resid, dof = M.ols(X, y)
    k = len(ts) + len(seasons)
    extra = {"d_trip": "On a long road trip",
             "d_after": "First games back after one"}
    labels = {**M.TERMS, **extra}
    coef = pd.DataFrame({
        "term": terms, "beta": beta[k:], "se": se[k:],
        "label": [labels[t] for t in terms]})
    coef["t"] = coef["beta"] / coef["se"]
    coef["lo"] = coef["beta"] - 1.96 * coef["se"]
    coef["hi"] = coef["beta"] + 1.96 * coef["se"]
    coef.round(4).to_csv(OUT / "trip_effect.csv", index=False)

    # What San Antonio did on its own trips, against what the model expected of
    # anyone walking into those games.
    #
    # The expectation deliberately leaves the two trip indicators out. Including
    # them would make the comparison circular: the residual would already have
    # the league-wide trip effect subtracted from it, and "San Antonio against
    # expectation" would silently mean "San Antonio against other teams on
    # trips" rather than "San Antonio against the situation".
    trip_cols = [k + terms.index("d_trip"), k + terms.index("d_after")]
    keep = [i for i in range(X.shape[1]) if i not in trip_cols]
    g = g.assign(expected_h=X[:, keep] @ beta[keep])

    on = g[(g["away"] == TEAM) & (g["away_on_trip"] == 1)].copy()
    off = g[(g["away"] == TEAM) & (g["away_on_trip"] == 0)].copy()
    at_home = g[g["home"] == TEAM].copy()
    for d, sign in ((on, -1.0), (off, -1.0), (at_home, 1.0)):
        d["actual"] = sign * d["net_h"]
        d["expected"] = sign * d["expected_h"]
        d["adj_net"] = d["actual"] - d["expected"]
        d["margin"] = sign * d["margin_h"]
        d["won"] = (d["margin"] > 0).astype(int)

    # The same number computed the circular way, so the write-up can quote the
    # size of the difference instead of asserting that it matters.
    circular = (-g.loc[g.index[(g["away"] == TEAM) & (g["away_on_trip"] == 1)],
                       "net_h"].to_numpy()) - (-(X @ beta)[
                           ((g["away"] == TEAM) & (g["away_on_trip"] == 1)).to_numpy()])
    pd.DataFrame([
        {"expectation": "excludes the trip indicators (used everywhere below)",
         "sa_adj_net": float(on["adj_net"].mean())},
        {"expectation": "includes them (circular)", "sa_adj_net": float(circular.mean())},
    ]).round(4).to_csv(OUT / "expectation_check.csv", index=False)

    splits = []
    for name, d in (("On the rodeo trip", on), ("Other road games", off),
                    ("Home games", at_home)):
        mean, lo, hi, p = T.bootstrap_mean(d["adj_net"].to_numpy(), N_BOOT, SEED)
        splits.append({"split": name, "games": len(d), "win_pct": d["won"].mean(),
                       "actual_net": d["actual"].mean(),
                       "expected_net": d["expected"].mean(),
                       "adj_net": mean, "lo": lo, "hi": hi, "p": p})
    rates = pd.DataFrame(splits)
    rates.round(4).to_csv(OUT / "win_rates.csv", index=False)

    # If two sets of games produce the same point differential and different win
    # rates, the difference is in the close ones.
    close = []
    for name, d in (("On the rodeo trip", on), ("Other road games", off)):
        c = d[d["margin"].abs() <= 5]
        close.append({"split": name, "games": len(d), "win_pct": d["won"].mean(),
                      "mean_margin": d["margin"].mean(),
                      "close_games": len(c), "close_win_pct": c["won"].mean()})
    close = pd.DataFrame(close)
    close.round(4).to_csv(OUT / "close_games.csv", index=False)

    # Two facts the write-up leans on that are not otherwise in any output file:
    # what makes the trip slate softer, and what the model cannot see inside it.
    east = {"ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DET", "IND", "MIA", "MIL",
            "NY", "NJ", "ORL", "PHI", "TOR", "WSH"}
    sas_away = labelled[(labelled["team"] == TEAM) & (labelled["is_home"] == 0)]
    ctx = []
    for name, d in (("On the rodeo trip", sas_away[sas_away["on_trip"] == 1]),
                    ("Other road games", sas_away[sas_away["on_trip"] == 0])):
        ctx.append({"split": name, "games": len(d),
                    "east_opponent_share": d["opp"].isin(east).mean(),
                    "mean_road_game_no": d["road_game_no"].mean()})
    after_home = labelled[(labelled["team"] == TEAM) & (labelled["after_trip"] == 1)]
    ctx.append({"split": "First games back", "games": len(after_home),
                "east_opponent_share": float("nan"),
                "mean_road_game_no": float("nan"),
                "home_share": after_home["is_home"].mean()})

    breaks = 0
    for r in spurs.itertuples():
        d = labelled[(labelled["team"] == TEAM) & (labelled["season"] == r.season)
                     & (labelled["date"] >= r.start) & (labelled["date"] <= r.end)]
        gaps = d.sort_values("date")["date"].diff().dt.days.dropna()
        breaks += int(len(gaps) and gaps.max() >= 5)
    ctx = pd.DataFrame(ctx)
    ctx.round(4).to_csv(OUT / "trip_context.csv", index=False)

    fig_calendar(spurs)
    fig_league_trips(team_trips)
    fig_effect(coef)
    fig_by_season(on, float(rates.loc[0, "adj_net"]))
    fig_anatomy(rates, close)

    print(f"{len(trips):,} team-season trips found; San Antonio has {len(spurs)}")
    print("\n--- the rodeo road trip ---")
    print(spurs[["season", "games", "days", "cities", "miles",
                 "start", "end"]].to_string(index=False))
    print(f"\nmean {spurs['games'].mean():.1f} games over {spurs['days'].mean():.1f} days, "
          f"{spurs['miles'].mean():,.0f} miles")
    print(f"longest {int(spurs['games'].max())} games "
          f"({int(spurs.loc[spurs['games'].idxmax(), 'season']) - 1}-"
          f"{str(int(spurs.loc[spurs['games'].idxmax(), 'season']))[2:]})")

    print("\n--- longest February road trip, league-wide ---")
    print(pd.concat([team_trips.nlargest(5, "games"), team_trips.nsmallest(3, "games")])
          .to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    print(f"\nmodel: R\u00b2 {r2:.4f}, residual SD {resid.std():.2f}, dof {dof:,}")
    print(coef[["label", "beta", "se", "t"]].round(3).to_string(index=False))

    print("\n--- San Antonio, by where the game was ---")
    print(rates.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print("\n--- what the trip slate is made of ---")
    print(ctx.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(f"trips containing a gap of five days or more (the All-Star break): "
          f"{breaks} of {len(spurs)}")

    print("\n--- and in the close ones ---")
    print(close.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    gap = on["expected"].mean() - off["expected"].mean()
    print(f"\ntrip slate easier than the rest of the road schedule by {gap:+.2f} "
          f"points per 100 before tip-off")
    pd.DataFrame([{"split": "On the rodeo trip", "expected_net": on["expected"].mean()},
                  {"split": "Other road games", "expected_net": off["expected"].mean()}]
                 ).round(4).to_csv(OUT / "expected_net.csv", index=False)

    sens = sensitivity(panel)
    sens.round(3).to_csv(OUT / "sensitivity.csv", index=False)
    print("\n--- under other definitions of the trip ---")
    print(sens.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
