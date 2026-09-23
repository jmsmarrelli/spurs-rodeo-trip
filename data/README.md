# Data

Two files per season in `data/raw/`:

* `nba_schedule_<season>.csv` — every game, with the venue city, which is what
  the trip detection and the travel calculation both key off.
* `team_box_<season>.csv.gz` — team box scores, for scores and for the
  possession estimate.

`<season>` is the year the season ended: 2023 is 2022-23.

## Getting the files

Both come from [sportsdataverse/hoopR-data](https://github.com/sportsdataverse/hoopR-data),
a mirror of ESPN's public feeds.

```bash
git clone --filter=blob:none --no-checkout --depth 1 \
  https://github.com/sportsdataverse/hoopR-data.git /tmp/hoopR-data
cd /tmp/hoopR-data
git sparse-checkout set --no-cone "nba/schedules/csv/*" "nba/team_box/csv/*"
git checkout
cd -
cp /tmp/hoopR-data/nba/schedules/csv/nba_schedule_20*.csv data/raw/
cp /tmp/hoopR-data/nba/team_box/csv/team_box_20*.csv.gz data/raw/
```

About 30 MB. `data/raw/` and `data/processed/` are gitignored; everything the
analysis cites is written to `output/` and committed.

## Filters applied in stage 1

| Filter | Why |
|---|---|
| `season_type == 2` | regular season only |
| both teams in the 32-franchise list | drops All-Star and exhibition rows, which the source files carry with the same season type |
| game marked completed | drops postponements |
| estimated possessions > 60 | drops rows with a broken or partial box score |
| venue city present in `venues.CITIES` | every city in twenty seasons is mapped, so this drops nothing today; a new one would be named on stderr and dropped |

23,926 games survive. Stage 2 then drops the 88 played in the 2019-20 Florida
restart, leaving 23,838 in the model.

## Location comes from the venue, not the team

The trip detector asks "was this team at home?", which sounds like a question
about the team and is really a question about the building. Twenty seasons
contain a lot of teams that were not where their name says: the Hornets played
71 of 80 home games in Oklahoma City across 2005-06 and 2006-07, the Nets moved
twice, the Warriors crossed the bay in 2019-20, the Raptors spent 2020-21 in
Tampa, and 88 games of 2019-20 were played in one Florida complex.

All of that falls out correctly from the schedule's venue field. None of it
falls out from the team name, and a detector keyed off the team name would have
credited Toronto with a 2020-21 season of home games in a city they never
entered.

## Columns used

| Column | Used for |
|---|---|
| `game_id`, `season`, `game_date` | joining, and walking each schedule in order |
| `venue_address_city` | where the game was played: travel, altitude, time zones |
| `home_abbreviation`, `away_abbreviation` | which side of the game a team is on |
| `team_home_away`, `team_score` (box) | the margin, taken from the box score rather than the schedule |
| `field_goals_attempted`, `free_throws_attempted`, `offensive_rebounds`, `turnovers` (box) | the possession estimate |
| `neutral_site` | carried through the panel; the bubble is excluded by venue city, not by this |
| `season_type`, `status_type_completed` | the filters above |
