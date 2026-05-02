"""Rolling-origin backtests for FPL point prediction models."""

from __future__ import annotations

import argparse
import importlib.util
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
from sklearn.ensemble import (
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
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
RESIDUAL_MODEL_NAMES = ("Ridge", "ElasticNet", "XGBoost", "LightGBM", "CatBoost")
BASELINE_FEATURE_MODELS = {
    "pred_previous_gameweek_points": "previous_gameweek_points",
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
    "pred_previous_gameweek_points",
    "pred_rolling_3_gameweek_mean",
    "pred_rolling_5_gameweek_mean",
    "pred_minutes_adjusted_rolling_mean",
    "team_elo_pre_gw",
    "opponent_elo_pre_gw",
    "elo_difference",
    "home_adjusted_elo_difference",
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


def feature_columns(frame: pd.DataFrame) -> list[str]:
    candidates = [column for column in STABLE_FEATURE_COLUMNS if column in frame.columns]
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
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_columns,
            )
        )
    return ColumnTransformer(transformers=transformers, remainder="drop")


def sklearn_model_specs(random_state: int = 42) -> list[SklearnModelSpec]:
    specs = [
        SklearnModelSpec("Ridge", Ridge(alpha=1.0), scale_numeric=True),
        SklearnModelSpec(
            "ElasticNet",
            ElasticNet(alpha=0.01, l1_ratio=0.2, max_iter=10_000, random_state=random_state),
            scale_numeric=True,
        ),
        SklearnModelSpec(
            "RandomForestRegressor",
            RandomForestRegressor(
                n_estimators=200,
                min_samples_leaf=5,
                n_jobs=-1,
                random_state=random_state,
            ),
        ),
        SklearnModelSpec(
            "HistGradientBoostingRegressor",
            HistGradientBoostingRegressor(max_iter=200, random_state=random_state),
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

    if importlib.util.find_spec("lightgbm") is not None:
        from lightgbm import LGBMRegressor

        specs.append(
            SklearnModelSpec(
                "LightGBM",
                LGBMRegressor(
                    n_estimators=300,
                    learning_rate=0.05,
                    num_leaves=31,
                    random_state=random_state,
                    verbose=-1,
                ),
            )
        )
    else:
        LOGGER.warning("Skipping LightGBM: package is not installed.")

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
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    train_model = train.dropna(subset=[TARGET_COLUMN]).copy()
    validation_model = validation.dropna(subset=[TARGET_COLUMN]).copy()
    if train_model.empty or validation_model.empty:
        raise BacktestError(f"No train/validation rows with targets for season {validation_season}.")

    columns = feature_columns(train_model)
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

    columns = feature_columns(train_model)
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
) -> dict[str, Any]:
    train_model = train.dropna(subset=[TARGET_COLUMN, NEXT_60_COLUMN]).copy()
    validation_model = validation.dropna(subset=[TARGET_COLUMN]).copy()
    if train_model.empty or validation_model.empty:
        raise BacktestError(f"No rows available for two-stage model in season {validation_season}.")

    columns = feature_columns(train_model)
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
) -> pd.Series:
    columns = feature_columns(train)
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

    predictions["global_model"] = fit_predict_direct_model(
        train_model,
        validation_model,
        estimator=base_estimator,
        include_position=True,
        add_interactions=False,
    )
    predictions["global_plus_position_interactions"] = fit_predict_direct_model(
        train_model,
        validation_model,
        estimator=base_estimator,
        include_position=True,
        add_interactions=True,
    )

    position_wise = pd.Series(index=validation_model.index, dtype="float64")
    for position, validation_position in validation_model.groupby(POSITION_COLUMN, dropna=False):
        position_key = str(position)
        train_position = train_model.loc[train_model[POSITION_COLUMN].astype(str) == position_key]
        if len(train_position) < min_position_train_rows:
            position_wise.loc[validation_position.index] = predictions.loc[
                validation_position.index, "global_model"
            ]
            continue
        position_wise.loc[validation_position.index] = fit_predict_direct_model(
            train_position,
            validation_position,
            estimator=base_estimator,
            include_position=False,
            add_interactions=False,
        )
    predictions["position_wise_models"] = position_wise

    rows: list[dict[str, Any]] = []
    for strategy in (
        "global_model",
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
) -> pd.DataFrame:
    validate_dataset(frame)
    data = frame.copy()
    data["season"] = data["season"].astype(str)
    diagnostics = {"position": position_diagnostics(data)}
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
) -> pd.DataFrame:
    """Run rolling-origin validation by season."""
    validate_dataset(frame)
    data = frame.copy()
    data["season"] = data["season"].astype(str)
    diagnostics: dict[str, Any] = {"position": position_diagnostics(data)}
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
            )
        )
        if residual_specs:
            rows.extend(
                evaluate_residual_models(
                    train,
                    validation,
                    validation_season=season,
                    models=residual_specs,
                )
            )
        if NEXT_60_COLUMN in data.columns:
            try:
                rows.append(
                    evaluate_two_stage_model(
                        train,
                        validation,
                        validation_season=season,
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--position-results", type=Path, default=DEFAULT_POSITION_RESULTS_PATH)
    parser.add_argument("--position-summary", type=Path, default=DEFAULT_POSITION_SUMMARY_PATH)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    args = parse_args()
    data = read_dataset(args.input)
    results = run_backtest(data)
    write_results(results, args.results)
    write_markdown_summary(results, args.summary)
    position_results = run_position_model_backtest(data)
    write_position_results(position_results, args.position_results)
    write_position_markdown_summary(position_results, args.position_summary)
    LOGGER.info(
        "Wrote backtest results to %s, %s, %s, and %s",
        args.results,
        args.summary,
        args.position_results,
        args.position_summary,
    )


if __name__ == "__main__":
    main()
