"""Rolling, leakage-safe feature generation for FPL gameweek data."""

from __future__ import annotations

from typing import Iterable

import pandas as pd


PLAYER_ID_COLUMNS = ("element", "id", "name")
POINTS_COLUMN = "total_points"
REQUIRED_COLUMNS = ("season", "gw", POINTS_COLUMN, "minutes", "bonus", "bps")
CANDIDATE_ROLLING_SOURCES = (
    "goals_scored",
    "assists",
    "clean_sheets",
    "goals_conceded",
    "influence",
    "creativity",
    "threat",
    "ict_index",
    "expected_goals",
    "expected_assists",
    "expected_goal_involvements",
    "expected_goals_conceded",
)
CANDIDATE_ROLLING_WINDOWS = (3, 5)
CANDIDATE_LAG_SOURCES = (
    "selected",
    "transfers_in",
    "transfers_out",
    "transfers_balance",
)


class FeatureBuildError(ValueError):
    """Raised when rolling features cannot be built from the input data."""


def player_key_column(frame: pd.DataFrame) -> str:
    """Choose the most stable available player identifier column."""
    for column in PLAYER_ID_COLUMNS:
        if column in frame.columns:
            return column
    raise FeatureBuildError("Expected one of element, id, or name to identify players.")


def validate_columns(frame: pd.DataFrame, required: Iterable[str] = REQUIRED_COLUMNS) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise FeatureBuildError(f"Missing required columns for feature building: {missing}")


def _previous_rolling(
    frame: pd.DataFrame,
    *,
    group_columns: list[str],
    source_column: str,
    window: int,
    aggregation: str,
) -> pd.Series:
    shifted = frame.groupby(group_columns, sort=False)[source_column].shift(1)
    grouped = shifted.groupby([frame[column] for column in group_columns], sort=False)
    rolling = grouped.rolling(window=window, min_periods=1)

    if aggregation == "mean":
        result = rolling.mean()
    elif aggregation == "sum":
        result = rolling.sum()
    else:
        raise FeatureBuildError(f"Unsupported rolling aggregation: {aggregation}")

    return result.reset_index(level=group_columns, drop=True).sort_index()


def build_rolling_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create one player-gameweek row with previous-gameweek rolling features.

    The input is sorted by player, season, and gameweek. Every rolling feature is
    calculated after shifting the source column by one gameweek within each
    player-season group, so gameweek t never uses gameweek t or future data.
    """
    validate_columns(frame)
    player_col = player_key_column(frame)
    group_columns = [player_col, "season"]

    data = frame.sort_values(group_columns + ["gw"]).reset_index(drop=True).copy()

    data["points_last_1"] = data.groupby(group_columns, sort=False)[POINTS_COLUMN].shift(1)
    data["points_mean_last_3"] = _previous_rolling(
        data,
        group_columns=group_columns,
        source_column=POINTS_COLUMN,
        window=3,
        aggregation="mean",
    )
    data["points_mean_last_5"] = _previous_rolling(
        data,
        group_columns=group_columns,
        source_column=POINTS_COLUMN,
        window=5,
        aggregation="mean",
    )
    data["minutes_mean_last_3"] = _previous_rolling(
        data,
        group_columns=group_columns,
        source_column="minutes",
        window=3,
        aggregation="mean",
    )
    data["minutes_mean_last_5"] = _previous_rolling(
        data,
        group_columns=group_columns,
        source_column="minutes",
        window=5,
        aggregation="mean",
    )

    if "starts" in data.columns:
        starts_source = "starts"
    else:
        starts_source = "_starts_from_minutes"
        data[starts_source] = (data["minutes"] > 0).astype(int)

    data["starts_last_5"] = _previous_rolling(
        data,
        group_columns=group_columns,
        source_column=starts_source,
        window=5,
        aggregation="sum",
    )
    if starts_source.startswith("_"):
        data = data.drop(columns=[starts_source])

    for optional_column, feature_name in (("xG", "xG_last_5"), ("xA", "xA_last_5")):
        if optional_column in data.columns:
            data[feature_name] = _previous_rolling(
                data,
                group_columns=group_columns,
                source_column=optional_column,
                window=5,
                aggregation="sum",
            )

    data["bonus_last_5"] = _previous_rolling(
        data,
        group_columns=group_columns,
        source_column="bonus",
        window=5,
        aggregation="sum",
    )
    data["bps_last_5"] = _previous_rolling(
        data,
        group_columns=group_columns,
        source_column="bps",
        window=5,
        aggregation="sum",
    )

    for source_column in CANDIDATE_ROLLING_SOURCES:
        if source_column not in data.columns:
            continue
        for window in CANDIDATE_ROLLING_WINDOWS:
            data[f"{source_column}_mean_last_{window}"] = _previous_rolling(
                data,
                group_columns=group_columns,
                source_column=source_column,
                window=window,
                aggregation="mean",
            )

    for source_column in CANDIDATE_LAG_SOURCES:
        if source_column not in data.columns:
            continue
        data[f"{source_column}_lag_1"] = data.groupby(group_columns, sort=False)[
            source_column
        ].shift(1)

    return data


def expected_candidate_feature_columns() -> list[str]:
    """Return candidate feature names that may be produced from optional sources."""
    rolling = [
        f"{source_column}_mean_last_{window}"
        for source_column in CANDIDATE_ROLLING_SOURCES
        for window in CANDIDATE_ROLLING_WINDOWS
    ]
    lags = [f"{source_column}_lag_1" for source_column in CANDIDATE_LAG_SOURCES]
    return [*rolling, *lags, "was_home"]


def skipped_candidate_sources(frame: pd.DataFrame) -> dict[str, str]:
    """Return optional candidate sources unavailable in this dataset."""
    skipped: dict[str, str] = {}
    for source_column in CANDIDATE_ROLLING_SOURCES:
        if source_column not in frame.columns:
            skipped[source_column] = "source column missing"
    for source_column in CANDIDATE_LAG_SOURCES:
        if source_column not in frame.columns:
            skipped[source_column] = "source column missing"
    if "was_home" not in frame.columns:
        skipped["was_home"] = "source column missing"
    return skipped
