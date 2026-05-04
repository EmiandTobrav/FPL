from pathlib import Path
import shutil

import pandas as pd
from evaluation.predict_week import (
    OUTPUT_COLUMNS,
    build_prediction_features,
    generate_weekly_predictions,
    predict_from_files,
)


def clean_scratch(name: str) -> Path:
    path = Path("tests") / f".tmp_{name}"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


def historical_rows() -> pd.DataFrame:
    rows = []
    for gw, points, minutes in [(1, 10, 90), (2, 20, 90), (3, 30, 45)]:
        rows.append(
            {
                "season": "2025-26",
                "gw": gw,
                "element": 1,
                "name": "A",
                "team": "ARS",
                "position": "MID",
                "value": 75,
                "total_points": points,
                "minutes": minutes,
                "starts": 1,
                "bonus": gw,
                "bps": gw * 10,
                "next_gw_points": points + 1,
            }
        )
    for gw, points in [(1, 2), (2, 4), (3, 6)]:
        rows.append(
            {
                "season": "2025-26",
                "gw": gw,
                "element": 2,
                "name": "B",
                "team": "CHE",
                "position": "FWD",
                "value": 65,
                "total_points": points,
                "minutes": 90,
                "starts": 1,
                "bonus": 0,
                "bps": 5,
                "next_gw_points": points + 1,
            }
        )
    return pd.DataFrame(rows)


def prediction_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "season": ["2025-26", "2025-26", "2025-26"],
            "gw": [4, 4, 4],
            "element": [1, 1, 2],
            "name": ["A", "A", "B"],
            "team": ["ARS", "ARS", "CHE"],
            "position": ["MID", "MID", "FWD"],
            "value": [75, 75, 65],
            "fixture": [40, 41, 42],
            "total_points": [pd.NA, pd.NA, pd.NA],
            "minutes": [pd.NA, pd.NA, pd.NA],
            "starts": [pd.NA, pd.NA, pd.NA],
            "bonus": [pd.NA, pd.NA, pd.NA],
            "bps": [pd.NA, pd.NA, pd.NA],
            "next_gw_points": [pd.NA, pd.NA, pd.NA],
        }
    )


def test_prediction_rows_do_not_need_actual_outcomes() -> None:
    output, summary = generate_weekly_predictions(
        historical=historical_rows(),
        prediction_rows=prediction_rows(),
        prediction_rows_path=Path("prediction_rows_gw4.parquet"),
        output_path=Path("tests/.tmp_unused_predictions.csv"),
    )
    try:
        assert summary.fixture_rows == 3
        assert output["expected_points_primary"].notna().all()
    finally:
        Path("tests/.tmp_unused_predictions.csv").unlink(missing_ok=True)


def test_rolling_features_for_prediction_rows_use_prior_completed_rows_only() -> None:
    features = build_prediction_features(historical_rows(), prediction_rows())
    player = features.loc[features["element"].eq(1)].iloc[0]

    assert player["points_mean_last_3"] == 20
    assert player["points_mean_last_5"] == 20
    assert player["minutes_mean_last_5"] == 75
    assert pd.isna(player["next_gw_points"])


def test_double_gameweek_fixture_predictions_aggregate_by_sum() -> None:
    output, _ = generate_weekly_predictions(
        historical=historical_rows(),
        prediction_rows=prediction_rows(),
        prediction_rows_path=Path("prediction_rows_gw4.parquet"),
        output_path=Path("tests/.tmp_unused_predictions.csv"),
    )
    try:
        fixture = output.loc[(output["prediction_level"] == "fixture") & (output["element"] == 1)]
        aggregated = output.loc[
            (output["prediction_level"] == "player_gw") & (output["element"] == 1)
        ].iloc[0]

        assert len(fixture) == 2
        assert aggregated["fixture_count"] == 2
        assert aggregated["expected_points_primary"] == fixture["expected_points_primary"].sum()
    finally:
        Path("tests/.tmp_unused_predictions.csv").unlink(missing_ok=True)


def test_weekly_prediction_output_columns_exist() -> None:
    output, _ = generate_weekly_predictions(
        historical=historical_rows(),
        prediction_rows=prediction_rows(),
        prediction_rows_path=Path("prediction_rows_gw4.parquet"),
        output_path=Path("tests/.tmp_unused_predictions.csv"),
    )
    try:
        assert set(OUTPUT_COLUMNS).issubset(output.columns)
        assert {
            "expected_points_primary",
            "rolling_3_gameweek_mean_prediction",
            "rolling_5_gameweek_mean_prediction",
        }.issubset(output.columns)
    finally:
        Path("tests/.tmp_unused_predictions.csv").unlink(missing_ok=True)


def test_no_target_leakage_from_prediction_rows() -> None:
    base = prediction_rows()
    changed = base.copy()
    changed["next_gw_points"] = 999
    changed["total_points"] = 999
    base_features = build_prediction_features(historical_rows(), base)
    changed_features = build_prediction_features(historical_rows(), changed)

    columns = ["points_mean_last_3", "points_mean_last_5", "minutes_mean_last_5"]
    pd.testing.assert_frame_equal(base_features[columns], changed_features[columns])


def test_predict_from_files_auto_detects_prediction_rows_and_writes_report() -> None:
    scratch = clean_scratch("predict_week")
    try:
        historical_path = scratch / "modeling_dataset.parquet"
        prediction_dir = scratch / "fpl_api" / "2025-26"
        output_path = scratch / "latest_predictions.csv"
        report_path = scratch / "weekly_report.md"
        prediction_dir.mkdir(parents=True)
        historical_rows().to_parquet(historical_path, index=False)
        prediction_rows().to_parquet(prediction_dir / "prediction_rows_gw4.parquet", index=False)

        output, summary = predict_from_files(
            historical_path=historical_path,
            fpl_api_root=scratch / "fpl_api",
            output_path=output_path,
            report_path=report_path,
        )

        assert summary.season == "2025-26"
        assert summary.gw == 4
        assert output_path.exists()
        assert report_path.exists()
        assert len(pd.read_csv(output_path)) == len(output)
        assert "minutes_adjusted_rolling_mean" in report_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
