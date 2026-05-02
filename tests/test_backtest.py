from pathlib import Path
import shutil
import subprocess
import sys

import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor

from evaluation.backtest import (
    SklearnModelSpec,
    add_position_interactions,
    run_position_model_backtest,
    run_backtest,
    write_position_markdown_summary,
    write_position_results,
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


def test_run_backtest_uses_prior_seasons_for_validation() -> None:
    results = run_backtest(
        modeling_frame(),
        model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
    )

    assert set(results["validation_season"]) == {"2023-24"}
    assert "DummyMean" in set(results["model"])
    assert "two_stage_minutes_points" in set(results["model"])
    dummy_row = results.loc[results["model"] == "DummyMean"].iloc[0]
    assert dummy_row["n_train"] == 6
    assert dummy_row["n_validation"] == 6


def test_write_backtest_reports() -> None:
    scratch = Path("tests/.tmp_backtest")
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        results = run_backtest(
            modeling_frame(),
            model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
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
