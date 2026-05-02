from pathlib import Path
import shutil

import pandas as pd
import pytest

from data.download_vaastav import (
    VaastavDownloadError,
    add_required_columns,
    combine_season_files,
    validate_no_introduced_duplicates,
)


def test_add_required_columns_includes_season_and_gw() -> None:
    frame = pd.DataFrame({"element": [1], "GW": [3], "total_points": [8]})

    result = add_required_columns(frame, "2023-24")

    assert "season" in result.columns
    assert "gw" in result.columns
    assert result.loc[0, "season"] == "2023-24"
    assert result.loc[0, "gw"] == 3


def test_combine_season_files_has_required_columns_and_writes_parquet() -> None:
    scratch = Path("tests/.tmp_download_vaastav")
    shutil.rmtree(scratch, ignore_errors=True)
    raw_root = scratch / "raw" / "vaastav"
    output_path = scratch / "interim" / "all_merged_gw.parquet"
    season_dir = raw_root / "2023-24"
    season_dir.mkdir(parents=True)
    try:
        pd.DataFrame(
            {
                "element": [1, 2],
                "GW": [1, 1],
                "total_points": [5, 2],
            }
        ).to_csv(season_dir / "merged_gw.csv", index=False)

        combined = combine_season_files(["2023-24"], raw_root=raw_root, output_path=output_path)

        assert "season" in combined.columns
        assert "gw" in combined.columns
        assert output_path.exists()
        pd.testing.assert_frame_equal(pd.read_parquet(output_path), combined)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_duplicate_validation_allows_duplicates_present_in_source() -> None:
    source = add_required_columns(
        pd.DataFrame({"element": [1, 1], "GW": [1, 1], "total_points": [5, 5]}),
        "2023-24",
    )
    combined = source.copy()

    validate_no_introduced_duplicates([source], combined)


def test_duplicate_validation_rejects_duplicates_introduced_by_combining() -> None:
    source = add_required_columns(
        pd.DataFrame({"element": [1], "GW": [1], "total_points": [5]}),
        "2023-24",
    )
    combined = pd.concat([source, source], ignore_index=True)

    with pytest.raises(VaastavDownloadError, match="duplicates"):
        validate_no_introduced_duplicates([source], combined)
