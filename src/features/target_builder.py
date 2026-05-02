"""Target generation for FPL gameweek point prediction."""

from __future__ import annotations

import pandas as pd

from features.rolling_features import POINTS_COLUMN, FeatureBuildError, player_key_column


def _future_sum_with_full_horizon(points: pd.Series, horizon: int) -> pd.Series:
    future_columns = [points.shift(-offset) for offset in range(1, horizon + 1)]
    future = pd.concat(future_columns, axis=1)
    return future.sum(axis=1).where(future.notna().all(axis=1))


def build_targets(frame: pd.DataFrame, *, target_horizon: int = 3) -> pd.DataFrame:
    """Add next-gameweek and next-three-gameweek point targets.

    Targets are calculated within each player-season group. The horizon target
    is only populated when all future rows in the horizon are available.
    """
    if target_horizon < 1:
        raise FeatureBuildError("target_horizon must be at least 1.")

    missing = [column for column in ("season", "gw", POINTS_COLUMN) if column not in frame.columns]
    if missing:
        raise FeatureBuildError(f"Missing required columns for target building: {missing}")

    player_col = player_key_column(frame)
    group_columns = [player_col, "season"]
    data = frame.sort_values(group_columns + ["gw"]).reset_index(drop=True).copy()
    grouped_points = data.groupby(group_columns, sort=False)[POINTS_COLUMN]

    data["next_gw_points"] = grouped_points.shift(-1)
    data[f"next_{target_horizon}_gw_points"] = grouped_points.transform(
        lambda points: _future_sum_with_full_horizon(points, target_horizon)
    )

    return data
