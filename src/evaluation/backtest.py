"""Rolling-origin backtests for FPL point prediction models."""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas import CategoricalDtype
from sklearn.compose import ColumnTransformer
from sklearn.base import clone
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.inspection import permutation_importance
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from evaluation.metrics import (
    average_actual_points_in_predicted_top_k,
    mae,
    rmse,
    spearman_rank_correlation,
    top_k_precision,
)
from models.baseline import BASELINES, BaselineModel, MinutesAdjustedRollingMeanBaseline


LOGGER = logging.getLogger(__name__)

DEFAULT_INPUT_PATH = Path("data/processed/modeling_dataset.parquet")
DEFAULT_RESULTS_PATH = Path("reports/model_results.csv")
DEFAULT_SUMMARY_PATH = Path("reports/model_comparison.md")
DEFAULT_POSITION_RESULTS_PATH = Path("reports/position_model_comparison.csv")
DEFAULT_POSITION_SUMMARY_PATH = Path("reports/position_model_comparison.md")
DEFAULT_SUPPORTED_RESULTS_PATH = Path("reports/model_results_supported_seasons.csv")
DEFAULT_SUPPORTED_SUMMARY_PATH = Path("reports/model_comparison_supported_seasons.md")
DEFAULT_SUPPORTED_FILTER_REPORT_PATH = Path("reports/supported_season_filter_report.md")
DEFAULT_TEAM_FORM_FEATURE_REPORT_PATH = Path("reports/team_form_feature_report.md")
DEFAULT_BROAD_ABLATION_RESULTS_PATH = Path("reports/broad_feature_ablation_results.csv")
DEFAULT_BROAD_ABLATION_REPORT_PATH = Path("reports/broad_feature_ablation_report.md")
DEFAULT_FEATURE_SELECTION_RESULTS_PATH = Path("reports/feature_selection_results.csv")
DEFAULT_FEATURE_SELECTION_REPORT_PATH = Path("reports/feature_selection_report.md")
DEFAULT_SEASON_WINDOW_RESULTS_PATH = Path("reports/season_window_results.csv")
DEFAULT_SEASON_WINDOW_REPORT_PATH = Path("reports/season_window_comparison.md")
DEFAULT_POSITION_FEATURE_MASK_RESULTS_PATH = Path("reports/position_feature_mask_results.csv")
DEFAULT_POSITION_FEATURE_MASK_REPORT_PATH = Path("reports/position_feature_mask_report.md")
DEFAULT_POSITION_FEATURE_RELEVANCE_PATH = Path("reports/position_feature_relevance.csv")
DEFAULT_ENSEMBLE_RESULTS_PATH = Path("reports/ensemble_results.csv")
DEFAULT_ENSEMBLE_REPORT_PATH = Path("reports/ensemble_report.md")
TARGET_COLUMN = "next_gw_points"
MINUTES_COLUMN = "minutes"
NEXT_60_COLUMN = "__next_gw_60_plus"
TWO_STAGE_MODEL_NAME = "two_stage_minutes_points"
MINUTES_ADJUSTED_BASELINE_NAME = "minutes_adjusted_rolling_mean"
RESIDUAL_TARGET_COLUMN = "__residual_target"
BASELINE_PREDICTION_COLUMN = "__minutes_adjusted_baseline_prediction"
REQUIRED_COLUMNS = ("season", "gw", TARGET_COLUMN)
POSITION_COLUMN = "position"
POSITION_STRATEGY_MODEL_NAME = "Ridge"
MIN_POSITION_TRAIN_ROWS = 50
TOP_K_VALUES = (10, 20, 50)
RANKING_POSITIONS = ("GK", "DEF", "MID", "FWD")
POSITION_LABEL_MAP = {
    "GKP": "GK",
    "GK": "GK",
    "DEF": "DEF",
    "MID": "MID",
    "FWD": "FWD",
}
RESIDUAL_MODEL_NAMES = ("Ridge", "ElasticNet", "XGBoost", "CatBoost")
BASELINE_FEATURE_MODELS = {
    "pred_rolling_3_gameweek_mean": "rolling_3_gameweek_mean",
    "pred_rolling_5_gameweek_mean": "rolling_5_gameweek_mean",
    "pred_minutes_adjusted_rolling_mean": MINUTES_ADJUSTED_BASELINE_NAME,
}

EXCLUDED_FEATURE_COLUMNS = {
    "next_gw_points",
    "next_3_gw_points",
    "kickoff_time",
    "fixture",
}
STABLE_FEATURE_COLUMNS = (
    "position",
    "pred_rolling_3_gameweek_mean",
    "pred_rolling_5_gameweek_mean",
    "pred_minutes_adjusted_rolling_mean",
    "team_elo_pre_gw",
    "opponent_elo_pre_gw",
    "elo_difference",
    "home_adjusted_elo_difference",
    "team_goals_scored_mean_last_5",
    "team_goals_conceded_mean_last_5",
    "opponent_goals_scored_mean_last_5",
    "opponent_goals_conceded_mean_last_5",
    "team_clean_sheet_rate_last_5",
    "opponent_clean_sheet_rate_last_5",
    "points_last_1",
    "points_mean_last_3",
    "points_mean_last_5",
    "minutes_mean_last_3",
    "minutes_mean_last_5",
    "starts_last_5",
    "xG_last_5",
    "xA_last_5",
    "bonus_last_5",
    "bps_last_5",
)
TEAM_ELO_FEATURES = (
    "team_elo_pre_gw",
    "opponent_elo_pre_gw",
    "elo_difference",
    "home_adjusted_elo_difference",
)
TEAM_FORM_FEATURES = (
    "team_goals_scored_mean_last_5",
    "team_goals_conceded_mean_last_5",
    "opponent_goals_scored_mean_last_5",
    "opponent_goals_conceded_mean_last_5",
    "team_clean_sheet_rate_last_5",
    "opponent_clean_sheet_rate_last_5",
)
PLAYER_RETURNS_ROLLING_FEATURES = (
    "goals_scored_mean_last_3",
    "goals_scored_mean_last_5",
    "assists_mean_last_3",
    "assists_mean_last_5",
    "clean_sheets_mean_last_3",
    "clean_sheets_mean_last_5",
    "goals_conceded_mean_last_3",
    "goals_conceded_mean_last_5",
)
ICT_ROLLING_FEATURES = (
    "influence_mean_last_3",
    "influence_mean_last_5",
    "creativity_mean_last_3",
    "creativity_mean_last_5",
    "threat_mean_last_3",
    "threat_mean_last_5",
    "ict_index_mean_last_3",
    "ict_index_mean_last_5",
)
EXPECTED_STATS_ROLLING_FEATURES = (
    "expected_goals_mean_last_3",
    "expected_goals_mean_last_5",
    "expected_assists_mean_last_3",
    "expected_assists_mean_last_5",
    "expected_goal_involvements_mean_last_3",
    "expected_goal_involvements_mean_last_5",
    "expected_goals_conceded_mean_last_3",
    "expected_goals_conceded_mean_last_5",
)
OWNERSHIP_TRANSFERS_LAGGED_FEATURES = (
    "selected_lag_1",
    "transfers_in_lag_1",
    "transfers_out_lag_1",
    "transfers_balance_lag_1",
)
FIXTURE_HOME_FEATURES = ("was_home",)
RAW_CURRENT_GW_OUTCOME_COLUMNS = (
    "total_points",
    "minutes",
    "goals_scored",
    "assists",
    "clean_sheets",
    "goals_conceded",
    "bonus",
    "bps",
    "influence",
    "creativity",
    "threat",
    "ict_index",
    "team_h_score",
    "team_a_score",
)
RAW_TEAM_COLUMNS = ("team", "opponent_team")
FOCUS_DIRECT_MODEL_NAMES = ("Ridge", "CatBoost", "XGBoost")
FOCUS_RESIDUAL_MODEL_NAMES = ("Ridge", "CatBoost", "XGBoost")
POSITION_FEATURE_MASK_DIRECT_MODEL_NAMES = ("Ridge", "ElasticNet")
POSITION_FEATURE_MASK_RESIDUAL_MODEL_NAMES = ("Ridge", "ElasticNet")
POSITION_FEATURE_MASK_UNMASKED_DIRECT_MODEL_NAMES = ("CatBoost", "XGBoost")
POSITION_FEATURE_MASK_UNMASKED_RESIDUAL_MODEL_NAMES = ("CatBoost", "XGBoost")
POSITION_FEATURE_MASK_MASKED_MODELS = (
    "Ridge",
    "ElasticNet",
    "residual_Ridge",
    "residual_ElasticNet",
    "global_plus_position_interactions",
    "position_wise_models",
)
POSITION_FEATURE_MASK_UNMASKED_MODELS = (
    "CatBoost",
    "XGBoost",
    "residual_CatBoost",
    "residual_XGBoost",
    MINUTES_ADJUSTED_BASELINE_NAME,
)
POSITION_FEATURE_MASK_FOCUS_MODELS = (
    "Ridge",
    "ElasticNet",
    "CatBoost",
    "XGBoost",
    "residual_Ridge",
    "residual_ElasticNet",
    "residual_CatBoost",
    "residual_XGBoost",
    "global_plus_position_interactions",
    "position_wise_models",
    MINUTES_ADJUSTED_BASELINE_NAME,
)
ENSEMBLE_BASELINE_MODEL_NAMES = (
    MINUTES_ADJUSTED_BASELINE_NAME,
    "rolling_3_gameweek_mean",
    "rolling_5_gameweek_mean",
)
ENSEMBLE_DIRECT_MODEL_NAMES = ("CatBoost", "XGBoost")
ENSEMBLE_RESIDUAL_MODEL_NAMES = ("CatBoost", "XGBoost", "Ridge", "ElasticNet")
ENSEMBLE_CANDIDATE_MODELS = (
    MINUTES_ADJUSTED_BASELINE_NAME,
    "rolling_3_gameweek_mean",
    "rolling_5_gameweek_mean",
    "residual_CatBoost",
    "residual_XGBoost",
    "residual_Ridge",
    "residual_ElasticNet",
    "CatBoost",
    "XGBoost",
)
ENSEMBLE_TOP_MODEL_MEMBERS = (
    MINUTES_ADJUSTED_BASELINE_NAME,
    "rolling_5_gameweek_mean",
    "residual_CatBoost",
    "residual_XGBoost",
)
ENSEMBLE_BASELINE_RESIDUAL_MEMBERS = (
    MINUTES_ADJUSTED_BASELINE_NAME,
    "residual_CatBoost",
    "residual_XGBoost",
)
SEASON_WINDOW_FOCUS_MODELS = (
    MINUTES_ADJUSTED_BASELINE_NAME,
    "Ridge",
    "ElasticNet",
    "CatBoost",
    "XGBoost",
    "residual_Ridge",
    "residual_ElasticNet",
    "residual_CatBoost",
    "residual_XGBoost",
    "global_plus_position_interactions",
    "position_wise_models",
)
MIN_POSITION_SELECTION_ROWS = 50
MAX_SELECTED_FEATURES = 30


class BacktestError(ValueError):
    """Raised when the backtest cannot be run."""


@dataclass(frozen=True)
class SklearnModelSpec:
    name: str
    estimator: Any
    scale_numeric: bool = False


def read_dataset(path: Path) -> pd.DataFrame:
    """Read a parquet or CSV modeling dataset."""
    if not path.exists():
        raise BacktestError(f"Input dataset does not exist: {path}")
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise BacktestError(f"Unsupported input format for {path}; expected .parquet or .csv")


def validate_dataset(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise BacktestError(f"Backtest dataset is missing required columns: {missing}")
    if frame["season"].nunique() < 2:
        raise BacktestError("Rolling-origin validation requires at least two seasons.")


def add_next_minutes_60_target(frame: pd.DataFrame) -> pd.DataFrame:
    """Add whether the next player-season gameweek has at least 60 minutes."""
    if MINUTES_COLUMN not in frame.columns:
        raise BacktestError("Two-stage prediction requires a minutes column.")

    data = frame.copy()
    player_column = next((column for column in ("element", "id", "name") if column in data.columns), None)
    if player_column is None:
        raise BacktestError("Two-stage prediction requires element, id, or name to identify players.")

    data = data.sort_values([player_column, "season", "gw"]).copy()
    next_minutes = data.groupby([player_column, "season"], sort=False)[MINUTES_COLUMN].shift(-1)
    data[NEXT_60_COLUMN] = (next_minutes >= 60).where(next_minutes.notna())
    return data.sort_index()


def validation_seasons(frame: pd.DataFrame) -> list[str]:
    seasons = sorted(frame["season"].dropna().astype(str).unique())
    return seasons[1:]


def season_filtered_frame(frame: pd.DataFrame, min_season: str | None) -> pd.DataFrame:
    """Return a copy limited to seasons at or after min_season."""
    if min_season is None:
        return frame.copy()
    data = frame.copy()
    seasons = data["season"].astype(str)
    return data.loc[seasons >= str(min_season)].copy()


def season_filter_diagnostics(
    original: pd.DataFrame,
    filtered: pd.DataFrame,
    *,
    min_season: str | None,
) -> dict[str, Any]:
    all_seasons = sorted(original["season"].dropna().astype(str).unique())
    included = sorted(filtered["season"].dropna().astype(str).unique())
    excluded = [season for season in all_seasons if season not in included]
    reasons = {
        season: f"season is earlier than min-season {min_season}"
        for season in excluded
    }
    return {
        "min_season": min_season,
        "included_seasons": included,
        "excluded_seasons": excluded,
        "excluded_season_reasons": reasons,
        "original_rows": len(original),
        "filtered_rows": len(filtered),
    }


def split_train_validation(frame: pd.DataFrame, validation_season: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    seasons = frame["season"].astype(str)
    train = frame.loc[seasons < validation_season].copy()
    validation = frame.loc[seasons == validation_season].copy()
    return train, validation


def normalized_position_labels(positions: pd.Series) -> pd.Series:
    """Normalize historical FPL position labels and mark unknown labels missing."""
    normalized = positions.astype("string").str.upper().map(POSITION_LABEL_MAP)
    return normalized.astype("object").where(normalized.notna(), pd.NA)


def position_diagnostics(frame: pd.DataFrame) -> dict[str, Any]:
    """Summarize raw position data quality before normalization."""
    if POSITION_COLUMN not in frame.columns:
        return {
            "position_column_present": False,
            "unknown_positions": {},
            "seasons_without_position_data": [],
            "missing_position_rows_by_season": {},
        }

    positions = frame[POSITION_COLUMN].astype("string").str.upper()
    missing_mask = positions.isna()
    unknown_mask = positions.notna() & ~positions.isin(POSITION_LABEL_MAP)
    normalized = normalized_position_labels(frame[POSITION_COLUMN])
    seasons = frame["season"].astype(str) if "season" in frame.columns else pd.Series("all", index=frame.index)
    seasons_without_position_data = sorted(
        seasons.loc[normalized.notna()].unique()
    )
    all_seasons = sorted(seasons.dropna().astype(str).unique())
    missing_by_season = (
        frame.loc[missing_mask | unknown_mask]
        .assign(__season=seasons.loc[missing_mask | unknown_mask].astype(str))
        .groupby("__season")
        .size()
        .to_dict()
    )
    return {
        "position_column_present": True,
        "unknown_positions": positions.loc[unknown_mask].value_counts().to_dict(),
        "seasons_without_position_data": [
            season for season in all_seasons if season not in seasons_without_position_data
        ],
        "missing_position_rows_by_season": missing_by_season,
    }


def normalize_position_column(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize position labels consistently before modeling and reporting."""
    if POSITION_COLUMN not in frame.columns:
        return frame
    data = frame.copy()
    raw_positions = data[POSITION_COLUMN].astype("string").str.upper()
    unknown_positions = sorted(raw_positions.loc[raw_positions.notna() & ~raw_positions.isin(POSITION_LABEL_MAP)].unique())
    if unknown_positions:
        LOGGER.warning(
            "Excluding unknown position labels from position-aware outputs: %s",
            ", ".join(unknown_positions),
        )
    data[POSITION_COLUMN] = normalized_position_labels(data[POSITION_COLUMN])
    return data


def dedupe_columns(columns: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result = []
    for column in columns:
        if column in seen:
            continue
        seen.add(column)
        result.append(column)
    return tuple(result)


def ablation_feature_configurations() -> dict[str, tuple[str, ...]]:
    stable = tuple(STABLE_FEATURE_COLUMNS)
    no_team_strength = tuple(
        column for column in stable if column not in {*TEAM_ELO_FEATURES, *TEAM_FORM_FEATURES}
    )
    elo_only = dedupe_columns([*no_team_strength, *TEAM_ELO_FEATURES])
    team_form_only = dedupe_columns([*no_team_strength, *TEAM_FORM_FEATURES])
    all_candidates = (
        *PLAYER_RETURNS_ROLLING_FEATURES,
        *ICT_ROLLING_FEATURES,
        *EXPECTED_STATS_ROLLING_FEATURES,
        *OWNERSHIP_TRANSFERS_LAGGED_FEATURES,
        *FIXTURE_HOME_FEATURES,
    )
    return {
        "current_stable": stable,
        "no_team_strength": no_team_strength,
        "elo_only": elo_only,
        "team_form_only": team_form_only,
        "player_returns_rolling": dedupe_columns([*stable, *PLAYER_RETURNS_ROLLING_FEATURES]),
        "ict_rolling": dedupe_columns([*stable, *ICT_ROLLING_FEATURES]),
        "expected_stats_rolling": dedupe_columns([*stable, *EXPECTED_STATS_ROLLING_FEATURES]),
        "ownership_transfers_lagged": dedupe_columns(
            [*stable, *OWNERSHIP_TRANSFERS_LAGGED_FEATURES]
        ),
        "fixture_home": dedupe_columns([*stable, *FIXTURE_HOME_FEATURES]),
        "all_safe_candidates": dedupe_columns([*stable, *all_candidates]),
    }


def feature_selection_candidate_groups() -> dict[str, tuple[str, ...]]:
    return {
        "baseline_prediction_features": tuple(BASELINE_FEATURE_MODELS),
        "rolling_player_form_features": (
            "points_last_1",
            "points_mean_last_3",
            "points_mean_last_5",
            "minutes_mean_last_3",
            "minutes_mean_last_5",
            "starts_last_5",
            "bonus_last_5",
            "bps_last_5",
        ),
        "rolling_attacking_returns": (
            "goals_scored_mean_last_3",
            "goals_scored_mean_last_5",
            "assists_mean_last_3",
            "assists_mean_last_5",
        ),
        "rolling_defensive_returns": (
            "clean_sheets_mean_last_3",
            "clean_sheets_mean_last_5",
            "goals_conceded_mean_last_3",
            "goals_conceded_mean_last_5",
        ),
        "ict_rolling_features": ICT_ROLLING_FEATURES,
        "expected_stats_rolling_features": EXPECTED_STATS_ROLLING_FEATURES,
        "ownership_transfers_lagged": OWNERSHIP_TRANSFERS_LAGGED_FEATURES,
        "elo_features": TEAM_ELO_FEATURES,
        "rolling_team_form_features": TEAM_FORM_FEATURES,
        "fixture_home_feature": FIXTURE_HOME_FEATURES,
    }


def feature_selection_candidate_columns(frame: pd.DataFrame) -> tuple[str, ...]:
    grouped_columns = [
        column
        for columns in feature_selection_candidate_groups().values()
        for column in columns
    ]
    candidates = [POSITION_COLUMN, *grouped_columns]
    return tuple(column for column in dedupe_columns(candidates) if column in frame.columns)


def assert_feature_configuration_safe(columns: tuple[str, ...]) -> None:
    forbidden = {*RAW_CURRENT_GW_OUTCOME_COLUMNS, *RAW_TEAM_COLUMNS}
    included_forbidden = sorted(forbidden.intersection(columns))
    if included_forbidden:
        raise BacktestError(f"Unsafe raw columns in feature configuration: {included_forbidden}")


def feature_columns(
    frame: pd.DataFrame,
    configured_columns: tuple[str, ...] | list[str] | None = None,
) -> list[str]:
    configured = tuple(STABLE_FEATURE_COLUMNS if configured_columns is None else configured_columns)
    assert_feature_configuration_safe(configured)
    candidates = [column for column in configured if column in frame.columns]
    usable = [
        column
        for column in candidates
        if frame[column].notna().any()
        if pd.api.types.is_numeric_dtype(frame[column])
        or pd.api.types.is_bool_dtype(frame[column])
        or pd.api.types.is_object_dtype(frame[column])
        or isinstance(frame[column].dtype, CategoricalDtype)
    ]
    if not usable:
        raise BacktestError("No usable feature columns found.")
    return usable


def build_preprocessor(train: pd.DataFrame, columns: list[str], *, scale_numeric: bool) -> ColumnTransformer:
    numeric_columns = [
        column
        for column in columns
        if pd.api.types.is_numeric_dtype(train[column]) or pd.api.types.is_bool_dtype(train[column])
    ]
    categorical_columns = [column for column in columns if column not in numeric_columns]

    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))

    transformers: list[tuple[str, Any, list[str]]] = []
    if numeric_columns:
        transformers.append(("numeric", Pipeline(numeric_steps), numeric_columns))
    if categorical_columns:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_columns,
            )
        )
    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
    return preprocessor.set_output(transform="pandas")


def numeric_feature_candidates(frame: pd.DataFrame, columns: tuple[str, ...]) -> list[str]:
    assert_feature_configuration_safe(columns)
    return [
        column
        for column in columns
        if column in frame.columns
        and frame[column].notna().any()
        and (
            pd.api.types.is_numeric_dtype(frame[column])
            or pd.api.types.is_bool_dtype(frame[column])
        )
    ]


def add_numeric_position_interactions(
    frame: pd.DataFrame,
    columns: list[str],
    *,
    positions: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    if POSITION_COLUMN not in frame.columns:
        return frame.copy(), columns
    data = frame.copy()
    if positions is None:
        positions = sorted(data[POSITION_COLUMN].dropna().astype(str).unique())
    interaction_data = {}
    for position in positions:
        mask = data[POSITION_COLUMN].astype(str) == position
        for column in columns:
            interaction_column = f"{column}__position_{position}"
            interaction_data[interaction_column] = pd.to_numeric(
                data[column],
                errors="coerce",
            ).where(mask, 0)
    if not interaction_data:
        return data, columns
    interactions = pd.DataFrame(interaction_data, index=data.index)
    return pd.concat([data, interactions], axis=1), [*columns, *interactions.columns]


def internal_train_validation_split(train: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    seasons = sorted(train["season"].dropna().astype(str).unique())
    if len(seasons) < 2:
        return train, train
    internal_validation_season = seasons[-1]
    season_values = train["season"].astype(str)
    internal_train = train.loc[season_values < internal_validation_season].copy()
    internal_validation = train.loc[season_values == internal_validation_season].copy()
    if internal_train.empty or internal_validation.empty:
        return train, train
    return internal_train, internal_validation


def metric_value(y_true: pd.Series, y_pred: pd.Series, metric: str) -> float:
    if metric == "mae":
        return mae(y_true, y_pred)
    if metric == "rmse":
        return rmse(y_true, y_pred)
    if metric == "spearman":
        return -spearman_rank_correlation(y_true, y_pred)
    if metric == "combined":
        return mae(y_true, y_pred) + rmse(y_true, y_pred) - spearman_rank_correlation(
            y_true,
            y_pred,
        )
    raise BacktestError(f"Unsupported feature selection metric: {metric}")


def select_features_elasticnet(
    train: pd.DataFrame,
    candidate_columns: tuple[str, ...],
    *,
    target_column: str = TARGET_COLUMN,
    random_state: int = 42,
    max_features: int = MAX_SELECTED_FEATURES,
) -> list[str]:
    train_model = train.dropna(subset=[target_column]).copy()
    columns = numeric_feature_candidates(train_model, candidate_columns)
    if not columns:
        return []
    x_train = train_model[columns].replace({pd.NA: np.nan})
    y_train = train_model[target_column]
    pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                ElasticNet(alpha=0.001, l1_ratio=0.5, max_iter=10_000, random_state=random_state),
            ),
        ]
    )
    pipeline.fit(x_train, y_train)
    coefficients = pd.Series(pipeline.named_steps["model"].coef_, index=columns)
    selected = coefficients.loc[coefficients.abs() > 1e-8].abs().sort_values(ascending=False)
    if selected.empty:
        selected = coefficients.abs().sort_values(ascending=False).head(min(5, len(coefficients)))
    return list(selected.head(max_features).index)


def select_features_permutation_importance(
    train: pd.DataFrame,
    candidate_columns: tuple[str, ...],
    *,
    random_state: int = 42,
    max_features: int = MAX_SELECTED_FEATURES,
) -> list[str]:
    internal_train, internal_validation = internal_train_validation_split(train)
    train_model = internal_train.dropna(subset=[TARGET_COLUMN]).copy()
    validation_model = internal_validation.dropna(subset=[TARGET_COLUMN]).copy()
    columns = numeric_feature_candidates(train_model, candidate_columns)
    if not columns or validation_model.empty:
        return columns[:max_features]
    pipeline = Pipeline(
        [
            ("preprocess", build_preprocessor(train_model, columns, scale_numeric=True)),
            ("model", Ridge(alpha=1.0)),
        ]
    )
    pipeline.fit(train_model[columns].replace({pd.NA: np.nan}), train_model[TARGET_COLUMN])
    importance = permutation_importance(
        pipeline,
        validation_model[columns].replace({pd.NA: np.nan}),
        validation_model[TARGET_COLUMN],
        scoring="neg_mean_absolute_error",
        n_repeats=3,
        random_state=random_state,
    )
    scores = pd.Series(importance.importances_mean, index=columns)
    selected = scores.loc[scores > 0].sort_values(ascending=False)
    return list(selected.head(max_features).index)


def select_features_group_forward(
    train: pd.DataFrame,
    *,
    selection_metric: str = "combined",
) -> list[str]:
    groups = feature_selection_candidate_groups()
    internal_train, internal_validation = internal_train_validation_split(train)
    train_model = internal_train.dropna(subset=[TARGET_COLUMN]).copy()
    validation_model = internal_validation.dropna(subset=[TARGET_COLUMN]).copy()
    selected = list(
        column
        for column in [
            *groups["baseline_prediction_features"],
            *groups["rolling_player_form_features"],
        ]
        if column in train_model.columns
    )
    if train_model.empty or validation_model.empty:
        return selected

    def score(columns: list[str]) -> float:
        usable = numeric_feature_candidates(train_model, tuple(columns))
        if not usable:
            return float("inf")
        pipeline = Pipeline(
            [
                ("preprocess", build_preprocessor(train_model, usable, scale_numeric=True)),
                ("model", Ridge(alpha=1.0)),
            ]
        )
        pipeline.fit(train_model[usable].replace({pd.NA: np.nan}), train_model[TARGET_COLUMN])
        predictions = pd.Series(
            pipeline.predict(validation_model[usable].replace({pd.NA: np.nan})),
            index=validation_model.index,
        )
        return metric_value(validation_model[TARGET_COLUMN], predictions, selection_metric)

    best_score = score(selected)
    for group_name, group_columns in groups.items():
        if group_name in {"baseline_prediction_features", "rolling_player_form_features"}:
            continue
        trial = dedupe_columns([*selected, *group_columns])
        trial_score = score(list(trial))
        if trial_score < best_score:
            selected = list(trial)
            best_score = trial_score
    return selected


def sklearn_model_specs(random_state: int = 42) -> list[SklearnModelSpec]:
    specs = [
        SklearnModelSpec("Ridge", Ridge(alpha=1.0), scale_numeric=True),
        SklearnModelSpec(
            "ElasticNet",
            ElasticNet(alpha=0.01, l1_ratio=0.2, max_iter=10_000, random_state=random_state),
            scale_numeric=True,
        ),
    ]

    if importlib.util.find_spec("xgboost") is not None:
        from xgboost import XGBRegressor

        specs.append(
            SklearnModelSpec(
                "XGBoost",
                XGBRegressor(
                    n_estimators=300,
                    max_depth=3,
                    learning_rate=0.05,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    objective="reg:squarederror",
                    random_state=random_state,
                    n_jobs=1,
                ),
            )
        )
    else:
        LOGGER.warning("Skipping XGBoost: package is not installed.")

    if importlib.util.find_spec("catboost") is not None:
        from catboost import CatBoostRegressor

        specs.append(
            SklearnModelSpec(
                "CatBoost",
                CatBoostRegressor(
                    iterations=300,
                    depth=6,
                    learning_rate=0.05,
                    loss_function="RMSE",
                    random_seed=random_state,
                    thread_count=1,
                    verbose=False,
                ),
            )
        )
    else:
        LOGGER.warning("Skipping CatBoost: package is not installed.")

    return specs


def residual_model_specs(random_state: int = 42) -> list[SklearnModelSpec]:
    """Return the model specs used for residual correction experiments."""
    return [spec for spec in sklearn_model_specs(random_state) if spec.name in RESIDUAL_MODEL_NAMES]


def evaluate_predictions(
    *,
    model_name: str,
    validation_season: str,
    y_true: pd.Series,
    y_pred: pd.Series,
    positions: pd.Series | None = None,
) -> dict[str, Any]:
    valid = pd.concat([y_true, y_pred], axis=1).dropna()
    if valid.empty:
        raise BacktestError(
            f"No valid predictions for {model_name} in validation season {validation_season}."
        )

    row = {
        "validation_season": validation_season,
        "model": model_name,
        "n_train": np.nan,
        "n_validation": len(valid),
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "spearman": spearman_rank_correlation(y_true, y_pred),
    }
    for k in TOP_K_VALUES:
        row[f"top_{k}_precision"] = top_k_precision(y_true, y_pred, k)
        row[f"top_{k}_avg_actual_points"] = average_actual_points_in_predicted_top_k(
            y_true,
            y_pred,
            k,
        )

    if positions is not None:
        aligned_positions = normalized_position_labels(positions.reindex(y_true.index))
        for position in RANKING_POSITIONS:
            mask = aligned_positions == position
            for k in TOP_K_VALUES:
                row[f"{position}_top_{k}_precision"] = top_k_precision(
                    y_true.loc[mask],
                    y_pred.loc[mask],
                    k,
                )
                row[f"{position}_top_{k}_avg_actual_points"] = (
                    average_actual_points_in_predicted_top_k(
                        y_true.loc[mask],
                        y_pred.loc[mask],
                        k,
                    )
                )
    return row


def metric_row(
    *,
    validation_season: str,
    strategy: str,
    position: str,
    n_train: int,
    y_true: pd.Series,
    y_pred: pd.Series,
) -> dict[str, Any]:
    row = evaluate_predictions(
        model_name=strategy,
        validation_season=validation_season,
        y_true=y_true,
        y_pred=y_pred,
    )
    row["strategy"] = row.pop("model")
    row["position"] = position
    row["n_train"] = n_train
    for k in TOP_K_VALUES:
        row[f"top_{k}_precision"] = top_k_precision(y_true, y_pred, k)
        row[f"top_{k}_avg_actual_points"] = average_actual_points_in_predicted_top_k(
            y_true,
            y_pred,
            k,
        )
    return row


def evaluate_baselines(
    validation: pd.DataFrame,
    *,
    validation_season: str,
    models: tuple[BaselineModel, ...] = BASELINES,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    y_true = validation[TARGET_COLUMN]
    for model in models:
        try:
            y_pred = model.predict(validation)
            rows.append(
                evaluate_predictions(
                    model_name=model.name,
                    validation_season=validation_season,
                    y_true=y_true,
                    y_pred=y_pred,
                    positions=validation[POSITION_COLUMN] if POSITION_COLUMN in validation.columns else None,
                )
            )
        except (ValueError, KeyError) as exc:
            LOGGER.warning("Skipping baseline %s for %s: %s", model.name, validation_season, exc)
    return rows


def evaluate_sklearn_models(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    validation_season: str,
    models: list[SklearnModelSpec],
    configured_columns: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    train_model = train.dropna(subset=[TARGET_COLUMN]).copy()
    validation_model = validation.dropna(subset=[TARGET_COLUMN]).copy()
    if train_model.empty or validation_model.empty:
        raise BacktestError(f"No train/validation rows with targets for season {validation_season}.")

    columns = feature_columns(train_model, configured_columns)
    x_train = train_model[columns].replace({pd.NA: np.nan})
    y_train = train_model[TARGET_COLUMN]
    x_validation = validation_model[columns].replace({pd.NA: np.nan})
    y_validation = validation_model[TARGET_COLUMN]

    for spec in models:
        pipeline = Pipeline(
            [
                (
                    "preprocess",
                    build_preprocessor(train_model, columns, scale_numeric=spec.scale_numeric),
                ),
                ("model", spec.estimator),
            ]
        )
        try:
            pipeline.fit(x_train, y_train)
            y_pred = pd.Series(pipeline.predict(x_validation), index=y_validation.index)
            row = evaluate_predictions(
                model_name=spec.name,
                validation_season=validation_season,
                y_true=y_validation,
                y_pred=y_pred,
                positions=(
                    validation_model[POSITION_COLUMN]
                    if POSITION_COLUMN in validation_model.columns
                    else None
                ),
            )
            row["n_train"] = len(train_model)
            rows.append(row)
        except Exception as exc:  # noqa: BLE001 - model libraries raise varied exception types.
            LOGGER.warning("Skipping model %s for %s: %s", spec.name, validation_season, exc)
    return rows


def add_baseline_prediction_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add leakage-safe baseline predictions as model features."""
    data = frame.copy()
    baseline_by_name = {model.name: model for model in BASELINES}
    for feature_name, model_name in BASELINE_FEATURE_MODELS.items():
        model = baseline_by_name[model_name]
        data[feature_name] = model.predict(data)
    return data


def minutes_adjusted_baseline_predictions(frame: pd.DataFrame) -> pd.Series:
    """Compute the strongest baseline through the existing baseline implementation."""
    return MinutesAdjustedRollingMeanBaseline().predict(frame).rename(BASELINE_PREDICTION_COLUMN)


def add_residual_target(frame: pd.DataFrame, baseline_predictions: pd.Series) -> pd.DataFrame:
    """Add residual_target = actual - minutes-adjusted baseline prediction."""
    data = frame.copy()
    data[BASELINE_PREDICTION_COLUMN] = baseline_predictions.reindex(data.index)
    data[RESIDUAL_TARGET_COLUMN] = data[TARGET_COLUMN] - data[BASELINE_PREDICTION_COLUMN]
    return data


def final_residual_prediction(
    baseline_predictions: pd.Series,
    predicted_residuals: pd.Series,
) -> pd.Series:
    """Compose final residual model predictions."""
    return baseline_predictions.add(predicted_residuals, fill_value=np.nan)


def evaluate_residual_models(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    validation_season: str,
    models: list[SklearnModelSpec],
    configured_columns: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    train_with_residual = add_residual_target(train, minutes_adjusted_baseline_predictions(train))
    validation_with_baseline = validation.copy()
    validation_with_baseline[BASELINE_PREDICTION_COLUMN] = minutes_adjusted_baseline_predictions(
        validation
    )

    train_model = train_with_residual.dropna(
        subset=[TARGET_COLUMN, BASELINE_PREDICTION_COLUMN, RESIDUAL_TARGET_COLUMN]
    ).copy()
    validation_model = validation_with_baseline.dropna(
        subset=[TARGET_COLUMN, BASELINE_PREDICTION_COLUMN]
    ).copy()
    if train_model.empty or validation_model.empty:
        raise BacktestError(f"No residual train/validation rows for season {validation_season}.")

    columns = feature_columns(train_model, configured_columns)
    x_train = train_model[columns].replace({pd.NA: np.nan})
    y_train = train_model[RESIDUAL_TARGET_COLUMN]
    x_validation = validation_model[columns].replace({pd.NA: np.nan})
    y_validation = validation_model[TARGET_COLUMN]

    for spec in models:
        pipeline = Pipeline(
            [
                (
                    "preprocess",
                    build_preprocessor(train_model, columns, scale_numeric=spec.scale_numeric),
                ),
                ("model", clone(spec.estimator)),
            ]
        )
        try:
            pipeline.fit(x_train, y_train)
            predicted_residual = pd.Series(pipeline.predict(x_validation), index=y_validation.index)
            y_pred = final_residual_prediction(
                validation_model[BASELINE_PREDICTION_COLUMN],
                predicted_residual,
            )
            row = evaluate_predictions(
                model_name=f"residual_{spec.name}",
                validation_season=validation_season,
                y_true=y_validation,
                y_pred=y_pred,
                positions=(
                    validation_model[POSITION_COLUMN]
                    if POSITION_COLUMN in validation_model.columns
                    else None
                ),
            )
            row["n_train"] = len(train_model)
            rows.append(row)
        except Exception as exc:  # noqa: BLE001 - model libraries raise varied exception types.
            LOGGER.warning(
                "Skipping residual model %s for %s: %s",
                spec.name,
                validation_season,
                exc,
            )
    return rows


def _classification_pipeline(train: pd.DataFrame, columns: list[str]) -> Pipeline:
    if train[NEXT_60_COLUMN].nunique(dropna=True) < 2:
        classifier = DummyClassifier(strategy="most_frequent")
    else:
        classifier = LogisticRegression(max_iter=1_000, random_state=42)

    return Pipeline(
        [
            ("preprocess", build_preprocessor(train, columns, scale_numeric=True)),
            ("model", classifier),
        ]
    )


def _regression_pipeline(
    train: pd.DataFrame,
    columns: list[str],
    estimator: Any,
    *,
    scale_numeric: bool,
) -> Pipeline:
    return Pipeline(
        [
            ("preprocess", build_preprocessor(train, columns, scale_numeric=scale_numeric)),
            ("model", estimator),
        ]
    )


def _predict_positive_probability(model: Pipeline, x_validation: pd.DataFrame) -> np.ndarray:
    probabilities = model.predict_proba(x_validation)
    classes = model.named_steps["model"].classes_
    if True in classes:
        positive_index = list(classes).index(True)
        return probabilities[:, positive_index]
    return np.zeros(len(x_validation))


def _fit_conditional_regressor(
    train: pd.DataFrame,
    columns: list[str],
    *,
    condition_value: bool,
    fallback_estimator: Any,
) -> Pipeline:
    subset = train.loc[train[NEXT_60_COLUMN] == condition_value]
    if subset.empty:
        estimator = DummyRegressor(strategy="mean")
        subset = train
    else:
        estimator = clone(fallback_estimator)

    model = _regression_pipeline(
        subset,
        columns,
        estimator,
        scale_numeric=not isinstance(estimator, DummyRegressor),
    )
    model.fit(subset[columns].replace({pd.NA: np.nan}), subset[TARGET_COLUMN])
    return model


def evaluate_two_stage_model(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    validation_season: str,
    configured_columns: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    train_model = train.dropna(subset=[TARGET_COLUMN, NEXT_60_COLUMN]).copy()
    validation_model = validation.dropna(subset=[TARGET_COLUMN]).copy()
    if train_model.empty or validation_model.empty:
        raise BacktestError(f"No rows available for two-stage model in season {validation_season}.")

    columns = feature_columns(train_model, configured_columns)
    x_train = train_model[columns].replace({pd.NA: np.nan})
    x_validation = validation_model[columns].replace({pd.NA: np.nan})
    y_validation = validation_model[TARGET_COLUMN]

    classifier = _classification_pipeline(train_model, columns)
    classifier.fit(x_train, train_model[NEXT_60_COLUMN].astype(bool))
    p_60_plus = _predict_positive_probability(classifier, x_validation)

    base_regressor = Ridge(alpha=1.0)
    regressor_60_plus = _fit_conditional_regressor(
        train_model,
        columns,
        condition_value=True,
        fallback_estimator=base_regressor,
    )
    regressor_under_60 = _fit_conditional_regressor(
        train_model,
        columns,
        condition_value=False,
        fallback_estimator=base_regressor,
    )

    expected_if_60_plus = regressor_60_plus.predict(x_validation)
    expected_if_under_60 = regressor_under_60.predict(x_validation)
    y_pred = pd.Series(
        p_60_plus * expected_if_60_plus + (1 - p_60_plus) * expected_if_under_60,
        index=y_validation.index,
    )

    row = evaluate_predictions(
        model_name=TWO_STAGE_MODEL_NAME,
        validation_season=validation_season,
        y_true=y_validation,
        y_pred=y_pred,
        positions=validation_model[POSITION_COLUMN] if POSITION_COLUMN in validation_model.columns else None,
    )
    row["n_train"] = len(train_model)
    return row


def add_position_interactions(
    frame: pd.DataFrame,
    columns: list[str],
    *,
    positions: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    if POSITION_COLUMN not in frame.columns:
        raise BacktestError("Position interactions require a position column.")

    data = frame.copy()
    numeric_columns = []
    for column in columns:
        if column == POSITION_COLUMN or column not in data.columns:
            continue
        if pd.api.types.is_numeric_dtype(data[column]) or pd.api.types.is_bool_dtype(data[column]):
            numeric_columns.append(column)
            continue
        if pd.to_numeric(data[column], errors="coerce").notna().any():
            numeric_columns.append(column)
    if positions is None:
        positions = sorted(data[POSITION_COLUMN].dropna().astype(str).unique())
    interaction_columns: list[str] = []
    for position in positions:
        mask = data[POSITION_COLUMN].astype(str) == position
        for column in numeric_columns:
            interaction_column = f"{column}__position_{position}"
            numeric_values = pd.to_numeric(data[column], errors="coerce")
            data[interaction_column] = numeric_values.where(mask, 0)
            interaction_columns.append(interaction_column)
    return data, columns + interaction_columns


def fit_predict_direct_model(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    estimator: Any,
    include_position: bool,
    add_interactions: bool,
    configured_columns: tuple[str, ...] | None = None,
) -> pd.Series:
    columns = feature_columns(train, configured_columns)
    if not include_position:
        columns = [column for column in columns if column != POSITION_COLUMN]
    train_features = train.copy()
    validation_features = validation.copy()
    if add_interactions:
        base_columns = columns.copy()
        train_positions = sorted(train_features[POSITION_COLUMN].dropna().astype(str).unique())
        train_features, columns = add_position_interactions(
            train_features,
            base_columns,
            positions=train_positions,
        )
        validation_features, validation_columns = add_position_interactions(
            validation_features,
            base_columns,
            positions=train_positions,
        )
        columns = validation_columns

    pipeline = Pipeline(
        [
            ("preprocess", build_preprocessor(train_features, columns, scale_numeric=True)),
            ("model", clone(estimator)),
        ]
    )
    pipeline.fit(train_features[columns].replace({pd.NA: np.nan}), train[TARGET_COLUMN])
    return pd.Series(
        pipeline.predict(validation_features[columns].replace({pd.NA: np.nan})),
        index=validation.index,
    )


def evaluate_position_strategies(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    validation_season: str,
    estimator: Any | None = None,
    min_position_train_rows: int = MIN_POSITION_TRAIN_ROWS,
    configured_columns: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    if POSITION_COLUMN not in train.columns or POSITION_COLUMN not in validation.columns:
        LOGGER.warning("Skipping position strategies for %s: position column is missing.", validation_season)
        return []

    base_estimator = Ridge(alpha=1.0) if estimator is None else estimator
    train_model = train.dropna(subset=[TARGET_COLUMN, POSITION_COLUMN]).copy()
    validation_model = validation.dropna(subset=[TARGET_COLUMN, POSITION_COLUMN]).copy()
    if train_model.empty or validation_model.empty:
        LOGGER.warning(
            "Skipping position strategies for %s because normalized position data is unavailable.",
            validation_season,
        )
        return []

    predictions = pd.DataFrame(index=validation_model.index)
    predictions["actual"] = validation_model[TARGET_COLUMN]
    predictions[POSITION_COLUMN] = validation_model[POSITION_COLUMN]

    global_fallback = fit_predict_direct_model(
        train_model,
        validation_model,
        estimator=base_estimator,
        include_position=True,
        add_interactions=False,
        configured_columns=configured_columns,
    )
    predictions["global_plus_position_interactions"] = fit_predict_direct_model(
        train_model,
        validation_model,
        estimator=base_estimator,
        include_position=True,
        add_interactions=True,
        configured_columns=configured_columns,
    )

    position_wise = pd.Series(index=validation_model.index, dtype="float64")
    for position, validation_position in validation_model.groupby(POSITION_COLUMN, dropna=False):
        position_key = str(position)
        train_position = train_model.loc[train_model[POSITION_COLUMN].astype(str) == position_key]
        if len(train_position) < min_position_train_rows:
            position_wise.loc[validation_position.index] = global_fallback.loc[validation_position.index]
            continue
        position_wise.loc[validation_position.index] = fit_predict_direct_model(
            train_position,
            validation_position,
            estimator=base_estimator,
            include_position=False,
            add_interactions=False,
            configured_columns=configured_columns,
        )
    predictions["position_wise_models"] = position_wise

    rows: list[dict[str, Any]] = []
    for strategy in (
        "position_wise_models",
        "global_plus_position_interactions",
    ):
        rows.append(
            metric_row(
                validation_season=validation_season,
                strategy=strategy,
                position="ALL",
                n_train=len(train_model),
                y_true=predictions["actual"],
                y_pred=predictions[strategy],
            )
        )
        for position, group in predictions.groupby(POSITION_COLUMN):
            rows.append(
                metric_row(
                    validation_season=validation_season,
                    strategy=strategy,
                    position=str(position),
                    n_train=len(train_model),
                    y_true=group["actual"],
                    y_pred=group[strategy],
                )
            )
    return rows


def run_position_model_backtest(
    frame: pd.DataFrame,
    *,
    estimator: Any | None = None,
    min_position_train_rows: int = MIN_POSITION_TRAIN_ROWS,
    min_season: str | None = None,
    configured_columns: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    validate_dataset(frame)
    original = frame.copy()
    data = season_filtered_frame(original, min_season)
    validate_dataset(data)
    data["season"] = data["season"].astype(str)
    diagnostics = {"position": position_diagnostics(data)}
    if min_season is not None:
        diagnostics["season_filter"] = season_filter_diagnostics(
            original,
            data,
            min_season=min_season,
        )
    data = normalize_position_column(data)
    data = add_baseline_prediction_features(data)
    data = data.sort_values(["season", "gw"]).reset_index(drop=True)

    rows: list[dict[str, Any]] = []
    for season in validation_seasons(data):
        train, validation = split_train_validation(data, season)
        if train.empty or validation.empty:
            continue
        rows.extend(
            evaluate_position_strategies(
                train,
                validation,
                validation_season=season,
                estimator=estimator,
                min_position_train_rows=min_position_train_rows,
                configured_columns=configured_columns,
            )
        )

    if not rows:
        raise BacktestError("No position model comparison results were produced.")
    results = pd.DataFrame(rows).sort_values(
        ["validation_season", "strategy", "position"]
    ).reset_index(drop=True)
    results.attrs["diagnostics"] = diagnostics
    return results


def run_backtest(
    frame: pd.DataFrame,
    *,
    model_specs: list[SklearnModelSpec] | None = None,
    residual_specs: list[SklearnModelSpec] | None = None,
    min_season: str | None = None,
    configured_columns: tuple[str, ...] | None = None,
    include_two_stage: bool = True,
) -> pd.DataFrame:
    """Run rolling-origin validation by season."""
    validate_dataset(frame)
    original = frame.copy()
    data = season_filtered_frame(original, min_season)
    validate_dataset(data)
    data["season"] = data["season"].astype(str)
    diagnostics: dict[str, Any] = {"position": position_diagnostics(data)}
    if min_season is not None:
        diagnostics["season_filter"] = season_filter_diagnostics(
            original,
            data,
            min_season=min_season,
        )
    data = normalize_position_column(data)
    if MINUTES_COLUMN in data.columns:
        data = add_next_minutes_60_target(data)
    else:
        LOGGER.warning("Skipping two-stage model: minutes column is missing.")
    data = add_baseline_prediction_features(data)
    data = data.sort_values(["season", "gw"]).reset_index(drop=True)
    specs = sklearn_model_specs() if model_specs is None else model_specs
    residual_specs = residual_model_specs() if residual_specs is None else residual_specs

    rows: list[dict[str, Any]] = []
    for season in validation_seasons(data):
        train, validation = split_train_validation(data, season)
        if train.empty or validation.empty:
            LOGGER.warning("Skipping validation season %s because train or validation is empty.", season)
            continue

        LOGGER.info("Backtesting validation season %s with %d train rows.", season, len(train))
        baseline_rows = evaluate_baselines(validation, validation_season=season)
        for row in baseline_rows:
            row["n_train"] = len(train)
        rows.extend(baseline_rows)
        rows.extend(
            evaluate_sklearn_models(
                train,
                validation,
                validation_season=season,
                models=specs,
                configured_columns=configured_columns,
            )
        )
        if residual_specs:
            rows.extend(
                evaluate_residual_models(
                    train,
                    validation,
                    validation_season=season,
                    models=residual_specs,
                    configured_columns=configured_columns,
                )
            )
        if include_two_stage and NEXT_60_COLUMN in data.columns:
            try:
                rows.append(
                    evaluate_two_stage_model(
                        train,
                        validation,
                        validation_season=season,
                        configured_columns=configured_columns,
                    )
                )
            except (ValueError, KeyError) as exc:
                LOGGER.warning("Skipping two-stage model for %s: %s", season, exc)

    if not rows:
        raise BacktestError("No backtest results were produced.")
    results = pd.DataFrame(rows).sort_values(["validation_season", "mae", "model"]).reset_index(drop=True)
    diagnostics["model_row_counts"] = results["model"].value_counts().sort_index().to_dict()
    diagnostics["expected_direct_models"] = [spec.name for spec in specs]
    diagnostics["expected_residual_models"] = [f"residual_{spec.name}" for spec in residual_specs]
    results.attrs["diagnostics"] = diagnostics
    return results


def write_results(results: pd.DataFrame, path: Path = DEFAULT_RESULTS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(path, index=False)


def diagnostics_markdown_lines(diagnostics: dict[str, Any]) -> list[str]:
    if not diagnostics:
        return ["## Diagnostics", "", "No diagnostics were attached to these results."]

    lines = ["## Diagnostics", ""]
    position = diagnostics.get("position", {})
    if position:
        if not position.get("position_column_present", False):
            lines.append("- Position column was not present, so position-aware metrics were unavailable.")
        else:
            unknown_positions = position.get("unknown_positions", {})
            if unknown_positions:
                unknown_summary = ", ".join(
                    f"{label} ({count})" for label, count in sorted(unknown_positions.items())
                )
                lines.append(f"- Unknown position labels were excluded from position-aware outputs: {unknown_summary}.")
            else:
                lines.append("- No unknown position labels were found after applying position normalization.")

            missing_seasons = position.get("seasons_without_position_data", [])
            if missing_seasons:
                lines.append(
                    "- These seasons have no normalized position data, so their position-specific ranking "
                    f"metrics are blank or absent: {', '.join(missing_seasons)}."
                )
            missing_counts = position.get("missing_position_rows_by_season", {})
            if missing_counts:
                count_summary = ", ".join(
                    f"{season}: {count}" for season, count in sorted(missing_counts.items())
                )
                lines.append(f"- Missing or excluded position rows by season: {count_summary}.")

    model_row_counts = diagnostics.get("model_row_counts", {})
    if model_row_counts:
        lines.append(
            "- Report CSV files are written with overwrite semantics, not append semantics; model rows "
            "shown below were produced by the current backtest result frame."
        )
        count_summary = ", ".join(
            f"{model}: {count}" for model, count in sorted(model_row_counts.items())
        )
        lines.append(f"- Model row counts in this result: {count_summary}.")
    season_filter = diagnostics.get("season_filter", {})
    if season_filter:
        included = season_filter.get("included_seasons", [])
        excluded = season_filter.get("excluded_seasons", [])
        lines.append(
            f"- Season filter enabled with min-season `{season_filter.get('min_season')}`."
        )
        lines.append(f"- Included seasons: {', '.join(included) if included else 'none'}.")
        lines.append(f"- Excluded seasons: {', '.join(excluded) if excluded else 'none'}.")
    lines.append("")
    return lines


def write_markdown_summary(results: pd.DataFrame, path: Path = DEFAULT_SUMMARY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    overall_ranking_columns = [
        column
        for column in results.columns
        if column.startswith("top_")
        and (column.endswith("_precision") or column.endswith("_avg_actual_points"))
    ]
    aggregate_spec = {
        "seasons": ("validation_season", "nunique"),
        "mean_mae": ("mae", "mean"),
        "mean_rmse": ("rmse", "mean"),
        "mean_spearman": ("spearman", "mean"),
    }
    aggregate_spec.update(
        {
            f"mean_{column}": (column, "mean")
            for column in overall_ranking_columns
            if column in results.columns
        }
    )
    aggregate = (
        results.groupby("model", as_index=False)
        .agg(**aggregate_spec)
        .sort_values(["mean_mae", "model"])
    )
    position_rows = []
    for position in RANKING_POSITIONS:
        position_columns = [
            column
            for column in results.columns
            if column.startswith(f"{position}_top_")
            and (column.endswith("_precision") or column.endswith("_avg_actual_points"))
        ]
        if not position_columns:
            continue
        position_aggregate = (
            results.groupby("model", as_index=False)[position_columns]
            .mean()
            .assign(position=position)
        )
        position_aggregate = position_aggregate.rename(
            columns={column: column.removeprefix(f"{position}_") for column in position_columns}
        )
        position_rows.append(position_aggregate)
    ranking_by_position = (
        pd.concat(position_rows, ignore_index=True)
        if position_rows
        else pd.DataFrame(columns=["model", "position"])
    )
    if not ranking_by_position.empty:
        ranking_by_position = ranking_by_position[
            ["model", "position"]
            + [column for column in ranking_by_position.columns if column not in {"model", "position"}]
        ].sort_values(["position", "top_10_avg_actual_points", "model"], ascending=[True, False, True])
    direct_results = results.loc[results["model"] != TWO_STAGE_MODEL_NAME]
    two_stage_results = results.loc[results["model"] == TWO_STAGE_MODEL_NAME]
    comparison_lines = ["Two-stage model was not evaluated."]
    if not direct_results.empty and not two_stage_results.empty:
        direct_aggregate = (
            direct_results.groupby("model", as_index=False)["mae"].mean().sort_values(["mae", "model"])
        )
        best_direct = direct_aggregate.iloc[0]
        two_stage_mae = two_stage_results["mae"].mean()
        delta = two_stage_mae - float(best_direct["mae"])
        comparison_lines = [
            f"Best direct points model by mean MAE: {best_direct['model']} "
            f"({float(best_direct['mae']):.4f}).",
            f"Two-stage mean MAE: {two_stage_mae:.4f}.",
            f"MAE delta versus best direct model: {delta:.4f}.",
        ]

    def markdown_table(frame: pd.DataFrame) -> str:
        headers = list(frame.columns)
        rows = []
        for _, row in frame.iterrows():
            values = []
            for value in row:
                if isinstance(value, float):
                    values.append(f"{value:.4f}" if not np.isnan(value) else "")
                else:
                    values.append(str(value))
            rows.append(values)

        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        lines.extend("| " + " | ".join(values) + " |" for values in rows)
        return "\n".join(lines)

    lines = [
        "# Model Comparison",
        "",
        "Rolling-origin validation by season. Lower MAE/RMSE is better; higher Spearman is better.",
        "",
        "## Overall Ranking",
        "",
        markdown_table(aggregate),
        "",
        "## Two-Stage Versus Best Direct Model",
        "",
        *comparison_lines,
        "",
        "## Ranking Metrics By Position",
        "",
        markdown_table(ranking_by_position),
        "",
        *diagnostics_markdown_lines(results.attrs.get("diagnostics", {})),
        "",
        "## Results By Validation Season",
        "",
        markdown_table(results),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def markdown_table(frame: pd.DataFrame) -> str:
    headers = list(frame.columns)
    rows = []
    for _, row in frame.iterrows():
        values = []
        for value in row:
            if isinstance(value, float):
                values.append(f"{value:.4f}" if not np.isnan(value) else "")
            else:
                values.append(str(value))
        rows.append(values)

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(values) + " |" for values in rows)
    return "\n".join(lines)


def write_position_results(
    results: pd.DataFrame,
    path: Path = DEFAULT_POSITION_RESULTS_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(path, index=False)


def write_position_markdown_summary(
    results: pd.DataFrame,
    path: Path = DEFAULT_POSITION_SUMMARY_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    overall = (
        results.loc[results["position"] == "ALL"]
        .groupby("strategy", as_index=False)
        .agg(
            seasons=("validation_season", "nunique"),
            mean_mae=("mae", "mean"),
            mean_rmse=("rmse", "mean"),
            mean_spearman=("spearman", "mean"),
            mean_top_10_precision=("top_10_precision", "mean"),
            mean_top_10_avg_actual_points=("top_10_avg_actual_points", "mean"),
            mean_top_20_precision=("top_20_precision", "mean"),
            mean_top_20_avg_actual_points=("top_20_avg_actual_points", "mean"),
            mean_top_50_precision=("top_50_precision", "mean"),
            mean_top_50_avg_actual_points=("top_50_avg_actual_points", "mean"),
        )
        .sort_values(["mean_mae", "strategy"])
    )
    by_position = (
        results.loc[results["position"] != "ALL"]
        .groupby(["strategy", "position"], as_index=False)
        .agg(
            mean_mae=("mae", "mean"),
            mean_rmse=("rmse", "mean"),
            mean_spearman=("spearman", "mean"),
            mean_top_10_precision=("top_10_precision", "mean"),
            mean_top_10_avg_actual_points=("top_10_avg_actual_points", "mean"),
            mean_top_20_precision=("top_20_precision", "mean"),
            mean_top_20_avg_actual_points=("top_20_avg_actual_points", "mean"),
            mean_top_50_precision=("top_50_precision", "mean"),
            mean_top_50_avg_actual_points=("top_50_avg_actual_points", "mean"),
        )
        .sort_values(["position", "mean_mae", "strategy"])
    )
    lines = [
        "# Position Model Comparison",
        "",
        f"Base direct model: {POSITION_STRATEGY_MODEL_NAME}. Rolling-origin validation by season.",
        "",
        "## Overall",
        "",
        markdown_table(overall),
        "",
        "## By Position",
        "",
        markdown_table(by_position),
        "",
        *diagnostics_markdown_lines(results.attrs.get("diagnostics", {})),
        "",
        "## By Validation Season And Position",
        "",
        markdown_table(results),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def aggregate_model_metrics(results: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [
        "mae",
        "rmse",
        "spearman",
        "top_10_precision",
        "top_20_precision",
        "top_50_precision",
    ]
    available = [column for column in metric_columns if column in results.columns]
    return results.groupby("model", as_index=False)[available].mean()


def aggregate_position_strategy_metrics(results: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [
        "mae",
        "rmse",
        "spearman",
        "top_10_precision",
        "top_20_precision",
        "top_50_precision",
    ]
    available = [column for column in metric_columns if column in results.columns]
    return (
        results.loc[results["position"] == "ALL"]
        .groupby("strategy", as_index=False)[available]
        .mean()
    )


def comparison_table(
    full: pd.DataFrame,
    filtered: pd.DataFrame,
    *,
    key_column: str,
    names: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    metrics = [
        "mae",
        "rmse",
        "spearman",
        "top_10_precision",
        "top_20_precision",
        "top_50_precision",
    ]
    full_indexed = full.set_index(key_column)
    filtered_indexed = filtered.set_index(key_column)
    keys = list(names) if names is not None else sorted(set(full_indexed.index) & set(filtered_indexed.index))
    rows: list[dict[str, Any]] = []
    for key in keys:
        if key not in full_indexed.index or key not in filtered_indexed.index:
            continue
        row: dict[str, Any] = {key_column: key}
        for metric in metrics:
            if metric not in full_indexed.columns or metric not in filtered_indexed.columns:
                continue
            before = float(full_indexed.loc[key, metric])
            after = float(filtered_indexed.loc[key, metric])
            row[f"full_{metric}"] = before
            row[f"filtered_{metric}"] = after
            row[f"delta_{metric}"] = after - before
        rows.append(row)
    return pd.DataFrame(rows)


def best_metric_summary(results: pd.DataFrame) -> pd.DataFrame:
    aggregate = aggregate_model_metrics(results)
    metric_specs = {
        "mae": True,
        "rmse": True,
        "spearman": False,
        "top_10_precision": False,
        "top_20_precision": False,
        "top_50_precision": False,
    }
    rows = []
    for metric, lower_is_better in metric_specs.items():
        if metric not in aggregate.columns:
            continue
        sorted_metric = aggregate.sort_values([metric, "model"], ascending=[lower_is_better, True])
        best = sorted_metric.iloc[0]
        rows.append({"metric": metric, "best_model": best["model"], "score": best[metric]})
    return pd.DataFrame(rows)


def best_metric_comparison(full_results: pd.DataFrame, filtered_results: pd.DataFrame) -> pd.DataFrame:
    full_best = best_metric_summary(full_results).set_index("metric")
    filtered_best = best_metric_summary(filtered_results).set_index("metric")
    lower_is_better = {"mae", "rmse"}
    rows = []
    for metric in full_best.index.intersection(filtered_best.index):
        full_score = float(full_best.loc[metric, "score"])
        filtered_score = float(filtered_best.loc[metric, "score"])
        delta = filtered_score - full_score
        improved = delta < 0 if metric in lower_is_better else delta > 0
        rows.append(
            {
                "metric": metric,
                "full_best_model": full_best.loc[metric, "best_model"],
                "full_score": full_score,
                "filtered_best_model": filtered_best.loc[metric, "best_model"],
                "filtered_score": filtered_score,
                "delta": delta,
                "improved": "yes" if improved else "no",
            }
        )
    return pd.DataFrame(rows)


def write_supported_season_filter_report(
    *,
    source: pd.DataFrame,
    full_results: pd.DataFrame,
    filtered_results: pd.DataFrame,
    full_position_results: pd.DataFrame | None,
    filtered_position_results: pd.DataFrame | None,
    min_season: str,
    path: Path = DEFAULT_SUPPORTED_FILTER_REPORT_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    filtered_source = season_filtered_frame(source, min_season)
    diagnostics = season_filter_diagnostics(source, filtered_source, min_season=min_season)
    full_aggregate = aggregate_model_metrics(full_results)
    filtered_aggregate = aggregate_model_metrics(filtered_results)
    focus_models = (
        "residual_CatBoost",
        "residual_XGBoost",
        MINUTES_ADJUSTED_BASELINE_NAME,
    )
    focus_comparison = comparison_table(
        full_aggregate,
        filtered_aggregate,
        key_column="model",
        names=focus_models,
    )
    best_comparison = best_metric_summary(filtered_results)
    metric_comparison = best_metric_comparison(full_results, filtered_results)

    position_lines = ["Position strategy comparison was unavailable."]
    if full_position_results is not None and filtered_position_results is not None:
        full_position = aggregate_position_strategy_metrics(full_position_results)
        filtered_position = aggregate_position_strategy_metrics(filtered_position_results)
        position_comparison = comparison_table(
            full_position,
            filtered_position,
            key_column="strategy",
            names=("global_plus_position_interactions",),
        )
        position_lines = [
            markdown_table(position_comparison)
            if not position_comparison.empty
            else "No comparable position-strategy rows were available."
        ]

    team_strength_columns = [
        "team_elo_pre_gw",
        "opponent_elo_pre_gw",
        "elo_difference",
        "home_adjusted_elo_difference",
        "team_goals_scored_mean_last_5",
        "team_goals_conceded_mean_last_5",
        "opponent_goals_scored_mean_last_5",
        "opponent_goals_conceded_mean_last_5",
        "team_clean_sheet_rate_last_5",
        "opponent_clean_sheet_rate_last_5",
    ]
    coverage_rows = []
    for column in team_strength_columns:
        if column in source.columns:
            coverage_rows.append(
                {
                    "feature": column,
                    "full_non_null_rate": source[column].notna().mean(),
                    "filtered_non_null_rate": filtered_source[column].notna().mean(),
                }
            )
    coverage = pd.DataFrame(coverage_rows)
    excluded_lines = [
        f"- `{season}`: {reason}"
        for season, reason in diagnostics["excluded_season_reasons"].items()
    ] or ["- None"]

    lines = [
        "# Supported-Season Filter Report",
        "",
        f"Minimum season: `{min_season}`.",
        "",
        "## Seasons",
        "",
        f"Included: {', '.join(diagnostics['included_seasons']) or 'none'}",
        "",
        "Excluded:",
        "",
        *excluded_lines,
        "",
        "## Team-Strength Feature Coverage",
        "",
        markdown_table(coverage) if not coverage.empty else "No team-strength feature columns were present.",
        "",
        "## Best Filtered Models",
        "",
        markdown_table(best_comparison),
        "",
        "## Metric-Level Filtering Impact",
        "",
        markdown_table(metric_comparison),
        "",
        "## Full-History Versus Supported-Season Models",
        "",
        "Positive deltas mean the metric increased after filtering; for MAE/RMSE that is worse, "
        "for Spearman and precision that is better.",
        "",
        markdown_table(focus_comparison) if not focus_comparison.empty else "No comparable model rows were available.",
        "",
        "## Global Plus Position Interactions",
        "",
        *position_lines,
        "",
        "## Interpretation",
        "",
        "- Filtering removes early seasons where team and position identifiers are unsupported.",
        "- The supported-season run uses fewer training rows, so worse MAE/RMSE can indicate that reduced history hurts more than cleaner team-strength coverage helps.",
        "- Team-strength features are more consistently available after filtering because the retained seasons have reliable normalized team/opponent IDs.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_team_form_feature_report(
    *,
    before_results: pd.DataFrame | None,
    after_results: pd.DataFrame,
    before_position_results: pd.DataFrame | None,
    after_position_results: pd.DataFrame | None,
    source: pd.DataFrame,
    min_season: str,
    path: Path = DEFAULT_TEAM_FORM_FEATURE_REPORT_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    filtered_source = season_filtered_frame(source, min_season)
    form_columns = [
        "team_goals_scored_mean_last_5",
        "team_goals_conceded_mean_last_5",
        "opponent_goals_scored_mean_last_5",
        "opponent_goals_conceded_mean_last_5",
        "team_clean_sheet_rate_last_5",
        "opponent_clean_sheet_rate_last_5",
    ]
    coverage = pd.DataFrame(
        [
            {
                "feature": column,
                "full_non_null_rate": source[column].notna().mean(),
                "supported_non_null_rate": filtered_source[column].notna().mean(),
            }
            for column in form_columns
            if column in source.columns
        ]
    )

    focus_models = (
        "residual_CatBoost",
        "residual_XGBoost",
        MINUTES_ADJUSTED_BASELINE_NAME,
    )
    if before_results is not None:
        model_comparison = comparison_table(
            aggregate_model_metrics(before_results),
            aggregate_model_metrics(after_results),
            key_column="model",
            names=focus_models,
        )
        model_comparison = model_comparison.rename(
            columns=lambda column: column.replace("full_", "before_").replace(
                "filtered_",
                "after_",
            )
        )
    else:
        model_comparison = pd.DataFrame()

    position_comparison = pd.DataFrame()
    if before_position_results is not None and after_position_results is not None:
        position_comparison = comparison_table(
            aggregate_position_strategy_metrics(before_position_results),
            aggregate_position_strategy_metrics(after_position_results),
            key_column="strategy",
            names=("global_plus_position_interactions",),
        )
        position_comparison = position_comparison.rename(
            columns=lambda column: column.replace("full_", "before_").replace(
                "filtered_",
                "after_",
            )
        )

    lines = [
        "# Team Form Feature Report",
        "",
        f"Supported-season comparison uses min-season `{min_season}`.",
        "",
        "## Features Added",
        "",
        *[f"- `{column}`" for column in form_columns],
        "",
        "## Feature Coverage",
        "",
        markdown_table(coverage) if not coverage.empty else "No rolling team form columns were present.",
        "",
        "## Model Comparison",
        "",
        "Positive deltas mean the metric increased after adding team form; for MAE/RMSE that is worse, "
        "for Spearman and precision that is better.",
        "",
        markdown_table(model_comparison)
        if not model_comparison.empty
        else "No previous supported-season result was available for comparison.",
        "",
        "## Global Plus Position Interactions",
        "",
        markdown_table(position_comparison)
        if not position_comparison.empty
        else "No comparable position-strategy result was available.",
        "",
        "## Notes",
        "",
        "- Rolling form is shifted by team-season gameweek, so GW t never uses GW t goals or clean-sheet outcomes.",
        "- Opponent form is joined from the opponent's normalized team ID in the same season and gameweek.",
        "- Unsupported seasons remain missing rather than being imputed from unreliable team identifiers.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def focus_model_specs(specs: list[SklearnModelSpec], names: tuple[str, ...]) -> list[SklearnModelSpec]:
    wanted = set(names)
    return [spec for spec in specs if spec.name in wanted]


def _ensemble_candidate_predictions(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    direct_specs: list[SklearnModelSpec],
    residual_specs: list[SklearnModelSpec],
) -> pd.DataFrame:
    train_model = train.dropna(subset=[TARGET_COLUMN]).copy()
    validation_model = validation.dropna(subset=[TARGET_COLUMN]).copy()
    predictions = pd.DataFrame(index=validation_model.index)
    predictions["actual"] = validation_model[TARGET_COLUMN]
    if POSITION_COLUMN in validation_model.columns:
        predictions[POSITION_COLUMN] = validation_model[POSITION_COLUMN]

    baseline_by_name = {model.name: model for model in BASELINES}
    for model_name in ENSEMBLE_BASELINE_MODEL_NAMES:
        model = baseline_by_name.get(model_name)
        if model is None:
            continue
        try:
            predictions[model_name] = model.predict(validation_model)
        except (ValueError, KeyError) as exc:
            LOGGER.warning("Skipping ensemble baseline candidate %s: %s", model_name, exc)

    if not train_model.empty and not validation_model.empty:
        columns = feature_columns(train_model)
        x_train = train_model[columns].replace({pd.NA: np.nan})
        y_train = train_model[TARGET_COLUMN]
        x_validation = validation_model[columns].replace({pd.NA: np.nan})
        for spec in direct_specs:
            try:
                pipeline = Pipeline(
                    [
                        (
                            "preprocess",
                            build_preprocessor(train_model, columns, scale_numeric=spec.scale_numeric),
                        ),
                        ("model", clone(spec.estimator)),
                    ]
                )
                pipeline.fit(x_train, y_train)
                predictions[spec.name] = pipeline.predict(x_validation)
            except Exception as exc:  # noqa: BLE001 - optional model libraries raise varied exceptions.
                LOGGER.warning("Skipping ensemble direct candidate %s: %s", spec.name, exc)

    train_with_residual = add_residual_target(train_model, minutes_adjusted_baseline_predictions(train_model))
    validation_with_baseline = validation_model.copy()
    validation_with_baseline[BASELINE_PREDICTION_COLUMN] = minutes_adjusted_baseline_predictions(
        validation_model
    )
    train_residual = train_with_residual.dropna(
        subset=[TARGET_COLUMN, BASELINE_PREDICTION_COLUMN, RESIDUAL_TARGET_COLUMN]
    ).copy()
    validation_residual = validation_with_baseline.dropna(
        subset=[TARGET_COLUMN, BASELINE_PREDICTION_COLUMN]
    ).copy()
    if not train_residual.empty and not validation_residual.empty:
        columns = feature_columns(train_residual)
        x_train = train_residual[columns].replace({pd.NA: np.nan})
        y_train = train_residual[RESIDUAL_TARGET_COLUMN]
        x_validation = validation_residual[columns].replace({pd.NA: np.nan})
        for spec in residual_specs:
            try:
                pipeline = Pipeline(
                    [
                        (
                            "preprocess",
                            build_preprocessor(
                                train_residual,
                                columns,
                                scale_numeric=spec.scale_numeric,
                            ),
                        ),
                        ("model", clone(spec.estimator)),
                    ]
                )
                pipeline.fit(x_train, y_train)
                predicted_residual = pd.Series(
                    pipeline.predict(x_validation),
                    index=validation_residual.index,
                )
                predictions[f"residual_{spec.name}"] = final_residual_prediction(
                    validation_residual[BASELINE_PREDICTION_COLUMN],
                    predicted_residual,
                )
            except Exception as exc:  # noqa: BLE001 - optional model libraries raise varied exceptions.
                LOGGER.warning("Skipping ensemble residual candidate %s: %s", spec.name, exc)

    candidate_columns = [column for column in ENSEMBLE_CANDIDATE_MODELS if column in predictions.columns]
    return predictions[["actual", *([POSITION_COLUMN] if POSITION_COLUMN in predictions.columns else []), *candidate_columns]]


def _rolling_inner_ensemble_predictions(
    data: pd.DataFrame,
    outer_validation_season: str,
    *,
    direct_specs: list[SklearnModelSpec],
    residual_specs: list[SklearnModelSpec],
) -> pd.DataFrame:
    train_history = data.loc[data["season"].astype(str) < str(outer_validation_season)].copy()
    rows: list[pd.DataFrame] = []
    for inner_validation_season in validation_seasons(train_history):
        inner_train, inner_validation = split_train_validation(
            train_history,
            inner_validation_season,
        )
        if inner_train.empty or inner_validation.empty:
            continue
        inner_predictions = _ensemble_candidate_predictions(
            inner_train,
            inner_validation,
            direct_specs=direct_specs,
            residual_specs=residual_specs,
        )
        if inner_predictions.empty:
            continue
        inner_predictions["inner_validation_season"] = inner_validation_season
        rows.append(inner_predictions)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, axis=0, ignore_index=False)


def _score_ensemble_weights(
    predictions: pd.DataFrame,
    target: pd.Series,
    weights: np.ndarray,
    metric: str,
) -> float:
    blended = pd.Series(predictions.to_numpy(dtype=float) @ weights, index=predictions.index)
    if metric == "mae":
        return mae(target, blended)
    if metric == "rmse":
        return rmse(target, blended)
    if metric == "spearman":
        corr = spearman_rank_correlation(target, blended)
        return float("inf") if pd.isna(corr) else -float(corr)
    raise BacktestError(f"Unsupported ensemble optimization metric: {metric}")


def learn_ensemble_weights(
    predictions: pd.DataFrame,
    target: pd.Series,
    *,
    metric: str,
    random_state: int = 42,
    n_random_candidates: int = 120,
) -> dict[str, float]:
    columns = list(predictions.columns)
    if not columns:
        return {}
    valid = pd.concat([target.rename("actual"), predictions], axis=1).dropna()
    if valid.empty:
        equal = 1.0 / len(columns)
        return dict.fromkeys(columns, equal)

    x = valid[columns].apply(pd.to_numeric, errors="coerce")
    y = valid["actual"]
    candidates: list[np.ndarray] = []
    n_columns = len(columns)
    candidates.append(np.full(n_columns, 1.0 / n_columns))
    candidates.extend(np.eye(n_columns))
    rng = np.random.default_rng(random_state)
    if n_columns > 1 and n_random_candidates > 0:
        candidates.extend(rng.dirichlet(np.ones(n_columns), size=n_random_candidates))

    best = min(candidates, key=lambda weights: _score_ensemble_weights(x, y, weights, metric))
    best = np.clip(np.asarray(best, dtype=float), 0.0, None)
    total = best.sum()
    if total <= 0:
        best = np.full(n_columns, 1.0 / n_columns)
    else:
        best = best / total
    return {column: float(weight) for column, weight in zip(columns, best, strict=True)}


def _equal_weights(columns: list[str]) -> dict[str, float]:
    if not columns:
        return {}
    return dict.fromkeys(columns, 1.0 / len(columns))


def _available_members(predictions: pd.DataFrame, members: tuple[str, ...]) -> list[str]:
    return [member for member in members if member in predictions.columns]


def _optimized_or_fallback_weights(
    inner_predictions: pd.DataFrame,
    outer_predictions: pd.DataFrame,
    *,
    members: tuple[str, ...],
    metric: str,
    random_state: int,
) -> tuple[dict[str, float], str]:
    available = _available_members(outer_predictions, members)
    if not available:
        return {}, "unavailable"
    inner_available = [member for member in available if member in inner_predictions.columns]
    if inner_predictions.empty or not inner_available:
        return _equal_weights(available), "fallback_preset"
    weights = learn_ensemble_weights(
        inner_predictions[inner_available],
        inner_predictions["actual"],
        metric=metric,
        random_state=random_state,
    )
    missing = [member for member in available if member not in weights]
    if missing:
        weights = {**weights, **dict.fromkeys(missing, 0.0)}
    total = sum(weights.values())
    if total <= 0:
        return _equal_weights(available), "fallback_preset"
    return {member: weights[member] / total for member in available}, "inner_validation"


def _blend_prediction_columns(predictions: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    columns = list(weights)
    if not columns:
        return pd.Series(np.nan, index=predictions.index, dtype="float64")
    weight_vector = np.asarray([weights[column] for column in columns], dtype=float)
    values = predictions[columns].apply(pd.to_numeric, errors="coerce")
    return pd.Series(
        values.to_numpy(dtype=float) @ weight_vector,
        index=predictions.index,
    )


def _json_weights(weights: dict[str, float]) -> str:
    return json.dumps({key: round(value, 6) for key, value in weights.items()}, sort_keys=True)


def run_ensemble_experiment(
    frame: pd.DataFrame,
    *,
    model_specs: list[SklearnModelSpec] | None = None,
    residual_specs: list[SklearnModelSpec] | None = None,
    random_state: int = 42,
) -> pd.DataFrame:
    validate_dataset(frame)
    data = normalize_position_column(frame.copy())
    data = add_baseline_prediction_features(data)
    data["season"] = data["season"].astype(str)
    data = data.sort_values(["season", "gw"]).reset_index(drop=True)
    direct_specs = focus_model_specs(
        sklearn_model_specs() if model_specs is None else model_specs,
        ENSEMBLE_DIRECT_MODEL_NAMES,
    )
    residual_focus_specs = focus_model_specs(
        residual_model_specs() if residual_specs is None else residual_specs,
        ENSEMBLE_RESIDUAL_MODEL_NAMES,
    )

    rows: list[dict[str, Any]] = []
    for validation_season in validation_seasons(data):
        train, validation = split_train_validation(data, validation_season)
        if train.empty or validation.empty:
            continue
        LOGGER.info("Running ensemble validation season %s.", validation_season)
        outer_predictions = _ensemble_candidate_predictions(
            train,
            validation,
            direct_specs=direct_specs,
            residual_specs=residual_focus_specs,
        )
        inner_predictions = _rolling_inner_ensemble_predictions(
            data,
            validation_season,
            direct_specs=direct_specs,
            residual_specs=residual_focus_specs,
        )

        blend_definitions: dict[str, tuple[dict[str, float], str]] = {}
        if MINUTES_ADJUSTED_BASELINE_NAME in outer_predictions.columns:
            blend_definitions["minutes_adjusted_only"] = (
                {MINUTES_ADJUSTED_BASELINE_NAME: 1.0},
                "fixed",
            )
        top_members = _available_members(outer_predictions, ENSEMBLE_TOP_MODEL_MEMBERS)
        blend_definitions["equal_weight_top_models"] = (
            _equal_weights(top_members),
            "fixed",
        )
        for metric in ("mae", "rmse", "spearman"):
            weights, source = _optimized_or_fallback_weights(
                inner_predictions,
                outer_predictions,
                members=ENSEMBLE_CANDIDATE_MODELS,
                metric=metric,
                random_state=random_state,
            )
            blend_definitions[f"optimized_{metric}_blend"] = (weights, source)
        weights, source = _optimized_or_fallback_weights(
            inner_predictions,
            outer_predictions,
            members=ENSEMBLE_BASELINE_RESIDUAL_MEMBERS,
            metric="mae",
            random_state=random_state,
        )
        blend_definitions["baseline_plus_residual_boost_blend"] = (weights, source)

        y_true = outer_predictions["actual"]
        positions = outer_predictions[POSITION_COLUMN] if POSITION_COLUMN in outer_predictions.columns else None
        for model_name in [model for model in ENSEMBLE_CANDIDATE_MODELS if model in outer_predictions.columns]:
            row = evaluate_predictions(
                model_name=model_name,
                validation_season=validation_season,
                y_true=y_true,
                y_pred=outer_predictions[model_name],
                positions=positions,
            )
            row["n_train"] = len(train)
            row["blend_type"] = "base_model_reference"
            row["blend_members"] = model_name
            row["weights_json"] = _json_weights({model_name: 1.0})
            row["weight_source"] = "reference"
            rows.append(row)

        for blend_name, (weights, source) in blend_definitions.items():
            if not weights:
                continue
            y_pred = _blend_prediction_columns(outer_predictions, weights)
            row = evaluate_predictions(
                model_name=blend_name,
                validation_season=validation_season,
                y_true=y_true,
                y_pred=y_pred,
                positions=positions,
            )
            row["n_train"] = len(train)
            row["blend_type"] = "ensemble"
            row["blend_members"] = ", ".join(weights)
            row["weights_json"] = _json_weights(weights)
            row["weight_source"] = source
            rows.append(row)

    if not rows:
        raise BacktestError("No ensemble experiment results were produced.")
    return pd.DataFrame(rows).sort_values(["validation_season", "blend_type", "model"]).reset_index(drop=True)


def write_ensemble_results(
    results: pd.DataFrame,
    path: Path = DEFAULT_ENSEMBLE_RESULTS_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(path, index=False)


def write_ensemble_report(
    results: pd.DataFrame,
    path: Path = DEFAULT_ENSEMBLE_REPORT_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    metrics = ["mae", "rmse", "spearman", "top_10_precision", "top_20_precision", "top_50_precision"]
    aggregate = results.groupby(["blend_type", "model"], as_index=False)[metrics].mean()
    ensembles = aggregate.loc[aggregate["blend_type"] == "ensemble"].copy()
    weights = results.loc[
        results["blend_type"].eq("ensemble"),
        ["validation_season", "model", "blend_members", "weights_json", "weight_source"],
    ].sort_values(["validation_season", "model"])

    best_lines = []
    for metric in metrics:
        ascending = metric in {"mae", "rmse"}
        best = ensembles.sort_values(metric, ascending=ascending).iloc[0]
        best_lines.append(
            {
                "metric": metric,
                "best_ensemble": best["model"],
                "value": best[metric],
            }
        )
    best_table = pd.DataFrame(best_lines)
    reference = aggregate.loc[aggregate["blend_type"] == "base_model_reference"]
    minutes_mae = reference.loc[
        reference["model"].eq(MINUTES_ADJUSTED_BASELINE_NAME),
        "mae",
    ]
    residual_catboost_rmse = reference.loc[reference["model"].eq("residual_CatBoost"), "rmse"]
    best_ensemble_mae = ensembles["mae"].min()
    best_ensemble_rmse = ensembles["rmse"].min()
    best_top_k = {
        metric: ensembles[metric].max()
        for metric in ("top_10_precision", "top_20_precision", "top_50_precision")
    }
    reference_top_k = {
        metric: reference[metric].max()
        for metric in ("top_10_precision", "top_20_precision", "top_50_precision")
    }

    recommendation = "Keep the strongest single models as default."
    if not minutes_mae.empty and best_ensemble_mae < float(minutes_mae.iloc[0]):
        recommendation = "Consider the best MAE ensemble for a follow-up default-model test."
    elif any(best_top_k[metric] > reference_top_k[metric] for metric in best_top_k):
        recommendation = "Keep the ensemble as a ranking specialist candidate only."

    lines = [
        "# Ensemble Experiment",
        "",
        "Opt-in rolling-origin experiment for convex weighted blends. Weights are "
        "non-negative, sum to 1, and are chosen from prior training-season "
        "inner-validation predictions only. The held-out validation season is never "
        "used to choose weights.",
        "",
        "## Blend Members And Weights",
        "",
        markdown_table(weights),
        "",
        "## Aggregate Results",
        "",
        markdown_table(aggregate.sort_values(["blend_type", "mae", "model"])),
        "",
        "## Best Ensembles",
        "",
        markdown_table(best_table),
        "",
        "## Checks",
        "",
        f"- Any ensemble beats `{MINUTES_ADJUSTED_BASELINE_NAME}` on MAE: "
        f"{'yes' if not minutes_mae.empty and best_ensemble_mae < float(minutes_mae.iloc[0]) else 'no'}.",
        "- Any ensemble beats `residual_CatBoost` on RMSE: "
        f"{'yes' if not residual_catboost_rmse.empty and best_ensemble_rmse < float(residual_catboost_rmse.iloc[0]) else 'no'}.",
        "- Any ensemble improves top-k precision over the best base candidate: "
        f"{'yes' if any(best_top_k[metric] > reference_top_k[metric] for metric in best_top_k) else 'no'}.",
        "",
        "## Recommendation",
        "",
        recommendation,
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _as_bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def load_position_feature_masks(
    path: Path = DEFAULT_POSITION_FEATURE_RELEVANCE_PATH,
    *,
    max_features_per_position: int = 20,
) -> dict[str, tuple[str, ...]]:
    if not path.exists():
        raise BacktestError(
            f"Position feature relevance file not found: {path}. "
            "Run evaluation.position_feature_relevance first."
        )
    relevance = pd.read_csv(path)
    required_columns = {
        "position",
        "feature",
        "non_missing_pct",
        "spearman",
        "mutual_information",
        "useful_in_at_least_2_of_3",
        "high_missingness",
        "relevance_score",
    }
    missing = required_columns.difference(relevance.columns)
    if missing:
        raise BacktestError(f"Position feature relevance file is missing columns: {sorted(missing)}")

    relevance = relevance.copy()
    relevance["useful_in_at_least_2_of_3"] = _as_bool_series(
        relevance["useful_in_at_least_2_of_3"]
    )
    relevance["high_missingness"] = _as_bool_series(relevance["high_missingness"])
    masks: dict[str, tuple[str, ...]] = {}
    forbidden = {*RAW_CURRENT_GW_OUTCOME_COLUMNS, *RAW_TEAM_COLUMNS, TARGET_COLUMN, "next_3_gw_points"}
    for position in RANKING_POSITIONS:
        rows = relevance.loc[
            relevance["position"].astype(str).eq(position)
            & relevance["high_missingness"].eq(False)
            & ~relevance["feature"].isin(forbidden)
            & (
                relevance["useful_in_at_least_2_of_3"].eq(True)
                | relevance["spearman"].abs().ge(0.05)
                | relevance["mutual_information"].ge(0.01)
            )
        ].sort_values(["relevance_score", "non_missing_pct"], ascending=[False, False])
        masks[position] = tuple(rows["feature"].head(max_features_per_position))
    return masks


def _position_mask_predictions(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    spec: SklearnModelSpec,
    masks: dict[str, tuple[str, ...]],
    *,
    target_column: str,
    baseline_column: str | None = None,
) -> tuple[pd.Series, int]:
    predictions = pd.Series(index=validation.index, dtype="float64")
    n_train = 0
    for position, validation_position in validation.groupby(POSITION_COLUMN, dropna=False):
        position_key = str(position)
        mask_columns = masks.get(position_key, ())
        if not mask_columns:
            continue
        train_position = train.loc[train[POSITION_COLUMN].astype(str) == position_key].copy()
        validation_position = validation_position.copy()
        train_position = train_position.dropna(subset=[target_column])
        validation_position = validation_position.dropna(subset=[TARGET_COLUMN])
        if train_position.empty or validation_position.empty:
            continue
        columns = feature_columns(train_position, mask_columns)
        pipeline = Pipeline(
            [
                (
                    "preprocess",
                    build_preprocessor(train_position, columns, scale_numeric=spec.scale_numeric),
                ),
                ("model", clone(spec.estimator)),
            ]
        )
        pipeline.fit(train_position[columns].replace({pd.NA: np.nan}), train_position[target_column])
        raw_prediction = pd.Series(
            pipeline.predict(validation_position[columns].replace({pd.NA: np.nan})),
            index=validation_position.index,
        )
        if baseline_column is not None:
            raw_prediction = final_residual_prediction(
                validation_position[baseline_column].astype(float),
                raw_prediction.astype(float),
            )
            raw_prediction = pd.Series(
                raw_prediction.to_numpy(dtype=float),
                index=validation_position.index,
            )
        predictions.loc[validation_position.index] = raw_prediction
        n_train += len(train_position)
    return predictions, n_train


def _evaluate_position_masked_models(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    validation_season: str,
    masks: dict[str, tuple[str, ...]],
    direct_specs: list[SklearnModelSpec],
    residual_specs: list[SklearnModelSpec],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    validation_model = validation.dropna(subset=[TARGET_COLUMN, POSITION_COLUMN]).copy()
    train_model = train.dropna(subset=[TARGET_COLUMN, POSITION_COLUMN]).copy()
    if train_model.empty or validation_model.empty:
        return rows

    for spec in direct_specs:
        try:
            y_pred, n_train = _position_mask_predictions(
                train_model,
                validation_model,
                spec,
                masks,
                target_column=TARGET_COLUMN,
            )
            row = evaluate_predictions(
                model_name=spec.name,
                validation_season=validation_season,
                y_true=validation_model[TARGET_COLUMN],
                y_pred=y_pred,
                positions=validation_model[POSITION_COLUMN],
            )
            row["n_train"] = n_train
            rows.append(row)
        except Exception as exc:  # noqa: BLE001 - model libraries raise varied exception types.
            LOGGER.warning("Skipping masked model %s for %s: %s", spec.name, validation_season, exc)

    train_residual = add_residual_target(train_model, minutes_adjusted_baseline_predictions(train_model))
    validation_residual = validation_model.copy()
    validation_residual[BASELINE_PREDICTION_COLUMN] = minutes_adjusted_baseline_predictions(
        validation_residual
    )
    train_residual = train_residual.dropna(
        subset=[TARGET_COLUMN, BASELINE_PREDICTION_COLUMN, RESIDUAL_TARGET_COLUMN]
    )
    validation_residual = validation_residual.dropna(subset=[TARGET_COLUMN, BASELINE_PREDICTION_COLUMN])
    for spec in residual_specs:
        try:
            y_pred, n_train = _position_mask_predictions(
                train_residual,
                validation_residual,
                spec,
                masks,
                target_column=RESIDUAL_TARGET_COLUMN,
                baseline_column=BASELINE_PREDICTION_COLUMN,
            )
            row = evaluate_predictions(
                model_name=f"residual_{spec.name}",
                validation_season=validation_season,
                y_true=validation_residual[TARGET_COLUMN],
                y_pred=y_pred,
                positions=validation_residual[POSITION_COLUMN],
            )
            row["n_train"] = n_train
            rows.append(row)
        except Exception as exc:  # noqa: BLE001 - model libraries raise varied exception types.
            LOGGER.warning(
                "Skipping masked residual model %s for %s: %s",
                spec.name,
                validation_season,
                exc,
            )
    return rows


def _evaluate_position_masked_strategies(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    validation_season: str,
    masks: dict[str, tuple[str, ...]],
    estimator: Any,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    train_model = train.dropna(subset=[TARGET_COLUMN, POSITION_COLUMN]).copy()
    validation_model = validation.dropna(subset=[TARGET_COLUMN, POSITION_COLUMN]).copy()
    if train_model.empty or validation_model.empty:
        return rows

    predictions = pd.DataFrame(index=validation_model.index)
    for position, validation_position in validation_model.groupby(POSITION_COLUMN, dropna=False):
        position_key = str(position)
        mask_columns = masks.get(position_key, ())
        if not mask_columns:
            continue
        configured = dedupe_columns([POSITION_COLUMN, *mask_columns])
        predictions.loc[validation_position.index, "global_plus_position_interactions"] = (
            fit_predict_direct_model(
                train_model,
                validation_position,
                estimator=estimator,
                include_position=True,
                add_interactions=True,
                configured_columns=configured,
            )
        )
        train_position = train_model.loc[train_model[POSITION_COLUMN].astype(str) == position_key]
        if len(train_position) < MIN_POSITION_TRAIN_ROWS:
            predictions.loc[validation_position.index, "position_wise_models"] = (
                fit_predict_direct_model(
                    train_model,
                    validation_position,
                    estimator=estimator,
                    include_position=True,
                    add_interactions=False,
                    configured_columns=configured,
                )
            )
        else:
            predictions.loc[validation_position.index, "position_wise_models"] = (
                fit_predict_direct_model(
                    train_position,
                    validation_position,
                    estimator=estimator,
                    include_position=False,
                    add_interactions=False,
                    configured_columns=mask_columns,
                )
            )

    for strategy in ("global_plus_position_interactions", "position_wise_models"):
        row = evaluate_predictions(
            model_name=strategy,
            validation_season=validation_season,
            y_true=validation_model[TARGET_COLUMN],
            y_pred=predictions[strategy],
            positions=validation_model[POSITION_COLUMN],
        )
        row["n_train"] = len(train_model)
        rows.append(row)
    return rows


def _current_position_mask_control_rows(
    frame: pd.DataFrame,
    *,
    direct_specs: list[SklearnModelSpec],
    residual_specs: list[SklearnModelSpec],
) -> pd.DataFrame:
    standard = run_backtest(
        frame,
        model_specs=direct_specs,
        residual_specs=residual_specs,
        include_two_stage=False,
    )
    standard = standard.loc[standard["model"].isin(POSITION_FEATURE_MASK_FOCUS_MODELS)].copy()
    position_results = run_position_model_backtest(
        frame,
        estimator=clone(direct_specs[0].estimator),
    )
    position_rows = _position_strategy_window_rows(position_results)
    current = pd.concat([standard, position_rows], ignore_index=True, sort=False)
    current = current.loc[current["model"].isin(POSITION_FEATURE_MASK_FOCUS_MODELS)].copy()
    current.insert(0, "feature_setup", "current")
    return current


def run_position_feature_mask_experiment(
    frame: pd.DataFrame,
    *,
    relevance_path: Path = DEFAULT_POSITION_FEATURE_RELEVANCE_PATH,
    model_specs: list[SklearnModelSpec] | None = None,
    residual_specs: list[SklearnModelSpec] | None = None,
) -> pd.DataFrame:
    masks = load_position_feature_masks(relevance_path)
    direct_specs = focus_model_specs(
        sklearn_model_specs() if model_specs is None else model_specs,
        POSITION_FEATURE_MASK_DIRECT_MODEL_NAMES,
    )
    unmasked_direct_specs = focus_model_specs(
        sklearn_model_specs() if model_specs is None else model_specs,
        POSITION_FEATURE_MASK_UNMASKED_DIRECT_MODEL_NAMES,
    )
    residual_focus_specs = focus_model_specs(
        residual_model_specs() if residual_specs is None else residual_specs,
        POSITION_FEATURE_MASK_RESIDUAL_MODEL_NAMES,
    )
    unmasked_residual_specs = focus_model_specs(
        residual_model_specs() if residual_specs is None else residual_specs,
        POSITION_FEATURE_MASK_UNMASKED_RESIDUAL_MODEL_NAMES,
    )
    current = _current_position_mask_control_rows(
        frame,
        direct_specs=[*direct_specs, *unmasked_direct_specs],
        residual_specs=[*residual_focus_specs, *unmasked_residual_specs],
    )

    data = add_baseline_prediction_features(normalize_position_column(frame))
    data["season"] = data["season"].astype(str)
    data = data.sort_values(["season", "gw"]).reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for season in validation_seasons(data):
        train, validation = split_train_validation(data, season)
        if train.empty or validation.empty:
            continue
        baseline_rows = evaluate_baselines(
            validation,
            validation_season=season,
            models=tuple(model for model in BASELINES if model.name == MINUTES_ADJUSTED_BASELINE_NAME),
        )
        rows.extend(baseline_rows)
        rows.extend(
            _evaluate_position_masked_models(
                train,
                validation,
                validation_season=season,
                masks=masks,
                direct_specs=direct_specs,
                residual_specs=residual_focus_specs,
            )
        )
        rows.extend(
            _evaluate_position_masked_strategies(
                train,
                validation,
                validation_season=season,
                masks=masks,
                estimator=clone(direct_specs[0].estimator),
            )
        )
    masked = pd.DataFrame(rows)
    masked = masked.loc[masked["model"].isin(POSITION_FEATURE_MASK_MASKED_MODELS)].copy()
    masked.insert(0, "feature_setup", "model_specific_position_masks")
    unmasked = current.loc[
        current["model"].isin(POSITION_FEATURE_MASK_UNMASKED_MODELS)
    ].copy()
    unmasked["feature_setup"] = "model_specific_position_masks"
    results = pd.concat([current, masked, unmasked], ignore_index=True, sort=False)
    results.attrs["position_feature_masks"] = masks
    results.attrs["masked_model_policy"] = {
        "masked_models": POSITION_FEATURE_MASK_MASKED_MODELS,
        "unmasked_models": POSITION_FEATURE_MASK_UNMASKED_MODELS,
    }
    return results.sort_values(["feature_setup", "validation_season", "model"]).reset_index(drop=True)


def write_position_feature_mask_results(
    results: pd.DataFrame,
    path: Path = DEFAULT_POSITION_FEATURE_MASK_RESULTS_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(path, index=False)


def _aggregate_feature_mask_results(results: pd.DataFrame) -> pd.DataFrame:
    metrics = ["mae", "rmse", "spearman", "top_10_precision", "top_20_precision", "top_50_precision"]
    available = [metric for metric in metrics if metric in results.columns]
    return results.groupby(["feature_setup", "model"], as_index=False)[available].mean()


def write_position_feature_mask_report(
    results: pd.DataFrame,
    path: Path = DEFAULT_POSITION_FEATURE_MASK_REPORT_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    aggregate = _aggregate_feature_mask_results(results)
    metrics = ["mae", "rmse", "spearman", "top_10_precision", "top_20_precision", "top_50_precision"]
    current = aggregate.loc[aggregate["feature_setup"] == "current"].rename(
        columns={metric: f"current_{metric}" for metric in metrics}
    )
    policy = aggregate.loc[
        aggregate["feature_setup"] == "model_specific_position_masks"
    ].rename(
        columns={metric: f"policy_{metric}" for metric in metrics}
    )
    comparison = current.merge(policy, on="model", how="inner")
    comparison = comparison.drop(columns=["feature_setup_x", "feature_setup_y"], errors="ignore")
    for metric in metrics:
        if f"current_{metric}" in comparison.columns and f"policy_{metric}" in comparison.columns:
            comparison[f"delta_{metric}"] = comparison[f"policy_{metric}"] - comparison[f"current_{metric}"]
    masks = results.attrs.get("position_feature_masks", {})
    policy_attrs = results.attrs.get("masked_model_policy", {})
    policy_rows = pd.DataFrame(
        [
            {
                "policy": "masked",
                "models": ", ".join(policy_attrs.get("masked_models", ())),
            },
            {
                "policy": "unmasked_current_features",
                "models": ", ".join(policy_attrs.get("unmasked_models", ())),
            },
        ]
    )
    mask_rows = pd.DataFrame(
        [
            {
                "position": position,
                "feature_count": len(features),
                "features": ", ".join(features),
            }
            for position, features in masks.items()
        ]
    )
    lines = [
        "# Position Feature Mask Experiment",
        "",
        "Opt-in comparison of the current feature setup against a model-specific "
        "position mask policy derived from `reports/position_feature_relevance.csv` "
        "and the relevance report. No wrapper search, broad ablation, or default "
        "model logic changes are performed.",
        "",
        "Masks are applied only to linear and position-strategy models because the "
        "previous mask experiment showed gains for Ridge, ElasticNet, residual "
        "linear models, `global_plus_position_interactions`, and "
        "`position_wise_models`, while CatBoost/XGBoost results were mixed or "
        "harmful. Boosted models and the minutes-adjusted rolling-mean baseline "
        "therefore keep the current feature setup in this experiment.",
        "",
        "## Model-Specific Policy",
        "",
        markdown_table(policy_rows),
        "",
        "## Position Masks",
        "",
        markdown_table(mask_rows),
        "",
        "## Aggregate Comparison",
        "",
        "Negative MAE/RMSE deltas are better. Positive Spearman and top-k deltas are better.",
        "",
        markdown_table(comparison.sort_values(["delta_mae", "model"]) if "delta_mae" in comparison.columns else comparison),
        "",
        "## Recommendation",
        "",
        "Use this as a screening experiment only. Promote a mask only if it improves the target "
        "metric across rolling validation seasons and does not degrade the baseline comparison.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_broad_feature_ablation(
    frame: pd.DataFrame,
    *,
    min_season: str,
    model_specs: list[SklearnModelSpec] | None = None,
    residual_specs: list[SklearnModelSpec] | None = None,
) -> pd.DataFrame:
    configs = ablation_feature_configurations()
    direct_specs = focus_model_specs(
        sklearn_model_specs() if model_specs is None else model_specs,
        FOCUS_DIRECT_MODEL_NAMES,
    )
    residual_focus_specs = focus_model_specs(
        residual_model_specs() if residual_specs is None else residual_specs,
        FOCUS_RESIDUAL_MODEL_NAMES,
    )

    rows: list[pd.DataFrame] = []
    for feature_group, configured_columns in configs.items():
        LOGGER.info("Running broad feature ablation group %s.", feature_group)
        results = run_backtest(
            frame,
            model_specs=direct_specs,
            residual_specs=residual_focus_specs,
            min_season=min_season,
            configured_columns=configured_columns,
            include_two_stage=False,
        )
        focus_models = {
            "Ridge",
            "CatBoost",
            "XGBoost",
            "residual_Ridge",
            "residual_CatBoost",
            "residual_XGBoost",
            MINUTES_ADJUSTED_BASELINE_NAME,
        }
        model_rows = results.loc[results["model"].isin(focus_models)].copy()
        model_rows["feature_group"] = feature_group
        model_rows["result_type"] = "model"
        rows.append(model_rows)

        position_results = run_position_model_backtest(
            frame,
            min_season=min_season,
            configured_columns=configured_columns,
        )
        position_rows = position_results.loc[
            (position_results["strategy"] == "global_plus_position_interactions")
            & (position_results["position"] == "ALL")
        ].copy()
        position_rows = position_rows.rename(columns={"strategy": "model"})
        position_rows["feature_group"] = feature_group
        position_rows["result_type"] = "position_strategy"
        rows.append(position_rows)

    if not rows:
        raise BacktestError("No broad feature ablation rows were produced.")
    return pd.concat(rows, ignore_index=True, sort=False)


def write_broad_feature_ablation_results(
    results: pd.DataFrame,
    path: Path = DEFAULT_BROAD_ABLATION_RESULTS_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(path, index=False)


def _ablation_aggregate(results: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [
        "mae",
        "rmse",
        "spearman",
        "top_10_precision",
        "top_20_precision",
        "top_50_precision",
    ]
    return (
        results.groupby(["feature_group", "model"], as_index=False)[metric_columns]
        .mean()
        .sort_values(["mae", "feature_group", "model"])
    )


def _best_feature_groups_by_metric(results: pd.DataFrame) -> pd.DataFrame:
    group_metrics = (
        results.groupby("feature_group", as_index=False)
        .agg(
            mae=("mae", "mean"),
            rmse=("rmse", "mean"),
            spearman=("spearman", "mean"),
            top_10_precision=("top_10_precision", "mean"),
            top_20_precision=("top_20_precision", "mean"),
            top_50_precision=("top_50_precision", "mean"),
        )
    )
    metric_specs = {
        "mae": True,
        "rmse": True,
        "spearman": False,
        "top_10_precision": False,
        "top_20_precision": False,
        "top_50_precision": False,
    }
    rows = []
    for metric, lower_is_better in metric_specs.items():
        best = group_metrics.sort_values(
            [metric, "feature_group"],
            ascending=[lower_is_better, True],
        ).iloc[0]
        rows.append(
            {
                "metric": metric,
                "best_feature_group": best["feature_group"],
                "score": best[metric],
            }
        )
    return pd.DataFrame(rows)


def _feature_group_delta_summary(results: pd.DataFrame) -> pd.DataFrame:
    aggregate = _ablation_aggregate(results)
    current = aggregate.loc[aggregate["feature_group"] == "current_stable"].set_index("model")
    rows = []
    for _, row in aggregate.loc[aggregate["feature_group"] != "current_stable"].iterrows():
        model = row["model"]
        if model not in current.index:
            continue
        rows.append(
            {
                "feature_group": row["feature_group"],
                "model": model,
                "delta_mae": row["mae"] - current.loc[model, "mae"],
                "delta_rmse": row["rmse"] - current.loc[model, "rmse"],
                "delta_spearman": row["spearman"] - current.loc[model, "spearman"],
                "delta_top_10_precision": (
                    row["top_10_precision"] - current.loc[model, "top_10_precision"]
                ),
                "delta_top_20_precision": (
                    row["top_20_precision"] - current.loc[model, "top_20_precision"]
                ),
                "delta_top_50_precision": (
                    row["top_50_precision"] - current.loc[model, "top_50_precision"]
                ),
            }
        )
    return pd.DataFrame(rows)


def write_broad_feature_ablation_report(
    results: pd.DataFrame,
    path: Path = DEFAULT_BROAD_ABLATION_REPORT_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    aggregate = _ablation_aggregate(results)
    best_groups = _best_feature_groups_by_metric(results)
    deltas = _feature_group_delta_summary(results)
    group_help = pd.DataFrame()
    if not deltas.empty:
        group_help = (
            deltas.groupby("feature_group", as_index=False)
            .agg(
                mean_delta_mae=("delta_mae", "mean"),
                mean_delta_rmse=("delta_rmse", "mean"),
                mean_delta_spearman=("delta_spearman", "mean"),
                mean_delta_top_10_precision=("delta_top_10_precision", "mean"),
                mean_delta_top_20_precision=("delta_top_20_precision", "mean"),
                mean_delta_top_50_precision=("delta_top_50_precision", "mean"),
            )
            .sort_values(["mean_delta_mae", "feature_group"])
        )
    lines = [
        "# Broad Feature Ablation Report",
        "",
        "Supported-season feature ablation using rolling-origin validation.",
        "",
        "## Best Feature Group By Metric",
        "",
        markdown_table(best_groups),
        "",
        "## Aggregate By Feature Group And Model",
        "",
        markdown_table(aggregate),
        "",
        "## Delta Versus Current Stable",
        "",
        "Negative MAE/RMSE deltas help. Positive Spearman and precision deltas help.",
        "",
        markdown_table(deltas),
        "",
        "## Feature Groups That Consistently Help Or Hurt",
        "",
        markdown_table(group_help),
        "",
        "## All Safe Candidates",
        "",
        "Compare `all_safe_candidates` against `current_stable` in the delta table. "
        "A lower MAE/RMSE with stable or higher ranking metrics suggests improvement; "
        "worse error with mixed ranking suggests overfitting or redundant features.",
        "",
        "## Recommended Default Feature Set",
        "",
        "Use the lowest-error feature group that does not materially reduce Spearman or top-k "
        "precision. Keep `minutes_adjusted_rolling_mean` as the baseline reference.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def fit_predict_selected_ridge(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    selected_columns: list[str],
) -> pd.Series:
    usable = feature_columns(train, tuple(selected_columns))
    train_model = train.dropna(subset=[TARGET_COLUMN]).copy()
    validation_model = validation.dropna(subset=[TARGET_COLUMN]).copy()
    pipeline = Pipeline(
        [
            ("preprocess", build_preprocessor(train_model, usable, scale_numeric=True)),
            ("model", Ridge(alpha=1.0)),
        ]
    )
    pipeline.fit(train_model[usable].replace({pd.NA: np.nan}), train_model[TARGET_COLUMN])
    return pd.Series(
        pipeline.predict(validation_model[usable].replace({pd.NA: np.nan})),
        index=validation_model.index,
    )


def run_feature_selection_experiment(
    frame: pd.DataFrame,
    *,
    min_season: str,
    random_state: int = 42,
    min_position_rows: int = MIN_POSITION_SELECTION_ROWS,
) -> pd.DataFrame:
    validate_dataset(frame)
    data = season_filtered_frame(frame, min_season)
    validate_dataset(data)
    data["season"] = data["season"].astype(str)
    data = normalize_position_column(data)
    data = add_baseline_prediction_features(data)
    data = data.sort_values(["season", "gw"]).reset_index(drop=True)

    rows: list[dict[str, Any]] = []
    for season in validation_seasons(data):
        train, validation = split_train_validation(data, season)
        if train.empty or validation.empty:
            continue
        train = train.dropna(subset=[TARGET_COLUMN]).copy()
        validation = validation.dropna(subset=[TARGET_COLUMN]).copy()
        if train.empty or validation.empty:
            continue

        base_candidates = feature_selection_candidate_columns(train)
        base_numeric = numeric_feature_candidates(train, base_candidates)
        train_positions = sorted(train[POSITION_COLUMN].dropna().astype(str).unique())
        train_interactions, interaction_candidates = add_numeric_position_interactions(
            train,
            base_numeric,
            positions=train_positions,
        )
        validation_interactions, _ = add_numeric_position_interactions(
            validation,
            base_numeric,
            positions=train_positions,
        )

        global_selected = select_features_elasticnet(
            train_interactions,
            tuple(interaction_candidates),
            random_state=random_state,
        )
        if not global_selected:
            global_selected = base_numeric[:5]
        global_pred = fit_predict_selected_ridge(
            train_interactions,
            validation_interactions,
            global_selected,
        )
        row = evaluate_predictions(
            model_name="global_selected_features",
            validation_season=season,
            y_true=validation_interactions[TARGET_COLUMN],
            y_pred=global_pred,
            positions=validation_interactions.get(POSITION_COLUMN),
        )
        row["n_train"] = len(train)
        row["selection_method"] = "elasticnet"
        row["selected_features"] = ",".join(global_selected)
        row["position"] = "ALL"
        rows.append(row)

        position_predictions = pd.Series(index=validation.index, dtype="float64")
        hybrid_predictions = pd.Series(index=validation.index, dtype="float64")
        selected_by_position: dict[str, list[str]] = {}
        hybrid_by_position: dict[str, list[str]] = {}
        global_core = global_selected[: min(15, len(global_selected))]
        for position, validation_position in validation.groupby(POSITION_COLUMN, dropna=False):
            position_key = str(position)
            validation_index = validation_position.index
            train_position = train.loc[train[POSITION_COLUMN].astype(str) == position_key]
            if len(train_position) < min_position_rows:
                position_predictions.loc[validation_index] = global_pred.loc[validation_index]
                hybrid_predictions.loc[validation_index] = global_pred.loc[validation_index]
                selected_by_position[position_key] = global_selected
                hybrid_by_position[position_key] = global_selected
                continue

            position_candidates = numeric_feature_candidates(train_position, base_candidates)
            position_selected = select_features_elasticnet(
                train_position,
                tuple(position_candidates),
                random_state=random_state,
            )
            if not position_selected:
                position_selected = global_selected
            selected_by_position[position_key] = position_selected
            position_predictions.loc[validation_index] = fit_predict_selected_ridge(
                train_position,
                validation_position,
                position_selected,
            )

            position_extras = [
                feature
                for feature in position_selected
                if feature not in global_core
            ][:10]
            hybrid_features = list(dedupe_columns([*global_core, *position_extras]))
            hybrid_by_position[position_key] = hybrid_features
            hybrid_predictions.loc[validation_index] = fit_predict_selected_ridge(
                train_position,
                validation_position,
                hybrid_features,
            )

        for strategy, predictions, selected in (
            ("position_selected_features", position_predictions, selected_by_position),
            ("hybrid_global_plus_position_features", hybrid_predictions, hybrid_by_position),
        ):
            metric = evaluate_predictions(
                model_name=strategy,
                validation_season=season,
                y_true=validation[TARGET_COLUMN],
                y_pred=predictions,
                positions=validation.get(POSITION_COLUMN),
            )
            metric["n_train"] = len(train)
            metric["selection_method"] = "elasticnet"
            metric["selected_features"] = json_dumps_selected_features(selected)
            metric["position"] = "BY_POSITION"
            rows.append(metric)

    if not rows:
        raise BacktestError("No feature selection experiment rows were produced.")
    results = pd.DataFrame(rows).sort_values(
        ["validation_season", "model"],
    ).reset_index(drop=True)
    results.attrs["feature_selections"] = collect_feature_selection_counts(results)
    return results


def json_dumps_selected_features(selected: dict[str, list[str]]) -> str:
    import json

    return json.dumps(selected, sort_keys=True)


def collect_feature_selection_counts(results: pd.DataFrame) -> dict[str, int]:
    import json

    counts: dict[str, int] = {}
    for value in results["selected_features"].dropna():
        if not isinstance(value, str):
            continue
        if value.startswith("{"):
            parsed = json.loads(value)
            features = [feature for values in parsed.values() for feature in values]
        else:
            features = [feature for feature in value.split(",") if feature]
        for feature in features:
            counts[feature] = counts.get(feature, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def write_feature_selection_results(
    results: pd.DataFrame,
    path: Path = DEFAULT_FEATURE_SELECTION_RESULTS_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(path, index=False)


def write_feature_selection_report(
    results: pd.DataFrame,
    path: Path = DEFAULT_FEATURE_SELECTION_REPORT_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    aggregate = aggregate_model_metrics(results)
    best = best_metric_summary(results)
    counts = collect_feature_selection_counts(results)
    count_frame = pd.DataFrame(
        [{"feature": feature, "selected_count": count} for feature, count in counts.items()]
    )
    all_candidates = set(feature for columns in feature_selection_candidate_groups().values() for feature in columns)
    selected_features = set(counts)
    rejected = pd.DataFrame(
        [{"feature": feature} for feature in sorted(all_candidates - selected_features)]
    )
    global_rows = results.loc[results["model"] == "global_selected_features"]
    position_rows = results.loc[results["model"] == "position_selected_features"]
    hybrid_rows = results.loc[results["model"] == "hybrid_global_plus_position_features"]

    lines = [
        "# Feature Selection Report",
        "",
        "Feature selection is fitted inside each rolling-origin training window only.",
        "",
        "## Method Used",
        "",
        "- Primary reported method: ElasticNet coefficient selection with standardized numeric features.",
        "- Additional implemented methods: permutation importance and group forward selection.",
        "- Combined score for group forward selection: `MAE + RMSE - Spearman` on an internal training-season validation split.",
        "",
        "## Selected Global Features",
        "",
        markdown_table(global_rows[["validation_season", "selected_features"]]),
        "",
        "## Selected Features By Position",
        "",
        markdown_table(position_rows[["validation_season", "selected_features"]]),
        "",
        "## Hybrid Global Plus Position-Specific Features",
        "",
        markdown_table(hybrid_rows[["validation_season", "selected_features"]]),
        "",
        "## Features Selected Most Often",
        "",
        markdown_table(count_frame.head(50)),
        "",
        "## Features Consistently Rejected",
        "",
        markdown_table(rejected),
        "",
        "## Aggregate Strategy Results",
        "",
        markdown_table(aggregate),
        "",
        "## Best Strategy By Metric",
        "",
        markdown_table(best),
        "",
        "## Position-Specific Versus Global",
        "",
        "Compare `position_selected_features` and `hybrid_global_plus_position_features` "
        "against `global_selected_features` in the aggregate table. Lower MAE/RMSE and "
        "higher Spearman/top-k precision indicate improvement.",
        "",
        "## Recommended Default Feature Set",
        "",
        "Do not replace the default model yet. Use the most stable selected features across "
        "folds as the next candidate set for a focused supported-season ablation.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def season_window_definitions() -> dict[str, str | None]:
    return {
        "full_history": None,
        "supported_seasons": "2020-21",
        "rich_feature_seasons": "2022-23",
    }


def season_window_frame(frame: pd.DataFrame, window_name: str) -> pd.DataFrame:
    windows = season_window_definitions()
    if window_name not in windows:
        raise BacktestError(f"Unknown season window: {window_name}")
    return season_filtered_frame(frame, windows[window_name])


def season_window_available(frame: pd.DataFrame, window_name: str) -> bool:
    min_season = season_window_definitions()[window_name]
    if min_season is None:
        return True
    seasons = set(frame["season"].dropna().astype(str))
    return any(season < min_season for season in seasons) or min(seasons, default=min_season) <= min_season


def season_window_fold_summary(frame: pd.DataFrame, window_name: str) -> pd.DataFrame:
    data = season_window_frame(frame, window_name)
    validate_dataset(data)
    data["season"] = data["season"].astype(str)
    rows = []
    for season in validation_seasons(data):
        train, validation = split_train_validation(data, season)
        if train.empty or validation.empty:
            rows.append(
                {
                    "window": window_name,
                    "validation_season": season,
                    "included_seasons": ", ".join(sorted(data["season"].unique())),
                    "train_seasons": "",
                    "n_train": 0,
                    "n_validation": len(validation),
                    "note": "skipped: no earlier training season within window",
                }
            )
            continue
        rows.append(
            {
                "window": window_name,
                "validation_season": season,
                "included_seasons": ", ".join(sorted(data["season"].unique())),
                "train_seasons": ", ".join(sorted(train["season"].astype(str).unique())),
                "n_train": len(train),
                "n_validation": len(validation),
                "note": "",
            }
        )
    return pd.DataFrame(rows)


def _position_strategy_window_rows(position_results: pd.DataFrame) -> pd.DataFrame:
    if position_results.empty:
        return pd.DataFrame()
    all_rows = position_results.loc[position_results["position"].astype(str) == "ALL"].copy()
    if all_rows.empty:
        return pd.DataFrame()
    all_rows = all_rows.rename(columns={"strategy": "model"})
    all_rows = all_rows.drop(columns=["position"], errors="ignore")
    return all_rows


def _window_results(
    frame: pd.DataFrame,
    window_name: str,
    *,
    model_specs: list[SklearnModelSpec] | None = None,
    residual_specs: list[SklearnModelSpec] | None = None,
) -> pd.DataFrame:
    min_season = season_window_definitions()[window_name]
    data = season_window_frame(frame, window_name)
    validate_dataset(data)
    standard = run_backtest(
        frame,
        min_season=min_season,
        model_specs=model_specs,
        residual_specs=residual_specs,
    )
    position = run_position_model_backtest(
        frame,
        min_season=min_season,
        estimator=clone((model_specs or sklearn_model_specs())[0].estimator),
    )
    combined = pd.concat(
        [standard, _position_strategy_window_rows(position)],
        ignore_index=True,
        sort=False,
    )
    combined.insert(0, "window", window_name)
    combined["source"] = np.where(
        combined["model"].isin(
            {"position_wise_models", "global_plus_position_interactions"}
        ),
        "position_strategy",
        "standard_backtest",
    )
    return combined


def run_season_window_comparison(
    frame: pd.DataFrame,
    *,
    model_specs: list[SklearnModelSpec] | None = None,
    residual_specs: list[SklearnModelSpec] | None = None,
) -> pd.DataFrame:
    rows = []
    diagnostics: dict[str, Any] = {"folds": {}}
    for window_name in season_window_definitions():
        try:
            if not season_window_available(frame, window_name):
                LOGGER.warning(
                    "Skipping season window %s: source data does not contain seasons needed for this comparison.",
                    window_name,
                )
                diagnostics["folds"][window_name] = pd.DataFrame(
                    [{"window": window_name, "note": "skipped: source lacks required earlier seasons"}]
                )
                continue
            fold_summary = season_window_fold_summary(frame, window_name)
            diagnostics["folds"][window_name] = fold_summary
            if fold_summary.empty or fold_summary["n_train"].eq(0).all():
                LOGGER.warning("Skipping season window %s: too little training data.", window_name)
                continue
            rows.append(
                _window_results(
                    frame,
                    window_name,
                    model_specs=model_specs,
                    residual_specs=residual_specs,
                )
            )
        except BacktestError as exc:
            LOGGER.warning("Skipping season window %s: %s", window_name, exc)
            diagnostics["folds"][window_name] = pd.DataFrame(
                [{"window": window_name, "note": f"skipped: {exc}"}]
            )
    if not rows:
        raise BacktestError("No season-window comparison results were produced.")
    results = pd.concat(rows, ignore_index=True, sort=False)
    results.attrs["diagnostics"] = diagnostics
    return results


def write_season_window_results(
    results: pd.DataFrame,
    path: Path = DEFAULT_SEASON_WINDOW_RESULTS_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(path, index=False)


def _season_window_aggregate(results: pd.DataFrame) -> pd.DataFrame:
    metrics = ["mae", "rmse", "spearman", "top_10_precision", "top_20_precision", "top_50_precision"]
    return (
        results.groupby(["window", "model"], as_index=False)
        .agg(
            seasons=("validation_season", "nunique"),
            mean_train_rows=("n_train", "mean"),
            mean_validation_rows=("n_validation", "mean"),
            **{metric: (metric, "mean") for metric in metrics},
        )
        .sort_values(["window", "mae", "model"])
    )


def _best_windows_by_metric(aggregate: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for metric in ["mae", "rmse"]:
        by_window = aggregate.groupby("window", as_index=False)[metric].min()
        best = by_window.loc[by_window[metric].idxmin()]
        rows.append({"metric": metric, "best_window": best["window"], "value": best[metric]})
    for metric in ["spearman", "top_10_precision", "top_20_precision", "top_50_precision"]:
        by_window = aggregate.groupby("window", as_index=False)[metric].max()
        best = by_window.loc[by_window[metric].idxmax()]
        rows.append({"metric": metric, "best_window": best["window"], "value": best[metric]})
    return pd.DataFrame(rows)


def _season_window_model_comparison(aggregate: pd.DataFrame) -> pd.DataFrame:
    focus = aggregate.loc[aggregate["model"].isin(SEASON_WINDOW_FOCUS_MODELS)].copy()
    if focus.empty:
        return pd.DataFrame()
    return focus.sort_values(["model", "window"])[
        ["model", "window", "seasons", "mae", "rmse", "spearman", *TOP_K_RESULT_COLUMNS]
    ]


TOP_K_RESULT_COLUMNS = ("top_10_precision", "top_20_precision", "top_50_precision")


def _older_season_effects(aggregate: pd.DataFrame) -> pd.DataFrame:
    rows = []
    indexed = aggregate.set_index(["model", "window"])
    for model in SEASON_WINDOW_FOCUS_MODELS:
        available = set(aggregate.loc[aggregate["model"] == model, "window"])
        for old_window, new_window, label in [
            ("full_history", "supported_seasons", "full_vs_supported"),
            ("supported_seasons", "rich_feature_seasons", "supported_vs_rich"),
        ]:
            if {old_window, new_window}.issubset(available):
                old = indexed.loc[(model, old_window)]
                new = indexed.loc[(model, new_window)]
                rows.append(
                    {
                        "model": model,
                        "comparison": label,
                        "mae_delta_old_minus_new": old["mae"] - new["mae"],
                        "rmse_delta_old_minus_new": old["rmse"] - new["rmse"],
                        "spearman_delta_old_minus_new": old["spearman"] - new["spearman"],
                        "interpretation": (
                            "older window helps MAE"
                            if old["mae"] < new["mae"]
                            else "older window hurts MAE"
                        ),
                    }
                )
    return pd.DataFrame(rows)


def write_season_window_report(
    results: pd.DataFrame,
    path: Path = DEFAULT_SEASON_WINDOW_REPORT_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    aggregate = _season_window_aggregate(results)
    best = _best_windows_by_metric(aggregate)
    model_comparison = _season_window_model_comparison(aggregate)
    older_effects = _older_season_effects(aggregate)
    fold_tables = results.attrs.get("diagnostics", {}).get("folds", {})
    fold_summary = (
        pd.concat(fold_tables.values(), ignore_index=True, sort=False)
        if fold_tables
        else pd.DataFrame()
    )
    rich_folds = fold_summary.loc[fold_summary["window"].eq("rich_feature_seasons")]
    rich_reliability = (
        "Rich-feature seasons have at least one prior training season for each produced fold, "
        f"with mean train rows {rich_folds['n_train'].mean():.0f}."
        if not rich_folds.empty and rich_folds["n_train"].gt(0).all()
        else "Rich-feature seasons have too little data for at least one fold."
    )
    best_mae_window = best.loc[best["metric"].eq("mae"), "best_window"].iloc[0]
    lines = [
        "# Season Window Comparison",
        "",
        "Rolling-origin comparison of season windows. Broad ablation and feature selection "
        "remain opt-in and are not run by this experiment.",
        "",
        "## Seasons And Folds",
        "",
        markdown_table(fold_summary),
        "",
        "## Best Window By Metric",
        "",
        markdown_table(best),
        "",
        "## Model-By-Model Window Comparison",
        "",
        markdown_table(model_comparison),
        "",
        "## Older Season Effects",
        "",
        "Positive MAE/RMSE deltas mean the older window is worse; negative deltas mean it is better. "
        "Positive Spearman deltas mean the older window is better.",
        "",
        markdown_table(older_effects),
        "",
        "## Rich-Feature Season Reliability",
        "",
        rich_reliability,
        "",
        "## Recommendation",
        "",
        f"Use `{best_mae_window}` as the default candidate window for the next modelling pass "
        "unless a specific ranking metric in the best-window table justifies a different target.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--position-results", type=Path, default=DEFAULT_POSITION_RESULTS_PATH)
    parser.add_argument("--position-summary", type=Path, default=DEFAULT_POSITION_SUMMARY_PATH)
    parser.add_argument(
        "--min-season",
        help=(
            "Optional supported-season experiment filter. When set, trains and validates only on "
            "seasons greater than or equal to this value and writes supported-season reports."
        ),
    )
    parser.add_argument(
        "--run-broad-ablation",
        action="store_true",
        help="Also run the slower broad feature ablation matrix in supported-season mode.",
    )
    parser.add_argument(
        "--run-feature-selection",
        action="store_true",
        help="Also run the slower mathematical feature-selection experiment in supported-season mode.",
    )
    parser.add_argument(
        "--run-season-window-comparison",
        action="store_true",
        help="Run the opt-in season-window comparison experiment and write separate reports.",
    )
    parser.add_argument(
        "--run-model-pruning-audit",
        action="store_true",
        help="Also run the model pruning audit and write separate audit reports.",
    )
    parser.add_argument(
        "--run-position-feature-mask-experiment",
        action="store_true",
        help="Run the opt-in statistical position feature mask experiment.",
    )
    parser.add_argument(
        "--run-ensemble-experiment",
        action="store_true",
        help="Run the opt-in lightweight weighted ensemble experiment.",
    )
    return parser.parse_args()


def run_model_pruning_audit_report(data: pd.DataFrame, *, min_season: str = "2022-23") -> None:
    from evaluation.model_pruning_audit import run_audit, write_audit_outputs

    audit, classifications = run_audit(data, min_season=min_season)
    write_audit_outputs(audit, classifications)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    args = parse_args()
    data = read_dataset(args.input)
    if args.run_ensemble_experiment:
        LOGGER.info("Running ensemble experiment.")
        ensemble_results = run_ensemble_experiment(data)
        write_ensemble_results(ensemble_results)
        write_ensemble_report(ensemble_results)
        LOGGER.info(
            "Wrote ensemble experiment to %s and %s",
            DEFAULT_ENSEMBLE_RESULTS_PATH,
            DEFAULT_ENSEMBLE_REPORT_PATH,
        )
        return

    if args.run_position_feature_mask_experiment:
        LOGGER.info("Running position feature mask experiment.")
        mask_results = run_position_feature_mask_experiment(data)
        write_position_feature_mask_results(mask_results)
        write_position_feature_mask_report(mask_results)
        LOGGER.info(
            "Wrote position feature mask experiment to %s and %s",
            DEFAULT_POSITION_FEATURE_MASK_RESULTS_PATH,
            DEFAULT_POSITION_FEATURE_MASK_REPORT_PATH,
        )
        return

    if args.run_season_window_comparison:
        LOGGER.info("Running season-window comparison experiment.")
        window_results = run_season_window_comparison(data)
        write_season_window_results(window_results)
        write_season_window_report(window_results)
        LOGGER.info(
            "Wrote season-window comparison to %s and %s",
            DEFAULT_SEASON_WINDOW_RESULTS_PATH,
            DEFAULT_SEASON_WINDOW_REPORT_PATH,
        )
        return

    if args.min_season is None:
        LOGGER.info(
            "Optional experiments: broad ablation disabled, feature selection disabled, "
            "model pruning audit %s",
            "enabled" if args.run_model_pruning_audit else "disabled",
        )
        results = run_backtest(data)
        write_results(results, args.results)
        write_markdown_summary(results, args.summary)
        position_results = run_position_model_backtest(data)
        write_position_results(position_results, args.position_results)
        write_position_markdown_summary(position_results, args.position_summary)
        if args.run_model_pruning_audit:
            run_model_pruning_audit_report(data, min_season="2022-23")
        LOGGER.info(
            "Wrote backtest results to %s, %s, %s, and %s",
            args.results,
            args.summary,
            args.position_results,
            args.position_summary,
        )
        return

    LOGGER.info(
        "Optional experiments: broad ablation %s, feature selection %s, model pruning audit %s",
        "enabled" if args.run_broad_ablation else "disabled",
        "enabled" if args.run_feature_selection else "disabled",
        "enabled" if args.run_model_pruning_audit else "disabled",
    )
    before_supported_results = (
        pd.read_csv(DEFAULT_SUPPORTED_RESULTS_PATH)
        if DEFAULT_SUPPORTED_RESULTS_PATH.exists()
        else None
    )
    before_position_results = (
        pd.read_csv(DEFAULT_POSITION_RESULTS_PATH)
        if DEFAULT_POSITION_RESULTS_PATH.exists()
        else None
    )

    filtered_results = run_backtest(data, min_season=args.min_season)
    write_results(filtered_results, DEFAULT_SUPPORTED_RESULTS_PATH)
    write_markdown_summary(filtered_results, DEFAULT_SUPPORTED_SUMMARY_PATH)
    filtered_position_results = run_position_model_backtest(data, min_season=args.min_season)

    if DEFAULT_RESULTS_PATH.exists():
        full_results = pd.read_csv(DEFAULT_RESULTS_PATH)
    else:
        full_results = run_backtest(data)
    if DEFAULT_POSITION_RESULTS_PATH.exists():
        full_position_results: pd.DataFrame | None = pd.read_csv(DEFAULT_POSITION_RESULTS_PATH)
    else:
        full_position_results = run_position_model_backtest(data)

    write_supported_season_filter_report(
        source=data,
        full_results=full_results,
        filtered_results=filtered_results,
        full_position_results=full_position_results,
        filtered_position_results=filtered_position_results,
        min_season=args.min_season,
    )
    write_team_form_feature_report(
        before_results=before_supported_results,
        after_results=filtered_results,
        before_position_results=before_position_results,
        after_position_results=filtered_position_results,
        source=data,
        min_season=args.min_season,
    )
    if args.run_broad_ablation:
        ablation_results = run_broad_feature_ablation(data, min_season=args.min_season)
        write_broad_feature_ablation_results(ablation_results)
        write_broad_feature_ablation_report(ablation_results)
    if args.run_feature_selection:
        feature_selection_results = run_feature_selection_experiment(
            data,
            min_season=args.min_season,
        )
        write_feature_selection_results(feature_selection_results)
        write_feature_selection_report(feature_selection_results)
    if args.run_model_pruning_audit:
        run_model_pruning_audit_report(data, min_season=args.min_season)
    LOGGER.info(
        "Wrote supported-season results to %s, %s, %s, and %s",
        DEFAULT_SUPPORTED_RESULTS_PATH,
        DEFAULT_SUPPORTED_SUMMARY_PATH,
        DEFAULT_SUPPORTED_FILTER_REPORT_PATH,
        DEFAULT_TEAM_FORM_FEATURE_REPORT_PATH,
    )


if __name__ == "__main__":
    main()
