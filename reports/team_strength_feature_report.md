# Team-Strength Feature Report

## Identifier Mapping Diagnostics

| diagnostic | value |
| --- | ---: |
| rows with valid normalized team IDs | 63.3% |
| rows with valid normalized opponent IDs | 63.3% |

Seasons where mapping works: 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26

Seasons where mapping fails:

- `2016-17`: team/opponent identifier types are unsupported or team names are missing
- `2017-18`: team/opponent identifier types are unsupported or team names are missing
- `2018-19`: team/opponent identifier types are unsupported or team names are missing
- `2019-20`: team/opponent identifier types are unsupported or team names are missing

## Features Added

- `team_elo_pre_gw`
- `opponent_elo_pre_gw`
- `elo_difference`
- `home_adjusted_elo_difference`

Raw `team` and `opponent_team` are used only as source columns for normalized identifiers and are not model features.

## Features Skipped

Rolling team goal-form features are still not integrated. The identifier mapping now supports reliable joins for seasons listed above, but rolling form features are intentionally left for a separate modelling change.

## Elo Initialization

- `base_elo = 1500`
- `k_factor = 20`
- `home_advantage = 50`
- Optional manual priors are read from `data/manual/team_season_priors.csv` when present.
