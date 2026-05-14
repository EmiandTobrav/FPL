from pathlib import Path
import shutil

import pandas as pd

from data.combine_merged_gw import (
    combine_from_paths,
    combine_merged_gw_sources,
    required_column_coverage,
    write_combined_dataset,
)


def clean_scratch(name: str) -> Path:
    path = Path("tests") / f".tmp_{name}"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


def vaastav_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "season": ["2024-25", "2025-26"],
            "gw": [1, 1],
            "element": [1, 1],
            "name": ["Historical", "Dropped"],
            "team": ["A", "A"],
            "opponent_team": [2, 3],
            "was_home": [True, False],
            "position": ["MID", "MID"],
            "total_points": [5, 99],
            "minutes": [90, 90],
            "bonus": [1, 3],
            "bps": [20, 30],
        }
    )


def fpl_api_frame(season: str = "2025-26") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "season": [season],
            "gw": [1],
            "element": [1],
            "name": ["API"],
            "team": ["A"],
            "opponent_team": [3],
            "was_home": [False],
            "position": ["MID"],
            "total_points": [7],
            "minutes": [90],
            "bonus": [2],
            "bps": [25],
            "expected_goals": [0.5],
        }
    )


def fpl_api_frame_with_numeric_strings(season: str = "2025-26") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "season": [season, season],
            "gw": ["1", "2"],
            "element": [1, 2],
            "name": ["API", "API Invalid"],
            "team": ["A", "B"],
            "opponent_team": [3, 4],
            "was_home": ["false", "true"],
            "position": ["MID", "FWD"],
            "total_points": ["7", "bad-points"],
            "minutes": ["90", "45"],
            "starts": ["1", "0"],
            "bonus": ["2", "0"],
            "bps": ["25", "bad-bps"],
            "selected": ["1000", "2000"],
            "transfers_in": ["10", "20"],
            "transfers_out": ["5", "6"],
            "value": ["75", "81"],
            "creativity": ["0.0", "not-a-number"],
            "influence": ["1.2", "2.3"],
            "threat": ["3.4", "4.5"],
            "ict_index": ["4.6", "5.7"],
            "expected_goals": ["0.5", "0.1"],
            "expected_assists": ["0.2", "0.3"],
            "expected_goal_involvements": ["0.7", "0.4"],
            "expected_goals_conceded": ["1.1", "0.9"],
        }
    )


def test_combiner_drops_vaastav_boundary_season_and_uses_fpl_api() -> None:
    combined, diagnostics = combine_merged_gw_sources(
        vaastav_frame(),
        {"2025-26": fpl_api_frame()},
    )

    rows_2025 = combined.loc[combined["season"].eq("2025-26")]

    assert len(rows_2025) == 1
    assert rows_2025.iloc[0]["name"] == "API"
    assert rows_2025.iloc[0]["total_points"] == 7
    assert diagnostics.dropped_vaastav_rows == 1
    assert diagnostics.dropped_vaastav_seasons == ("2025-26",)


def test_combiner_does_not_mix_sources_within_same_season() -> None:
    _, diagnostics = combine_merged_gw_sources(
        vaastav_frame(),
        {"2025-26": fpl_api_frame()},
    )

    included = diagnostics.seasons_by_source
    season_sources = included.groupby("season")["source"].nunique()

    assert season_sources.max() == 1
    assert set(included["season"]) == {"2024-25", "2025-26"}


def test_combiner_skips_pre_boundary_fpl_api_seasons() -> None:
    combined, diagnostics = combine_merged_gw_sources(
        vaastav_frame(),
        {"2024-25": fpl_api_frame("2024-25"), "2025-26": fpl_api_frame()},
    )

    assert diagnostics.skipped_fpl_api_seasons == ("2024-25",)
    assert len(combined.loc[combined["season"].eq("2024-25")]) == 1
    assert combined.loc[combined["season"].eq("2024-25")].iloc[0]["name"] == "Historical"


def test_required_column_coverage_reports_missing_columns() -> None:
    coverage = required_column_coverage(pd.DataFrame({"season": ["2025-26"], "gw": [1]}))

    season_row = coverage.loc[coverage["column"].eq("season")].iloc[0]
    element_row = coverage.loc[coverage["column"].eq("element")].iloc[0]

    assert bool(season_row["present"]) is True
    assert season_row["coverage_pct"] == 100.0
    assert bool(element_row["present"]) is False
    assert element_row["coverage_pct"] == 0.0


def test_combine_from_paths_writes_output_and_report() -> None:
    scratch = clean_scratch("combine_merged_gw")
    try:
        vaastav_path = scratch / "all_merged_gw.parquet"
        fpl_dir = scratch / "fpl_api" / "2025-26"
        output_path = scratch / "combined.parquet"
        report_path = scratch / "report.md"
        fpl_dir.mkdir(parents=True)
        vaastav_frame().to_parquet(vaastav_path, index=False)
        fpl_api_frame().to_parquet(fpl_dir / "merged_gw_api.parquet", index=False)

        combined, diagnostics = combine_from_paths(
            vaastav_input=vaastav_path,
            fpl_api_root=scratch / "fpl_api",
            output_path=output_path,
            report_path=report_path,
        )

        assert output_path.exists()
        assert report_path.exists()
        assert len(pd.read_parquet(output_path)) == len(combined)
        assert not diagnostics.required_column_coverage.empty
        assert "Required Column Coverage" in report_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_combiner_normalizes_fpl_api_numeric_strings_and_writes_parquet() -> None:
    scratch = clean_scratch("combine_merged_gw_numeric_strings")
    try:
        output_path = scratch / "combined.parquet"
        combined, diagnostics = combine_merged_gw_sources(
            vaastav_frame().assign(creativity=[1.0, 99.0]),
            {"2025-26": fpl_api_frame_with_numeric_strings()},
        )

        write_combined_dataset(combined, output_path)
        reread = pd.read_parquet(output_path)
        api_rows = reread.loc[reread["season"].eq("2025-26")].sort_values("element")
        creativity_coercion = diagnostics.numeric_coercions.loc[
            diagnostics.numeric_coercions["column"].eq("creativity")
        ].iloc[0]

        assert len(api_rows) == 2
        assert api_rows.iloc[0]["creativity"] == 0.0
        assert pd.isna(api_rows.iloc[1]["creativity"])
        assert int(creativity_coercion["values_coerced_to_na"]) == 1
        assert str(reread["creativity"].dtype).startswith("float")
        assert str(reread["was_home"].dtype) == "boolean"
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_combiner_diagnostics_include_final_key_dtypes() -> None:
    _, diagnostics = combine_merged_gw_sources(
        vaastav_frame(),
        {"2025-26": fpl_api_frame_with_numeric_strings()},
    )

    dtype_lookup = diagnostics.final_key_dtypes.set_index("column")["dtype"].to_dict()

    assert dtype_lookup["season"] == "string"
    assert dtype_lookup["name"] == "string"
    assert dtype_lookup["team"] == "string"
    assert dtype_lookup["position"] == "string"
    assert dtype_lookup["was_home"] == "boolean"
    assert "float" in dtype_lookup["creativity"]
