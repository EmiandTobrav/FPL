import pandas as pd

from evaluation.position_feature_relevance import (
    candidate_feature_columns,
    build_relevance_table,
)


def relevance_frame() -> pd.DataFrame:
    rows = []
    for season, offset in [("2022-23", 0), ("2023-24", 10), ("2024-25", 20)]:
        for position in ["GK", "DEF", "MID", "FWD"]:
            for element in range(1, 8):
                points = offset + element
                rows.append(
                    {
                        "name": f"{position}-{element}",
                        "element": element,
                        "season": season,
                        "gw": element,
                        "position": position,
                        "team": "ARS",
                        "opponent_team": "CHE",
                        "total_points": points,
                        "minutes": 90,
                        "next_gw_points": points + (5 if position == "FWD" else 1),
                        "next_3_gw_points": points + 3,
                        "points_last_1": points - 1,
                        "points_mean_last_3": points - 0.5,
                        "points_mean_last_5": points - 0.25,
                        "minutes_mean_last_3": 80,
                        "minutes_mean_last_5": 85,
                        "starts_last_5": 0.8,
                        "bonus_last_5": element / 10,
                        "bps_last_5": element,
                        "team_elo_pre_gw": 1500 + element,
                        "opponent_elo_pre_gw": 1500 - element,
                        "elo_difference": element * 2,
                        "home_adjusted_elo_difference": element * 2 + 50,
                        "was_home": element % 2 == 0,
                    }
                )
    return pd.DataFrame(rows)


def test_candidate_feature_columns_exclude_raw_outcomes_teams_identifiers_and_targets() -> None:
    candidates = set(candidate_feature_columns(relevance_frame()))

    forbidden = {
        "total_points",
        "minutes",
        "team",
        "opponent_team",
        "name",
        "element",
        "next_gw_points",
        "next_3_gw_points",
        "position",
    }
    assert not forbidden.intersection(candidates)
    assert {"points_mean_last_3", "pred_minutes_adjusted_rolling_mean", "was_home"}.issubset(
        candidates
    )


def test_build_relevance_table_reports_each_position_and_safe_features() -> None:
    relevance = build_relevance_table(relevance_frame(), random_state=7)

    assert set(relevance["position"]) == {"GK", "DEF", "MID", "FWD"}
    assert "points_mean_last_3" in set(relevance["feature"])
    assert "team" not in set(relevance["feature"])
    assert "spearman" in relevance.columns
    assert "mutual_information" in relevance.columns
    assert "useful_in_at_least_2_of_3" in relevance.columns
