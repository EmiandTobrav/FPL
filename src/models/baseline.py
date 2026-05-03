"""Baseline models for Fantasy Premier League point prediction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd


DEFAULT_OUTPUT_PATH = Path("data/predictions/baselines.csv")
PLAYER_ID_COLUMNS = ("element", "id", "name")
POINTS_COLUMN = "total_points"


class BaselineModel(Protocol):
    """Common interface for baseline predictors."""

    name: str

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        """Return one prediction per row in frame."""


class BaselinePredictionError(ValueError):
    """Raised when a baseline cannot produce predictions from the input data."""


def player_key_column(frame: pd.DataFrame) -> str:
    for column in PLAYER_ID_COLUMNS:
        if column in frame.columns:
            return column
    raise BaselinePredictionError("Expected one of element, id, or name to identify players.")


def require_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise BaselinePredictionError(f"Missing required columns for baseline predictions: {missing}")


@dataclass(frozen=True)
class ColumnBaseline:
    """Predict directly from an existing feature column."""

    name: str
    column: str

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        require_columns(frame, [self.column])
        return frame[self.column].rename(self.name)


@dataclass(frozen=True)
class MinutesAdjustedRollingMeanBaseline:
    """Scale recent points by recent minutes relative to a full-match baseline."""

    name: str = "minutes_adjusted_rolling_mean"
    points_column: str = "points_mean_last_5"
    minutes_column: str = "minutes_mean_last_5"

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        require_columns(frame, [self.points_column, self.minutes_column])
        minutes_factor = frame[self.minutes_column].fillna(0).clip(lower=0) / 90
        return (frame[self.points_column] * minutes_factor).rename(self.name)


BASELINES: tuple[BaselineModel, ...] = (
    ColumnBaseline("previous_gameweek_points", "points_last_1"),
    ColumnBaseline("rolling_3_gameweek_mean", "points_mean_last_3"),
    ColumnBaseline("rolling_5_gameweek_mean", "points_mean_last_5"),
    MinutesAdjustedRollingMeanBaseline(),
)


def predict_baselines(
    frame: pd.DataFrame,
    *,
    models: tuple[BaselineModel, ...] = BASELINES,
) -> pd.DataFrame:
    """Return baseline predictions with row identifiers when available."""
    predictions = pd.DataFrame(index=frame.index)

    identifier_columns = [
        column
        for column in ("element", "id", "name", "season", "gw", "position", "next_gw_points")
        if column in frame.columns
    ]
    for column in identifier_columns:
        predictions[column] = frame[column]

    for model in models:
        predictions[model.name] = model.predict(frame)

    return predictions


def save_baseline_predictions(
    frame: pd.DataFrame,
    *,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    models: tuple[BaselineModel, ...] = BASELINES,
) -> pd.DataFrame:
    """Generate baseline predictions and save them to CSV."""
    predictions = predict_baselines(frame, models=models)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output_path, index=False)
    return predictions
