from pathlib import Path
import shutil

import pandas as pd

from data.build_prediction_rows import (
    build_prediction_rows,
    build_prediction_rows_from_files,
    next_unfinished_gameweek,
)


def clean_scratch(name: str) -> Path:
    path = Path("tests") / f".tmp_{name}"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


def sample_fixtures() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [10, 11, 12, 13],
            "event": [1, 2, 2, 3],
            "team_h": [1, 1, 3, 2],
            "team_a": [2, 2, 1, 3],
            "kickoff_time": ["done", "k1", "k2", "future"],
            "finished": [True, False, False, False],
            "started": [True, False, False, False],
        }
    )


def sample_elements() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [101, 102, 201, 301],
            "web_name": ["A1", "A2", "B1", "C1"],
            "element_type": [3, 2, 4, 1],
            "team": [1, 1, 2, 3],
            "now_cost": [75, 55, 65, 45],
            "selected_by_percent": ["20.0", "10.0", "5.0", "2.0"],
            "transfers_in": [100, 50, 10, 5],
            "transfers_out": [20, 15, 3, 1],
        }
    )


def sample_teams() -> pd.DataFrame:
    return pd.DataFrame({"id": [1, 2, 3, 4], "name": ["A", "B", "C", "Blank"]})


def sample_upcoming() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "element": [101, 101],
            "id": [11, 12],
            "event": [2, 2],
            "kickoff_time": ["uk1", "uk2"],
            "is_home": [True, False],
        }
    )


def test_next_unfinished_gameweek_uses_earliest_unfinished_fixture_event() -> None:
    assert next_unfinished_gameweek(sample_fixtures()) == 2


def test_prediction_rows_create_one_player_fixture_row_and_handle_double_gameweeks() -> None:
    rows, summary = build_prediction_rows(
        season="2025-26",
        fixtures=sample_fixtures(),
        elements=sample_elements(),
        teams=sample_teams(),
        upcoming_player_fixtures=sample_upcoming(),
    )

    team_a_rows = rows.loc[rows["team"].eq("A")]

    assert summary.gw == 2
    assert summary.fixture_count == 2
    assert len(team_a_rows.loc[team_a_rows["element"].eq(101)]) == 2
    assert len(team_a_rows.loc[team_a_rows["element"].eq(102)]) == 2
    assert summary.double_fixture_teams == ("A",)
    assert set(team_a_rows["fixture"]) == {11, 12}


def test_prediction_rows_exclude_blank_teams_and_report_affected_players() -> None:
    elements = pd.concat(
        [
            sample_elements(),
            pd.DataFrame(
                {
                    "id": [401],
                    "web_name": ["D1"],
                    "element_type": [3],
                    "team": [4],
                    "now_cost": [50],
                    "selected_by_percent": ["1.0"],
                    "transfers_in": [0],
                    "transfers_out": [0],
                }
            ),
        ],
        ignore_index=True,
    )

    rows, summary = build_prediction_rows(
        season="2025-26",
        fixtures=sample_fixtures(),
        elements=elements,
        teams=sample_teams(),
        upcoming_player_fixtures=sample_upcoming(),
    )

    assert 401 not in set(rows["element"])
    assert summary.blank_teams == ("Blank",)
    assert summary.blank_player_count == 1


def test_prediction_rows_keep_outcomes_missing_and_fixture_metadata_present() -> None:
    rows, summary = build_prediction_rows(
        season="2025-26",
        fixtures=sample_fixtures(),
        elements=sample_elements(),
        teams=sample_teams(),
        upcoming_player_fixtures=sample_upcoming(),
    )

    for column in ("total_points", "minutes", "starts", "bonus", "bps"):
        assert column in rows.columns
        assert rows[column].isna().all()
        assert column in summary.outcome_columns_missing
    assert {"fixture", "kickoff_time", "finished", "started"}.issubset(rows.columns)
    assert rows.loc[(rows["element"] == 101) & (rows["fixture"] == 11), "kickoff_time"].iloc[0] == "k1"


def test_prediction_rows_validate_against_completed_schema() -> None:
    completed = pd.DataFrame(columns=["season", "gw", "element", "fixture", "legacy_only"])

    _, summary = build_prediction_rows(
        season="2025-26",
        fixtures=sample_fixtures(),
        elements=sample_elements(),
        teams=sample_teams(),
        completed_schema=completed,
    )

    assert summary.schema_missing_from_completed == ("legacy_only",)


def test_build_prediction_rows_from_files_writes_output_and_report() -> None:
    scratch = clean_scratch("build_prediction_rows")
    try:
        season_dir = scratch / "2025-26"
        season_dir.mkdir(parents=True)
        sample_fixtures().to_parquet(season_dir / "fixtures.parquet", index=False)
        sample_elements().to_parquet(season_dir / "elements.parquet", index=False)
        sample_teams().to_parquet(season_dir / "teams.parquet", index=False)
        sample_upcoming().to_parquet(season_dir / "upcoming_player_fixtures.parquet", index=False)
        pd.DataFrame(columns=["season", "gw", "element", "fixture"]).to_parquet(
            season_dir / "merged_gw_api.parquet",
            index=False,
        )
        report_path = scratch / "report.md"

        rows, summary = build_prediction_rows_from_files(
            season="2025-26",
            input_root=scratch,
            report_path=report_path,
        )

        assert (season_dir / "prediction_rows_gw2.parquet").exists()
        assert len(pd.read_parquet(season_dir / "prediction_rows_gw2.parquet")) == len(rows)
        assert summary.output_path == season_dir / "prediction_rows_gw2.parquet"
        assert "Prediction Row Builder Report" in report_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
