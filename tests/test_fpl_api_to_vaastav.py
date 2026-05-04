from __future__ import annotations

from pathlib import Path
import shutil

import pandas as pd
import pytest

from data.fpl_api_to_vaastav import (
    FplApiVaastavAdapterError,
    adapt_fpl_api_season,
    adapt_fpl_api_tables,
    season_is_supported,
    write_adapter_report,
)


def clean_scratch(name: str) -> Path:
    path = Path("tests") / f".tmp_{name}"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


def sample_history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "element": [11, 12],
            "round": [1, 2],
            "fixture": [100, 101],
            "opponent_team": [2, 3],
            "was_home": [True, False],
            "total_points": [6, 2],
            "minutes": [90, 45],
            "starts": [1, 0],
            "bonus": [1, 0],
            "bps": [20, 5],
            "selected": [1000, 900],
            "transfers_in": [100, 50],
            "transfers_out": [20, 10],
            "value": [75, 55],
            "expected_goals": [0.2, 0.0],
            "expected_assists": [0.1, 0.3],
            "expected_goal_involvements": [0.3, 0.3],
            "expected_goals_conceded": [1.1, 0.8],
            "team_h_score": [2, 1],
            "team_a_score": [1, 1],
        }
    )


def sample_elements() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [11, 12],
            "web_name": ["Saka", "Raya"],
            "first_name": ["Bukayo", "David"],
            "second_name": ["Saka", "Raya"],
            "element_type": [3, 1],
            "team": [1, 1],
        }
    )


def sample_teams() -> pd.DataFrame:
    return pd.DataFrame({"id": [1, 2, 3], "name": ["Arsenal", "Chelsea", "Spurs"]})


def test_supported_season_starts_at_2025_26() -> None:
    assert season_is_supported("2025-26")
    assert season_is_supported("2026-27")
    assert not season_is_supported("2024-25")


def test_adapter_creates_vaastav_style_required_columns() -> None:
    result = adapt_fpl_api_tables(
        season="2025-26",
        history=sample_history(),
        elements=sample_elements(),
        teams=sample_teams(),
    )

    row = result.loc[result["element"].eq(11)].iloc[0]

    assert row["season"] == "2025-26"
    assert row["gw"] == 1
    assert row["GW"] == 1
    assert row["name"] == "Saka"
    assert row["team"] == "Arsenal"
    assert row["position"] == "MID"
    assert row["opponent_team"] == 2
    assert bool(row["was_home"]) is True
    assert row["total_points"] == 6
    assert row["minutes"] == 90
    assert row["starts"] == 1
    assert row["bonus"] == 1
    assert row["bps"] == 20
    assert row["expected_goals"] == 0.2
    assert row["expected_assists"] == 0.1
    assert row["expected_goal_involvements"] == 0.3
    assert row["expected_goals_conceded"] == 1.1


def test_adapter_rejects_pre_2025_26_seasons() -> None:
    with pytest.raises(FplApiVaastavAdapterError, match="2025-26"):
        adapt_fpl_api_tables(
            season="2024-25",
            history=sample_history(),
            elements=sample_elements(),
            teams=sample_teams(),
        )


def test_adapter_fills_unavailable_optional_columns_with_na() -> None:
    result = adapt_fpl_api_tables(
        season="2025-26",
        history=sample_history(),
        elements=sample_elements(),
        teams=sample_teams(),
    )

    assert "attempted_passes" in result.columns
    assert "mng_win" in result.columns
    assert result["attempted_passes"].isna().all()
    assert result["mng_win"].isna().all()


def test_adapt_fpl_api_season_reads_tables_writes_output_and_report() -> None:
    scratch = clean_scratch("fpl_api_to_vaastav")
    try:
        season_dir = scratch / "2025-26"
        season_dir.mkdir(parents=True)
        sample_history().to_parquet(season_dir / "player_gameweek_history.parquet", index=False)
        sample_elements().to_parquet(season_dir / "elements.parquet", index=False)
        sample_teams().to_parquet(season_dir / "teams.parquet", index=False)
        mapping_path = scratch / "mapping.csv"
        pd.DataFrame(
            {
                "vaastav_column": ["element", "season", "gw", "total_points"],
                "current_pipeline_importance": ["essential", "essential", "essential", "essential"],
            }
        ).to_csv(mapping_path, index=False)

        merged, summary = adapt_fpl_api_season(
            season="2025-26",
            input_root=scratch,
            mapping_report_path=mapping_path,
        )
        report_path = scratch / "adapter_report.md"
        write_adapter_report(merged, summary, output_path=report_path)

        assert (season_dir / "merged_gw_api.parquet").exists()
        assert summary.rows_produced == 2
        assert "element" in summary.required_present
        assert not summary.required_missing
        assert "attempted_passes" in summary.columns_filled_na
        assert "Rows Produced By GW" in report_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
