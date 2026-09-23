# Method notes

The detection rule in full, the specification choices, the two places the
obvious approach is wrong, and where this is thin.

## Detecting the trip

Nothing in the schedule file says "rodeo road trip", and no list of rodeo dates
is read in. For each team-season the rule is:

1. Split the season into maximal runs of consecutive road games.
2. Keep the runs whose **first** game falls between 20 January and 20 March.
3. Take the longest of those. Ties go to the earlier one.
4. Discard it if it is shorter than four games.

Anchoring on the first game rather than on any overlap matters for the handful
of runs that straddle the window edge: a road trip that begins on 14 January and
runs into February is a January trip that happens to be long, not a February
one, and including it would let the schedule maker's January decisions into a
February question.

The rule is applied identically to all thirty-two franchise codes. For San
Antonio it returns the rodeo trip in all twenty seasons. For everyone else it
returns whatever their schedule happened to hand them, which is the comparison
group in `output/team_trips.csv` and figure 02.

**External check.** Three of the twenty were checked against contemporaneous
reporting rather than against the data that produced them. The detector puts the
2016-17 trip's first game on 6 February 2017, which is the day local coverage
described the team as kicking off the fifteenth annual trek; it ends the 2018-19
trip on 25 February 2019, and the league's own write-up of the team regrouping
after the rodeo road trip is dated the 26th; and the eight opponents a
season-preview piece listed for 2022-23 are eight of the nine games the detector
found. It is the right event.

**The fifteenth in 2017 also dates the tradition.** Counting back puts the first
one in February 2003, the season the arena opened, which is why this project
starts at 2003-04 and treats the whole sample as having the trip in it.

## Is the window doing the work?

I picked 20 January to 20 March before looking at a single result, on the
grounds that it brackets the rodeo without being so wide that it starts
collecting other teams' western swings. The window, the length floor and the
control set are all choices, though, so `sensitivity()` refits the entire
analysis under seven combinations and writes `output/sensitivity.csv`:

| Window | Min | Controls | SA seasons | SA mean length | Trip coefficient | Slate gap | SA vs. expectation |
|---|---|---|---|---|---|---|---|
| 20 Jan – 20 Mar | 4 | all | 20 | 8.00 | +0.16 (0.30) | +0.61 | −0.71 |
| 20 Jan – 20 Mar | 5 | all | 20 | 8.00 | +0.18 (0.36) | +0.64 | −0.71 |
| 20 Jan – 20 Mar | 6 | all | 19 | 8.16 | +0.11 (0.44) | +0.83 | −0.69 |
| 15 Jan – 31 Mar | 4 | all | 20 | 8.00 | +0.06 (0.28) | +0.64 | −0.75 |
| 1 Feb – 10 Mar | 4 | all | 16 | 7.94 | +0.02 (0.34) | +0.30 | −0.84 |
| 1 Jan – 15 Apr | 4 | all | 20 | 8.00 | +0.05 (0.27) | +0.72 | −0.60 |
| 20 Jan – 20 Mar | 4 | less Nth road game | 20 | 8.00 | +0.30 (0.28) | +0.33 | −0.45 |

Two further rows vary the after-trip window rather than the trip itself; they are
in the same file and discussed under "The trip enters on one side only" below.

Three things fall out of that table that the README does not stop to say.

**The window is not what makes the trip unique.** Widening it to the entire
January-to-April stretch changes San Antonio's mean trip length by nothing at
all — still 8.00 games, still twenty seasons. The rodeo trip is not merely their
longest February road run, it is their longest road run of the whole second half
of the season, every year for twenty years. No definition finds them a longer
one.

**Neither number is fragile.** The trip coefficient sits between +0.02 and +0.30
under every definition, against standard errors of 0.27 to 0.44. San Antonio's
own deviation sits between −0.45 and −0.84, against a 95% interval that is about
four points wide in every specification. The nulls are not artifacts of where the
window was drawn.

**The slate gap is the sensitive one.** It ranges from +0.30 to +0.83, and the
bottom row is why. The Nth-straight-road-game control carries +0.10 per game,
so a model with it in expects more of a team eight games into a trip than one
without it, and the trip games sit at a mean depth of 4.6 road games against 1.7
for the rest of the road schedule. Drop that control and the gap halves.

The last row is worth keeping in view for another reason: the sibling schedule
project fits the same Nth-road-game term, gets the same slightly positive sign,
and says explicitly that it does not believe it. Anything downstream of it
inherits that doubt. What survives the doubt is the direction — the trip slate
is easier either way — and both nulls.

Two rows miss seasons. Requiring six games drops 2017-18, whose trip was six
games long but is caught by the four- and five-game floors — a boundary case, not
a finding. The narrow 1 February – 10 March window drops five rodeo trips: the
four that started in late January (2005, 2006, 2007 and 2008) and the compressed
2020-21 one, which ran in March. That row's 16 seasons are therefore 15 rodeo
trips plus one shorter run the detector picked up instead, which is why its
mean length and slate gap are the odd ones out.

## The trip enters on one side only

Every other schedule term in this model is differenced — home value minus away
value — which imposes that a burden costs whoever carries it the same amount.
A road trip cannot be differenced that way, because the home team is never on
one. So `d_trip` is minus the away team's indicator, and the coefficient reads
as the effect on the away team's own net rating.

The after-trip term *is* differenced, because two teams can both be in that state
in the same game, and occasionally are. "First games back" is the next N games in
date order, whatever venue they are played at — 72% of them are at home, and
nothing in the definition requires it — with N matching the length of the trip
that preceded it: eight games away, eight games watched afterwards.

That definition matters more than any other choice in this project, and it is the
soft spot in the results. `output/sensitivity.csv` carries the alternatives: a
fixed three-game window gives −0.55 (se 0.36), a fixed five-game window −0.19
(se 0.29), and matching the trip's own length −0.13 (se 0.28). Across all nine
specifications the term ranges from −0.55 to +0.54. None reaches significance and
the spread is wider than any single estimate, which is the honest summary: on
twenty trips this data cannot separate a hangover of half a point per 100 from
nothing. The README says the hangover is not there; it should be read as saying
that nothing here can find one.

## Why the win-rate comparison is the wrong one, twice

The folklore compares trip games to other road games. That comparison is wrong
in two independent ways, and they are worth separating because only one of them
is about the schedule.

**The slates are different.** The model's fitted value for a game is what it
expects of *that* Spurs team in that situation — its own team-season effect is in
there, along with the opponent's, the venue, the rest and the travel. Averaged
over the trip games it is +2.46 per 100; over the other road games, +1.84. Since
the Spurs term is common to both, the 0.6 between them is entirely opponent and
schedule.

About a third of it is the opponents: 50% of trip opponents are
eastern-conference teams against 33% of other road opponents, because a two-week
block has to be assembled out of whoever is at home and a Texas team's eastern
swing is the natural shape for one. Most of the rest is the Nth-straight-road-game
term, which the trip games sit deep in (mean 4.6 against 1.7) and which carries a
small positive coefficient the sibling project explicitly disbelieves. Dropping
that control halves the gap to 0.33 and leaves every conclusion where it was.

**The margins are identical and the wins are not.** San Antonio's actual net
rating is +1.74 on the trip and +1.76 elsewhere on the road. The 4.5-point win
gap is therefore entirely a close-game record: 58.5% in games decided by five or
fewer on the trip, 47.2% off it, on 41 and 178 games respectively. Nothing in
this project claims that is skill, and nothing in it could.

**The expectation excludes the trip terms.** This is the circularity trap and it
is easy to fall into. If the fitted value used to define "expected" includes
`d_trip`, then the residual has already had the league-wide trip effect
subtracted, and "San Antonio against expectation" silently becomes "San Antonio
against other teams on trips" — a different and much less interesting question.
So `run_02_trips.py` drops both trip columns from the fitted value before taking
residuals. `output/expectation_check.csv` reports it both ways: −0.89 circular,
−0.71 not. The difference is small and the point is not its size — it is that
only one of the two numbers means what the sentence around it says.

## What the bootstrap does and does not cover

`bootstrap_mean` resamples the 160 trip games with replacement, 5,000 times. It
prices the sampling variation in *those games' outcomes*. It does not price the
uncertainty in the fitted values themselves, which come from a model estimated
on all 23,838 games and are treated here as known.

That understates the interval by a little. It does not matter for what the
interval is used for, which is to say the effect is not distinguishable from
zero; a slightly wider interval is still not distinguishable from zero.

## Cross-check against the sibling project

The schedule controls here are fit on a different sample from the one in
`nba-schedule-tax` — this project drops the bubble games and adds two trip
terms — and they land in the same place:

| Term | Here | Sibling project |
|---|---|---|
| Back-to-back | −1.52 | −1.52 |
| Playing at altitude | −2.13 | −2.12 |
| Games in the past week | −0.37 | −0.38 |
| Time zones crossed | −0.32 | −0.32 |

That is the check that the trip term is being read off a model that works,
rather than off one that happens to have been tuned until the trip term behaved.

## Where this is thin

**No injury or rest data, and this is the Spurs.** The team most famous in the
league for sitting healthy starters is the team being studied, over the two
decades in which they did it. If the rodeo trip was systematically used to rest
players — or systematically not, because it was the trip that mattered — that is
inside the estimate. The null is "nothing after everything the schedule can
see", and a coach's roster decisions are not something the schedule can see.

**The All-Star break is inside seventeen of the twenty trips.** Seventeen
contain an internal gap of five days or more; the model has no term for it. A
trip interrupted by a week off is not the same object as one that is not, and
with twenty of them there is no way to separate the two.

**Twenty trips is twenty observations.** The game-level estimates use 160 games,
but games inside one trip are not independent of each other, and the effective
sample for anything about *trips* rather than about *games on trips* is closer to
twenty. Figure 04 is drawn with that in mind: it is a display of variation, not
a set of twenty estimates.

**Possessions are estimated** from the box score with FGA + 0.44×FTA − OREB +
TOV, averaged across the two teams. Fine at the level of a whole game, not fine
below it, and never used below it here.

**Regular season only, through 2022-23**, which is where the public mirror this
reads currently ends.
