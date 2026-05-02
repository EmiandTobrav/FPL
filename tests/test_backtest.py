from pathlib import Path
import shutil
import subprocess
import sys

import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor

from evaluation.backtest import (
    DEFAULT_SUPPORTED_RESULTS_PATH,
    DEFAULT_SUPPORTED_SUMMARY_PATH,
    SklearnModelSpec,
    add_baseline_prediction_features,
    add_position_interactions,
    add_residual_target,
    final_residual_prediction,
    minutes_adjusted_baseline_predictions,
    normalize_position_column,
    position_diagnostics,
    run_position_model_backtest,
    run_backtest,
    season_filtered_frame,
    write_position_markdown_summary,
    write_position_results,
    write_supported_season_filter_report,
    write_markdown_summary,
    write_results,
)


class RecordingRegressor(BaseEstimator, RegressorMixin):
    fit_targets: list[list[float]] = []

    def fit(self, x: pd.DataFrame, y: pd.Series) -> "RecordingRegressor":
        self.fit_targets.append(list(y))
        self.prediction_ = float(pd.Series(y).mean())
        return self

    def predict(self, x: pd.DataFrame) -> list[float]:
        return [self.prediction_] * len(x)


def modeling_frame() -> pd.DataFrame:
    rows = []
    for season, offset in [("2022-23", 0), ("2023-24", 10)]:
        for element, position in [(1, "MID"), (2, "FWD")]:
            for gw in [1, 2, 3, 4]:
                points = offset + element + gw
                rows.append(
                    {
                        "element": element,
                        "season": season,
                        "gw": gw,
                        "position": position,
                        "total_points": points,
                        "minutes": 90 if gw % 2 == 0 else 30,
                        "points_last_1": points - 1 if gw > 1 else pd.NA,
                        "points_mean_last_3": points - 1 if gw > 1 else pd.NA,
                        "points_mean_last_5": points - 1 if gw > 1 else pd.NA,
                        "minutes_mean_last_5": 90,
                        "next_gw_points": points + 1 if gw < 4 else pd.NA,
                    }
                )
    return pd.DataFrame(rows)


def three_season_modeling_frame() -> pd.DataFrame:
    rows = []
    for season, offset in [("2020-21", 0), ("2021-22", 100), ("2022-23", 200)]:
        for element, position in [(1, "MID"), (2, "FWD")]:
            for gw in [1, 2, 3, 4]:
                points = offset + element + gw
                rows.append(
                    {
                        "element": element,
                        "season": season,
                        "gw": gw,
                        "position": position,
                        "total_points": points,
                        "minutes": 90,
                        "points_last_1": points - 1 if gw > 1 else pd.NA,
                        "points_mean_last_3": points - 1 if gw > 1 else pd.NA,
                        "points_mean_last_5": points - 1 if gw > 1 else pd.NA,
                        "minutes_mean_last_5": 90,
                        "team_elo_pre_gw": 1500.0,
                        "opponent_elo_pre_gw": 1500.0,
                        "elo_difference": 0.0,
                        "home_adjusted_elo_difference": 50.0,
                        "next_gw_points": points + 1 if gw < 4 else pd.NA,
                    }
                )
    return pd.DataFrame(rows)


def test_run_backtest_uses_prior_seasons_for_validation() -> None:
    results = run_backtest(
        modeling_frame(),
        model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
        residual_specs=[],
    )

    assert set(results["validation_season"]) == {"2023-24"}
    assert "DummyMean" in set(results["model"])
    assert "two_stage_minutes_points" in set(results["model"])
    dummy_row = results.loc[results["model"] == "DummyMean"].iloc[0]
    assert dummy_row["n_train"] == 6
    assert dummy_row["n_validation"] == 6
    assert "top_10_precision" in results.columns
    assert "top_10_avg_actual_points" in results.columns
    assert "GK_top_10_precision" in results.columns
    assert "DEF_top_50_avg_actual_points" in results.columns


def test_write_backtest_reports() -> None:
    scratch = Path("tests/.tmp_backtest")
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        results = run_backtest(
            modeling_frame(),
            model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
            residual_specs=[],
        )
        results_path = scratch / "model_results.csv"
        summary_path = scratch / "model_comparison.md"

        write_results(results, results_path)
        write_markdown_summary(results, summary_path)

        assert results_path.exists()
        assert summary_path.exists()
        summary = summary_path.read_text(encoding="utf-8")
        assert "# Model Comparison" in summary
        assert "Two-Stage Versus Best Direct Model" in summary
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_backtest_module_has_command_line_help() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "evaluation.backtest", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "--input" in completed.stdout
    assert "--min-season" in completed.stdout


def test_min_season_filters_train_and_validation_data() -> None:
    results = run_backtest(
        three_season_modeling_frame(),
        model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
        residual_specs=[],
        min_season="2021-22",
    )

    assert set(results["validation_season"]) == {"2022-23"}
    dummy_row = results.loc[results["model"] == "DummyMean"].iloc[0]
    assert dummy_row["n_train"] == 6
    assert dummy_row["n_validation"] == 6
    assert results.attrs["diagnostics"]["season_filter"]["included_seasons"] == [
        "2021-22",
        "2022-23",
    ]
    assert results.attrs["diagnostics"]["season_filter"]["excluded_seasons"] == ["2020-21"]


def test_default_backtest_still_uses_full_available_dataset() -> None:
    results = run_backtest(
        three_season_modeling_frame(),
        model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
        residual_specs=[],
    )

    assert set(results["validation_season"]) == {"2021-22", "2022-23"}
    assert "season_filter" not in results.attrs["diagnostics"]


def test_min_season_does_not_leak_future_validation_seasons_into_training() -> None:
    data = three_season_modeling_frame()
    data.loc[data["season"] == "2022-23", "next_gw_points"] = 999
    RecordingRegressor.fit_targets = []

    run_backtest(
        data,
        model_specs=[SklearnModelSpec("RecordingRegressor", RecordingRegressor())],
        residual_specs=[],
        min_season="2021-22",
    )

    assert RecordingRegressor.fit_targets
    assert all(max(targets) < 999 for targets in RecordingRegressor.fit_targets if targets)


def test_filtered_reports_are_written_to_separate_files() -> None:
    scratch = Path("tests/.tmp_backtest")
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        data = three_season_modeling_frame()
        full_results = run_backtest(
            data,
            model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
            residual_specs=[],
        )
        filtered_results = run_backtest(
            data,
            model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
            residual_specs=[],
            min_season="2021-22",
        )
        filtered_path = scratch / DEFAULT_SUPPORTED_RESULTS_PATH.name
        filtered_summary_path = scratch / DEFAULT_SUPPORTED_SUMMARY_PATH.name
        report_path = scratch / "supported_season_filter_report.md"

        write_results(filtered_results, filtered_path)
        write_markdown_summary(filtered_results, filtered_summary_path)
        write_supported_season_filter_report(
            source=data,
            full_results=full_results,
            filtered_results=filtered_results,
            full_position_results=None,
            filtered_position_results=None,
            min_season="2021-22",
            path=report_path,
        )

        assert filtered_path.exists()
        assert filtered_summary_path.exists()
        assert report_path.exists()
        assert "Supported-Season Filter Report" in report_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_season_filtered_frame_keeps_only_supported_seasons() -> None:
    filtered = season_filtered_frame(three_season_modeling_frame(), "2021-22")

    assert sorted(filtered["season"].unique()) == ["2021-22", "2022-23"]


def test_residual_target_is_actual_minus_minutes_adjusted_baseline() -> None:
    frame = pd.DataFrame(
        {
            "next_gw_points": [8.0, 2.0],
            "points_mean_last_5": [6.0, 9.0],
            "minutes_mean_last_5": [45.0, 90.0],
        }
    )
    baseline = minutes_adjusted_baseline_predictions(frame)

    with_residual = add_residual_target(frame, baseline)

    assert list(baseline) == [3.0, 9.0]
    assert list(with_residual["__residual_target"]) == [5.0, -7.0]


def test_validation_baseline_predictions_do_not_use_other_validation_rows() -> None:
    validation = pd.DataFrame(
        {
            "next_gw_points": [8.0, 999.0],
            "points_mean_last_5": [6.0, 1000.0],
            "minutes_mean_last_5": [45.0, 90.0],
        }
    )

    first_row_prediction = minutes_adjusted_baseline_predictions(validation.iloc[[0]]).iloc[0]
    full_frame_prediction = minutes_adjusted_baseline_predictions(validation).iloc[0]

    assert first_row_prediction == full_frame_prediction == 3.0


def test_residual_final_prediction_adds_baseline_and_predicted_residual() -> None:
    baseline = pd.Series([3.0, 9.0], index=[10, 11])
    predicted_residual = pd.Series([5.0, -7.0], index=[10, 11])

    prediction = final_residual_prediction(baseline, predicted_residual)

    assert list(prediction) == [8.0, 2.0]


def test_baseline_prediction_features_are_row_local() -> None:
    frame = pd.DataFrame(
        {
            "next_gw_points": [8.0, 999.0],
            "points_last_1": [4.0, 1000.0],
            "points_mean_last_3": [5.0, 1000.0],
            "points_mean_last_5": [6.0, 1000.0],
            "minutes_mean_last_5": [45.0, 90.0],
        }
    )

    first_row_features = add_baseline_prediction_features(frame.iloc[[0]])
    full_frame_features = add_baseline_prediction_features(frame)

    feature_columns = [
        "pred_previous_gameweek_points",
        "pred_rolling_3_gameweek_mean",
        "pred_rolling_5_gameweek_mean",
        "pred_minutes_adjusted_rolling_mean",
    ]
    pd.testing.assert_series_equal(
        first_row_features.iloc[0][feature_columns],
        full_frame_features.iloc[0][feature_columns],
        check_names=False,
    )
    assert list(full_frame_features.loc[0, feature_columns]) == [4.0, 5.0, 6.0, 3.0]


def test_position_normalization_maps_known_labels_and_excludes_unknowns() -> None:
    frame = pd.DataFrame(
        {
            "season": ["2023-24", "2023-24", "2023-24", "2023-24", "2023-24"],
            "gw": [1, 1, 1, 1, 1],
            "position": ["GKP", "GK", "DEF", "MID", "AM"],
            "next_gw_points": [1, 2, 3, 4, 5],
        }
    )

    normalized = normalize_position_column(frame)
    diagnostics = position_diagnostics(frame)

    assert list(normalized["position"][:4]) == ["GK", "GK", "DEF", "MID"]
    assert pd.isna(normalized.loc[4, "position"])
    assert diagnostics["unknown_positions"] == {"AM": 1}


def test_write_results_overwrites_stale_model_rows() -> None:
    scratch = Path("tests/.tmp_backtest")
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        results_path = scratch / "model_results.csv"
        stale = pd.DataFrame(
            {
                "validation_season": ["2023-24"],
                "model": ["stale_model"],
                "mae": [99.0],
            }
        )
        fresh = pd.DataFrame(
            {
                "validation_season": ["2023-24"],
                "model": ["fresh_model"],
                "mae": [1.0],
            }
        )

        write_results(stale, results_path)
        write_results(fresh, results_path)

        saved = pd.read_csv(results_path)
        assert list(saved["model"]) == ["fresh_model"]
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_position_model_backtest_does_not_fit_on_validation_targets() -> None:
    data = modeling_frame()
    data.loc[data["season"] == "2023-24", "next_gw_points"] = 999
    RecordingRegressor.fit_targets = []

    results = run_position_model_backtest(
        data,
        estimator=RecordingRegressor(),
        min_position_train_rows=1,
    )

    assert {"global_model", "position_wise_models", "global_plus_position_interactions"}.issubset(
        set(results["strategy"])
    )
    assert RecordingRegressor.fit_targets
    assert all(max(targets) < 999 for targets in RecordingRegressor.fit_targets if targets)


def test_position_interactions_are_based_on_training_positions_only() -> None:
    train = modeling_frame().loc[lambda frame: frame["season"] == "2022-23"].copy()
    validation = pd.DataFrame(
        {
            "position": ["GK"],
            "points_last_1": [10],
            "points_mean_last_3": [10],
            "points_mean_last_5": [10],
            "minutes_mean_last_5": [90],
        }
    )
    columns = ["position", "points_last_1", "points_mean_last_3"]
    train_positions = sorted(train["position"].dropna().astype(str).unique())

    _, train_columns = add_position_interactions(train, columns, positions=train_positions)
    validation_with_interactions, validation_columns = add_position_interactions(
        validation,
        columns,
        positions=train_positions,
    )

    assert train_columns == validation_columns
    assert "points_last_1__position_GK" not in validation_columns
    assert validation_with_interactions.filter(like="__position_").eq(0).all().all()


def test_position_wise_models_fall_back_to_global_model_when_training_rows_are_low() -> None:
    results = run_position_model_backtest(
        modeling_frame(),
        estimator=DummyRegressor(strategy="mean"),
        min_position_train_rows=999,
    )

    metric_columns = [
        "mae",
        "rmse",
        "spearman",
        "top_10_precision",
        "top_20_precision",
        "top_50_precision",
    ]
    global_rows = results.loc[results["strategy"] == "global_model"].set_index(
        ["validation_season", "position"]
    )
    fallback_rows = results.loc[results["strategy"] == "position_wise_models"].set_index(
        ["validation_season", "position"]
    )

    pd.testing.assert_frame_equal(
        global_rows[metric_columns].sort_index(),
        fallback_rows[metric_columns].sort_index(),
    )


def test_write_position_model_reports() -> None:
    scratch = Path("tests/.tmp_backtest")
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        results = run_position_model_backtest(
            modeling_frame(),
            estimator=DummyRegressor(strategy="mean"),
            min_position_train_rows=1,
        )
        results_path = scratch / "position_model_comparison.csv"
        summary_path = scratch / "position_model_comparison.md"

        write_position_results(results, results_path)
        write_position_markdown_summary(results, summary_path)

        assert results_path.exists()
        assert summary_path.exists()
        summary = summary_path.read_text(encoding="utf-8")
        assert "Position Model Comparison" in summary
        assert "top_10_precision" in results.columns
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
