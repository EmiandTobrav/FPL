import pandas as pd
import pytest

from features.rolling_features import build_rolling_features
from features.target_builder import build_targets


def sample_gameweeks() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "element": [1, 1, 1, 1, 1, 1],
            "season": ["2023-24"] * 6,
            "gw": [1, 2, 3, 4, 5, 6],
            "total_points": [10, 20, 30, 40, 50, 60],
            "minutes": [90, 80, 70, 60, 50, 40],
            "starts": [1, 1, 1, 0, 1, 0],
            "xG": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            "xA": [1.1, 1.2, 1.3, 1.4, 1.5, 1.6],
            "bonus": [0, 1, 2, 3, 4, 5],
            "bps": [5, 10, 15, 20, 25, 30],
            "goals_scored": [0, 1, 2, 3, 4, 5],
            "assists": [5, 4, 3, 2, 1, 0],
            "clean_sheets": [1, 0, 1, 0, 1, 0],
            "goals_conceded": [0, 1, 0, 2, 0, 3],
            "influence": [10, 20, 30, 40, 50, 60],
            "creativity": [1, 2, 3, 4, 5, 6],
            "threat": [6, 5, 4, 3, 2, 1],
            "ict_index": [2, 4, 6, 8, 10, 12],
            "expected_goals": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            "expected_assists": [0.5, 0.4, 0.3, 0.2, 0.1, 0.0],
            "expected_goal_involvements": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
            "expected_goals_conceded": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5],
            "selected": [100, 110, 120, 130, 140, 150],
            "transfers_in": [0, 10, 20, 30, 40, 50],
            "transfers_out": [5, 4, 3, 2, 1, 0],
            "transfers_balance": [-5, 6, 17, 28, 39, 50],
            "was_home": [True, False, True, False, True, False],
        }
    )


def test_rolling_features_use_only_previous_gameweeks() -> None:
    result = build_rolling_features(sample_gameweeks())
    gw4 = result.loc[result["gw"] == 4].iloc[0]

    assert gw4["points_last_1"] == 30
    assert gw4["points_mean_last_3"] == 20
    assert gw4["points_mean_last_5"] == 20
    assert gw4["minutes_mean_last_3"] == 80
    assert gw4["minutes_mean_last_5"] == 80
    assert gw4["starts_last_5"] == 3
    assert gw4["xG_last_5"] == 0.6
    assert gw4["xA_last_5"] == 3.6
    assert gw4["bonus_last_5"] == 3
    assert gw4["bps_last_5"] == 30
    assert gw4["goals_scored_mean_last_3"] == 1
    assert gw4["goals_scored_mean_last_5"] == 1
    assert gw4["assists_mean_last_3"] == 4
    assert gw4["clean_sheets_mean_last_3"] == 2 / 3
    assert gw4["goals_conceded_mean_last_3"] == 1 / 3
    assert gw4["influence_mean_last_3"] == 20
    assert gw4["expected_goals_mean_last_3"] == pytest.approx(0.1)
    assert gw4["selected_lag_1"] == 120
    assert gw4["transfers_in_lag_1"] == 20
    assert gw4["transfers_out_lag_1"] == 3
    assert gw4["transfers_balance_lag_1"] == 17
    assert bool(gw4["was_home"]) is False


def test_rolling_features_do_not_use_current_gameweek() -> None:
    base = sample_gameweeks()
    changed_current = base.copy()
    changed_current.loc[changed_current["gw"] == 4, "total_points"] = 999
    changed_current.loc[changed_current["gw"] == 4, "minutes"] = 999
    changed_current.loc[changed_current["gw"] == 4, "starts"] = 999
    changed_current.loc[changed_current["gw"] == 4, "xG"] = 999
    changed_current.loc[changed_current["gw"] == 4, "xA"] = 999
    changed_current.loc[changed_current["gw"] == 4, "bonus"] = 999
    changed_current.loc[changed_current["gw"] == 4, "bps"] = 999
    changed_current.loc[changed_current["gw"] == 4, "goals_scored"] = 999
    changed_current.loc[changed_current["gw"] == 4, "assists"] = 999
    changed_current.loc[changed_current["gw"] == 4, "influence"] = 999
    changed_current.loc[changed_current["gw"] == 4, "expected_goals"] = 999
    changed_current.loc[changed_current["gw"] == 4, "selected"] = 999

    base_gw4 = build_rolling_features(base).loc[lambda data: data["gw"] == 4].iloc[0]
    changed_gw4 = build_rolling_features(changed_current).loc[lambda data: data["gw"] == 4].iloc[0]
    feature_columns = [
        "points_last_1",
        "points_mean_last_3",
        "points_mean_last_5",
        "minutes_mean_last_3",
        "minutes_mean_last_5",
        "starts_last_5",
        "xG_last_5",
        "xA_last_5",
        "bonus_last_5",
        "bps_last_5",
        "goals_scored_mean_last_3",
        "goals_scored_mean_last_5",
        "assists_mean_last_3",
        "influence_mean_last_3",
        "expected_goals_mean_last_3",
        "selected_lag_1",
    ]

    pd.testing.assert_series_equal(base_gw4[feature_columns], changed_gw4[feature_columns])


def test_candidate_rolling_features_do_not_cross_season_boundaries() -> None:
    data = pd.DataFrame(
        {
            "element": [1, 1, 1],
            "season": ["2022-23", "2023-24", "2023-24"],
            "gw": [38, 1, 2],
            "total_points": [10, 100, 200],
            "minutes": [90, 90, 90],
            "bonus": [0, 0, 0],
            "bps": [1, 1, 1],
            "goals_scored": [5, 1, 3],
            "selected": [10, 100, 200],
            "was_home": [True, False, True],
        }
    )

    result = build_rolling_features(data)
    first_new_season = result.loc[(result["season"] == "2023-24") & (result["gw"] == 1)].iloc[0]
    second_new_season = result.loc[(result["season"] == "2023-24") & (result["gw"] == 2)].iloc[0]

    assert pd.isna(first_new_season["goals_scored_mean_last_3"])
    assert pd.isna(first_new_season["selected_lag_1"])
    assert second_new_season["goals_scored_mean_last_3"] == 1
    assert second_new_season["selected_lag_1"] == 100


def test_missing_candidate_source_columns_are_skipped_safely() -> None:
    data = sample_gameweeks().drop(
        columns=[
            "goals_scored",
            "assists",
            "expected_goals",
            "selected",
            "transfers_in",
            "transfers_out",
            "transfers_balance",
        ]
    )

    result = build_rolling_features(data)

    assert "goals_scored_mean_last_3" not in result.columns
    assert "assists_mean_last_3" not in result.columns
    assert "expected_goals_mean_last_3" not in result.columns
    assert "selected_lag_1" not in result.columns


def test_targets_use_future_gameweeks_only() -> None:
    result = build_targets(sample_gameweeks())
    gw2 = result.loc[result["gw"] == 2].iloc[0]

    assert gw2["next_gw_points"] == 30
    assert gw2["next_3_gw_points"] == 120


def test_targets_do_not_cross_players_or_seasons() -> None:
    data = pd.DataFrame(
        {
            "element": [1, 1, 1, 1],
            "season": ["2022-23", "2022-23", "2023-24", "2023-24"],
            "gw": [37, 38, 1, 2],
            "total_points": [1, 2, 100, 200],
        }
    )

    result = build_targets(data)
    last_old_season = result.loc[(result["season"] == "2022-23") & (result["gw"] == 38)].iloc[0]
    first_new_season = result.loc[(result["season"] == "2023-24") & (result["gw"] == 1)].iloc[0]

    assert pd.isna(last_old_season["next_gw_points"])
    assert first_new_season["next_gw_points"] == 200
