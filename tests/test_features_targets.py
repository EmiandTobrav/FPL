import pandas as pd

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
    ]

    pd.testing.assert_series_equal(base_gw4[feature_columns], changed_gw4[feature_columns])


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
