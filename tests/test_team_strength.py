import pandas as pd
import pytest

from evaluation.backtest import STABLE_FEATURE_COLUMNS
from features.team_strength import (
    TeamIdentifierColumns,
    TeamStrengthError,
    add_elo_features,
    create_team_gameweek_table,
    detect_team_identifier_columns,
    initial_team_elos,
    normalize_position_label,
    normalize_team_identifier,
)


def player_gameweek_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "season": ["2023-24", "2023-24", "2023-24", "2023-24"],
            "gw": [1, 1, 1, 1],
            "element": [1, 2, 3, 4],
            "team": [1, 1, 2, 2],
            "opponent_team": [2, 2, 1, 1],
            "was_home": [True, True, False, False],
            "team_h_score": [3, 3, 3, 3],
            "team_a_score": [1, 1, 1, 1],
        }
    )


def test_normalization_helpers() -> None:
    assert normalize_position_label("GKP") == "GK"
    assert normalize_position_label("AM") is None
    assert normalize_team_identifier(" ars ") == "ARS"
    assert normalize_team_identifier(1) == "1"


def test_detect_team_identifier_columns() -> None:
    detected = detect_team_identifier_columns(player_gameweek_frame())

    assert detected == TeamIdentifierColumns(
        team="team",
        opponent_team="opponent_team",
        was_home="was_home",
    )


def test_team_gameweek_table_has_expected_columns_when_source_columns_exist() -> None:
    table = create_team_gameweek_table(player_gameweek_frame())

    assert list(table.columns) == [
        "season",
        "gw",
        "team",
        "opponent_team",
        "was_home",
        "goals_scored",
        "goals_conceded",
    ]
    home = table.loc[table["team"] == "1"].iloc[0]
    away = table.loc[table["team"] == "2"].iloc[0]
    assert home["goals_scored"] == 3
    assert home["goals_conceded"] == 1
    assert away["goals_scored"] == 1
    assert away["goals_conceded"] == 3


def test_duplicate_player_rows_do_not_create_duplicate_team_gameweek_rows() -> None:
    table = create_team_gameweek_table(player_gameweek_frame())

    assert len(table) == 2
    assert table[["season", "gw", "team"]].drop_duplicates().shape[0] == 2


def test_season_and_gameweek_are_preserved() -> None:
    source = player_gameweek_frame()
    source.loc[:, "season"] = "2024-25"
    source.loc[:, "gw"] = 12

    table = create_team_gameweek_table(source)

    assert set(table["season"]) == {"2024-25"}
    assert set(table["gw"]) == {12}


def test_goals_are_omitted_when_scores_cannot_be_reliably_derived() -> None:
    source = player_gameweek_frame().drop(columns=["was_home"])

    table = create_team_gameweek_table(source)

    assert "goals_scored" not in table.columns
    assert "goals_conceded" not in table.columns


def test_missing_team_identifier_fails_clearly() -> None:
    with pytest.raises(TeamStrengthError, match="Could not detect team identifier"):
        create_team_gameweek_table(pd.DataFrame({"season": ["2023-24"], "gw": [1]}))


def test_raw_team_columns_are_not_model_features() -> None:
    assert "team" not in STABLE_FEATURE_COLUMNS
    assert "opponent_team" not in STABLE_FEATURE_COLUMNS


def elo_source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "season": ["2023-24", "2023-24", "2023-24", "2023-24", "2023-24"],
            "gw": [1, 1, 2, 2, 1],
            "team": ["A", "B", "A", "B", "C"],
            "opponent_team": ["B", "A", "B", "A", "D"],
            "was_home": [True, False, False, True, True],
            "goals_scored": [3, 1, 0, 0, 2],
            "goals_conceded": [1, 3, 0, 0, 2],
        }
    )


def test_elo_for_gameweek_does_not_include_same_gameweek_result() -> None:
    features = add_elo_features(elo_source_frame())
    gw1 = features.loc[(features["season"] == "2023-24") & (features["gw"] == 1)]

    assert set(gw1["pre_gw_team_elo"]) == {1500.0}
    assert set(gw1["pre_gw_opponent_elo"]) == {1500.0}


def test_elo_update_affects_next_gameweek_only() -> None:
    features = add_elo_features(elo_source_frame())
    team_a_gw1 = features.loc[(features["team"] == "A") & (features["gw"] == 1)].iloc[0]
    team_a_gw2 = features.loc[(features["team"] == "A") & (features["gw"] == 2)].iloc[0]

    assert team_a_gw1["pre_gw_team_elo"] == 1500.0
    assert team_a_gw2["pre_gw_team_elo"] == 1510.0
    assert team_a_gw2["pre_gw_opponent_elo"] == 1490.0


def test_home_adjusted_elo_difference_is_temporary() -> None:
    features = add_elo_features(elo_source_frame(), home_advantage=50)
    home = features.loc[(features["team"] == "A") & (features["gw"] == 1)].iloc[0]
    away = features.loc[(features["team"] == "B") & (features["gw"] == 1)].iloc[0]

    assert home["elo_difference"] == 0.0
    assert home["home_adjusted_elo_difference"] == 50.0
    assert away["elo_difference"] == 0.0
    assert away["home_adjusted_elo_difference"] == -50.0
    assert features.loc[(features["team"] == "A") & (features["gw"] == 2)].iloc[0][
        "pre_gw_team_elo"
    ] == 1510.0


def test_elo_resets_at_season_boundaries() -> None:
    source = pd.concat(
        [
            elo_source_frame(),
            pd.DataFrame(
                {
                    "season": ["2024-25"],
                    "gw": [1],
                    "team": ["A"],
                    "opponent_team": ["B"],
                    "was_home": [True],
                    "goals_scored": [0],
                    "goals_conceded": [1],
                }
            ),
        ],
        ignore_index=True,
    )

    features = add_elo_features(source)
    new_season = features.loc[(features["season"] == "2024-25") & (features["team"] == "A")].iloc[0]

    assert new_season["pre_gw_team_elo"] == 1500.0
    assert new_season["pre_gw_opponent_elo"] == 1500.0


def test_unknown_teams_fall_back_to_base_elo() -> None:
    features = add_elo_features(
        pd.DataFrame(
            {
                "season": ["2023-24"],
                "gw": [1],
                "team": ["UNKNOWN"],
                "opponent_team": ["ALSO_UNKNOWN"],
                "was_home": [True],
                "goals_scored": [1],
                "goals_conceded": [1],
            }
        )
    )

    assert features.iloc[0]["pre_gw_team_elo"] == 1500.0
    assert features.iloc[0]["pre_gw_opponent_elo"] == 1500.0


def test_previous_season_position_prior_is_used_when_available() -> None:
    priors = pd.DataFrame(
        {
            "season": ["2024-25"],
            "team": ["A"],
            "previous_season_position": [1],
            "promoted_status": ["returning"],
            "promoted_rank": [pd.NA],
        }
    )

    elos = initial_team_elos(
        pd.Series(["A"]),
        season="2024-25",
        team_season_priors=priors,
    )

    assert elos["A"] == 1600.0


def test_previous_final_elo_is_blended_with_table_position_prior() -> None:
    priors = pd.DataFrame(
        {
            "season": ["2024-25"],
            "team": ["A"],
            "previous_season_position": [1],
            "promoted_status": ["returning"],
            "promoted_rank": [pd.NA],
        }
    )

    elos = initial_team_elos(
        pd.Series(["A"]),
        season="2024-25",
        previous_season_final_elos={"A": 1700.0},
        team_season_priors=priors,
    )

    assert elos["A"] == 1670.0


def test_promoted_teams_get_lower_priors_than_strong_returning_teams() -> None:
    priors = pd.DataFrame(
        {
            "season": ["2024-25", "2024-25"],
            "team": ["A", "B"],
            "previous_season_position": [1, pd.NA],
            "promoted_status": ["returning", "promoted"],
            "promoted_rank": [pd.NA, 1],
        }
    )

    elos = initial_team_elos(
        pd.Series(["A", "B"]),
        season="2024-25",
        team_season_priors=priors,
    )

    assert elos["A"] == 1600.0
    assert elos["B"] == 1470.0
    assert elos["B"] < elos["A"]


def test_unknown_promoted_rank_falls_back_to_1450() -> None:
    priors = pd.DataFrame(
        {
            "season": ["2024-25"],
            "team": ["B"],
            "previous_season_position": [pd.NA],
            "promoted_status": ["promoted"],
            "promoted_rank": [pd.NA],
        }
    )

    elos = initial_team_elos(
        pd.Series(["B"]),
        season="2024-25",
        team_season_priors=priors,
    )

    assert elos["B"] == 1450.0


def test_unknown_team_without_prior_falls_back_to_1500() -> None:
    elos = initial_team_elos(pd.Series(["UNKNOWN"]), season="2024-25")

    assert elos["UNKNOWN"] == 1500.0


def test_current_season_final_position_is_not_used_for_start_elo() -> None:
    priors = pd.DataFrame(
        {
            "season": ["2024-25", "2025-26"],
            "team": ["A", "A"],
            "previous_season_position": [10, 1],
            "promoted_status": ["returning", "returning"],
            "promoted_rank": [pd.NA, pd.NA],
        }
    )

    elos = initial_team_elos(
        pd.Series(["A"]),
        season="2024-25",
        team_season_priors=priors,
    )

    assert elos["A"] == 1555.0
