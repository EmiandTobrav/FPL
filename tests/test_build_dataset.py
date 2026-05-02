from pathlib import Path
import shutil

import pandas as pd

from data.build_dataset import build_modeling_dataset, dataset_summary, read_dataset, write_dataset


def source_frame() -> pd.DataFrame:
    rows = []
    for season, offset in [("2022-23", 0), ("2023-24", 100)]:
        for gw in [1, 2, 3, 4]:
            rows.append(
                {
                    "element": 1,
                    "season": season,
                    "gw": gw,
                    "total_points": offset + gw * 10,
                    "minutes": 90 - gw,
                    "starts": 1,
                    "bonus": gw,
                    "bps": gw * 5,
                }
            )
    return pd.DataFrame(rows)


def test_build_dataset_creates_output_parquet() -> None:
    scratch = Path("tests/.tmp_build_dataset")
    shutil.rmtree(scratch, ignore_errors=True)
    output_path = scratch / "modeling_dataset.parquet"
    try:
        result = build_modeling_dataset(source_frame())
        write_dataset(result, output_path)
        loaded = read_dataset(output_path)

        assert output_path.exists()
        assert len(loaded) == len(result)
        assert "Rows: 8" in dataset_summary(loaded, target_horizon=3)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_build_dataset_contains_features_and_targets() -> None:
    result = build_modeling_dataset(source_frame())

    assert "points_last_1" in result.columns
    assert "points_mean_last_3" in result.columns
    assert "minutes_mean_last_5" in result.columns
    assert "next_gw_points" in result.columns
    assert "next_3_gw_points" in result.columns


def test_final_gw_each_season_has_missing_next_gw_points() -> None:
    result = build_modeling_dataset(source_frame())
    final_gameweeks = result.loc[result["gw"] == 4]

    assert final_gameweeks["next_gw_points"].isna().all()


def test_targets_do_not_cross_season_boundaries() -> None:
    result = build_modeling_dataset(source_frame())
    last_old_season = result.loc[(result["season"] == "2022-23") & (result["gw"] == 4)].iloc[0]
    first_new_season = result.loc[(result["season"] == "2023-24") & (result["gw"] == 1)].iloc[0]

    assert pd.isna(last_old_season["next_gw_points"])
    assert pd.isna(first_new_season["points_last_1"])


def test_features_for_gw_t_do_not_use_gw_t_data() -> None:
    base = source_frame()
    changed = base.copy()
    changed.loc[(changed["season"] == "2023-24") & (changed["gw"] == 3), "total_points"] = 999
    changed.loc[(changed["season"] == "2023-24") & (changed["gw"] == 3), "minutes"] = 999

    base_row = build_modeling_dataset(base).loc[
        lambda data: (data["season"] == "2023-24") & (data["gw"] == 3)
    ].iloc[0]
    changed_row = build_modeling_dataset(changed).loc[
        lambda data: (data["season"] == "2023-24") & (data["gw"] == 3)
    ].iloc[0]

    assert base_row["points_last_1"] == changed_row["points_last_1"]
    assert base_row["points_mean_last_3"] == changed_row["points_mean_last_3"]
    assert base_row["minutes_mean_last_3"] == changed_row["minutes_mean_last_3"]
