# FPL API Vaastav Adapter Report

Season: `2025-26`
Output: `data/interim/fpl_api/2025-26/merged_gw_api.parquet`
Rows produced: 28066

## Rows Produced By GW

| gw | rows |
| --- | --- |
| 1 | 690 |
| 2 | 705 |
| 3 | 712 |
| 4 | 740 |
| 5 | 741 |
| 6 | 742 |
| 7 | 743 |
| 8 | 745 |
| 9 | 746 |
| 10 | 747 |
| 11 | 752 |
| 12 | 755 |
| 13 | 755 |
| 14 | 758 |
| 15 | 759 |
| 16 | 760 |
| 17 | 770 |
| 18 | 775 |
| 19 | 780 |
| 20 | 790 |
| 21 | 795 |
| 22 | 799 |
| 23 | 803 |
| 24 | 811 |
| 25 | 817 |
| 26 | 896 |
| 27 | 818 |
| 28 | 819 |
| 29 | 820 |
| 30 | 822 |
| 31 | 664 |
| 32 | 826 |
| 33 | 1077 |
| 34 | 582 |
| 35 | 832 |
| 36 | 920 |

## Required Columns

Present: GW, bonus, bps, element, expected_assists, expected_goal_involvements, expected_goals, expected_goals_conceded, fixture, gw, id, minutes, name, opponent_team, position, season, selected, starts, team, team_a_score, team_h_score, total_points, transfers_in, transfers_out, value, was_home

Missing: None

## Optional Columns

Present: GW, assists, attempted_passes, big_chances_created, big_chances_missed, clean_sheets, clearances_blocks_interceptions, completed_passes, creativity, defensive_contribution, dribbles, ea_index, errors_leading_to_goal, errors_leading_to_goal_attempt, fixture, fouls, goals_conceded, goals_scored, ict_index, id, influence, key_passes, kickoff_time, kickoff_time_formatted, loaned_in, loaned_out, mng_clean_sheets, mng_draw, mng_goals_scored, mng_loss, mng_underdog_draw, mng_underdog_win, mng_win, modified, offside, open_play_crosses, own_goals, penalties_conceded, penalties_missed, penalties_saved, recoveries, red_cards, round, saves, tackled, tackles, target_missed, team_a_score, team_h_score, threat, transfers_balance, winning_goals, xP, yellow_cards

Missing: None

## Columns Filled As NA

attempted_passes, big_chances_created, big_chances_missed, completed_passes, dribbles, ea_index, errors_leading_to_goal, errors_leading_to_goal_attempt, fouls, id, key_passes, kickoff_time_formatted, loaned_in, loaned_out, mng_clean_sheets, mng_draw, mng_goals_scored, mng_loss, mng_underdog_draw, mng_underdog_win, mng_win, offside, open_play_crosses, penalties_conceded, tackled, target_missed, winning_goals, xP

## Schema Differences From Vaastav merged_gw

Extra normalized API columns retained: None

Some older Vaastav pass/chance/manager fields may be present only as all-NA compatibility columns because they are not available in the sampled official API.

## Assumptions

- Only seasons >= 2025-26 are accepted.
- `name`, `position`, and `team` are joined from `elements` and `teams`.
- `gw` and `GW` come from history `round` when missing.
- Unavailable compatibility columns are filled with NA instead of being fabricated.
- This command does not merge FPL API rows with Vaastav history.
