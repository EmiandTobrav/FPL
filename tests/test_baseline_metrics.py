from pathlib import Path
import shutil

import pandas as pd
import pytest

from evaluation.metrics import (
    average_actual_points_in_predicted_top_k,
    mae,
    rmse,
    spearman_rank_correlation,
    top_k_precision,
)
from models.baseline import (
    BaselinePredictionError,
    PositionAverageBaseline,
    predict_baselines,
    save_baseline_predictions,
)


def baseline_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "element": [1, 1, 1, 2],
            "season": ["2023-24", "2023-24", "2023-24", "2023-24"],
            "gw": [1, 2, 3, 1],
            "position": ["MID", "MID", "MID", "FWD"],
            "total_points": [10, 20, 30, 5],
            "points_last_1": [pd.NA, 10, 20, pd.NA],
            "points_mean_last_3": [pd.NA, 10, 15, pd.NA],
            "points_mean_last_5": [pd.NA, 10, 15, pd.NA],
            "minutes_mean_last_5": [pd.NA, 90, 45, pd.NA],
            "next_gw_points": [20, 30, pd.NA, pd.NA],
        }
    )


def test_predict_baselines_common_interface() -> None:
    predictions = predict_baselines(baseline_frame())

    expected_columns = {
        "previous_gameweek_points",
        "rolling_3_gameweek_mean",
        "rolling_5_gameweek_mean",
        "position_average",
        "minutes_adjusted_rolling_mean",
    }
    assert expected_columns.issubset(predictions.columns)
    assert predictions.loc[1, "previous_gameweek_points"] == 10
    assert predictions.loc[2, "rolling_3_gameweek_mean"] == 15
    assert predictions.loc[2, "minutes_adjusted_rolling_mean"] == 7.5


def test_position_average_uses_prior_position_rows_only() -> None:
    predictions = PositionAverageBaseline().predict(baseline_frame())

    assert pd.isna(predictions.iloc[0])
    assert predictions.iloc[1] == 10
    assert predictions.iloc[2] == 15
    assert pd.isna(predictions.iloc[3])


def test_save_baseline_predictions_writes_csv() -> None:
    scratch = Path("tests/.tmp_baseline_predictions")
    shutil.rmtree(scratch, ignore_errors=True)
    output_path = scratch / "baselines.csv"
    try:
        predictions = save_baseline_predictions(baseline_frame(), output_path=output_path)

        assert output_path.exists()
        saved = pd.read_csv(output_path)
        assert list(saved.columns) == list(predictions.columns)
        assert len(saved) == len(predictions)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_baseline_requires_needed_columns() -> None:
    with pytest.raises(BaselinePredictionError, match="Missing required columns"):
        predict_baselines(pd.DataFrame({"points_last_1": [1]}))


def test_metrics() -> None:
    actual = pd.Series([1.0, 2.0, 4.0])
    predicted = pd.Series([1.0, 3.0, 2.0])

    assert mae(actual, predicted) == 1.0
    assert rmse(actual, predicted) == pytest.approx((5 / 3) ** 0.5)
    assert spearman_rank_correlation(actual, predicted) == pytest.approx(0.5)


def test_ranking_metrics() -> None:
    actual = pd.Series([10.0, 8.0, 2.0, 1.0], index=[1, 2, 3, 4])
    predicted = pd.Series([0.4, 0.1, 0.3, 0.2], index=[1, 2, 3, 4])

    assert top_k_precision(actual, predicted, 2) == 0.5
    assert average_actual_points_in_predicted_top_k(actual, predicted, 2) == 6.0
