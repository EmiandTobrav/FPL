"""Audit supported-season models for possible pruning."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.pipeline import Pipeline

from evaluation.backtest import (
    BASELINES,
    BASELINE_PREDICTION_COLUMN,
    MIN_POSITION_TRAIN_ROWS,
    NEXT_60_COLUMN,
    POSITION_COLUMN,
    TARGET_COLUMN,
    add_baseline_prediction_features,
    add_residual_target,
    build_preprocessor,
    feature_columns,
    final_residual_prediction,
    fit_predict_direct_model,
    minutes_adjusted_baseline_predictions,
    normalize_position_column,
    residual_model_specs,
    season_filtered_frame,
    sklearn_model_specs,
    split_train_validation,
    validate_dataset,
    validation_seasons,
    _classification_pipeline,
    _fit_conditional_regressor,
    _predict_positive_probability,
)
from evaluation.metrics import mae, rmse, spearman_rank_correlation, top_k_precision


LOGGER = logging.getLogger(__name__)
DEFAULT_INPUT_PATH = Path("data/processed/modeling_dataset.parquet")
DEFAULT_RESULTS_PATH = Path("reports/model_pruning_audit.csv")
DEFAULT_REPORT_PATH = Path("reports/model_pruning_audit.md")
TOP_K_COLUMNS = ("top_10_precision", "top_20_precision", "top_50_precision")
ERROR_COLUMNS = ("mae", "rmse")
CORRELATION_COLUMNS = ("spearman",)
METRIC_COLUMNS = (*ERROR_COLUMNS, *CORRELATION_COLUMNS, *TOP_K_COLUMNS)
EARLY_GW_BUCKETS = (
    ("GW1-5", 1, 5),
    ("GW6-10", 6, 10),
    ("GW11+", 11, None),
)
POSITIONS = ("GK", "DEF", "MID", "FWD")
BASELINE_REFERENCE = "minutes_adjusted_rolling_mean"


def read_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input dataset does not exist: {path}")
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported input format for {path}; expected .parquet or .csv")


def _prediction_frame(
    *,
    validation: pd.DataFrame,
    model_name: str,
    predictions: pd.Series,
) -> pd.DataFrame:
    frame = validation[[TARGET_COLUMN, "season", "gw"]].copy()
    frame["model"] = model_name
    frame["actual"] = validation[TARGET_COLUMN]
    frame["predicted"] = predictions.reindex(validation.index)
    if POSITION_COLUMN in validation.columns:
        frame[POSITION_COLUMN] = validation[POSITION_COLUMN]
    return frame.dropna(subset=["actual", "predicted"])


def _baseline_predictions(validation: pd.DataFrame) -> list[pd.DataFrame]:
    rows = []
    for model in BASELINES:
        try:
            predictions = model.predict(validation)
        except (ValueError, KeyError) as exc:
            LOGGER.warning("Skipping baseline %s in pruning audit: %s", model.name, exc)
            continue
        rows.append(_prediction_frame(validation=validation, model_name=model.name, predictions=predictions))
    return rows


def _direct_model_predictions(train: pd.DataFrame, validation: pd.DataFrame) -> list[pd.DataFrame]:
    rows = []
    train_model = train.dropna(subset=[TARGET_COLUMN]).copy()
    validation_model = validation.dropna(subset=[TARGET_COLUMN]).copy()
    columns = feature_columns(train_model)
    x_train = train_model[columns].replace({pd.NA: np.nan})
    x_validation = validation_model[columns].replace({pd.NA: np.nan})

    for spec in sklearn_model_specs():
        pipeline = Pipeline(
            [
                ("preprocess", build_preprocessor(train_model, columns, scale_numeric=spec.scale_numeric)),
                ("model", clone(spec.estimator)),
            ]
        )
        try:
            pipeline.fit(x_train, train_model[TARGET_COLUMN])
            predictions = pd.Series(pipeline.predict(x_validation), index=validation_model.index)
        except Exception as exc:  # noqa: BLE001 - model libraries raise varied exception types.
            LOGGER.warning("Skipping model %s in pruning audit: %s", spec.name, exc)
            continue
        rows.append(
            _prediction_frame(
                validation=validation_model,
                model_name=spec.name,
                predictions=predictions,
            )
        )
    return rows


def _residual_model_predictions(train: pd.DataFrame, validation: pd.DataFrame) -> list[pd.DataFrame]:
    rows = []
    train_with_residual = add_residual_target(train, minutes_adjusted_baseline_predictions(train))
    validation_with_baseline = validation.copy()
    validation_with_baseline[BASELINE_PREDICTION_COLUMN] = minutes_adjusted_baseline_predictions(
        validation
    )
    train_model = train_with_residual.dropna(
        subset=[TARGET_COLUMN, BASELINE_PREDICTION_COLUMN, "__residual_target"]
    ).copy()
    validation_model = validation_with_baseline.dropna(
        subset=[TARGET_COLUMN, BASELINE_PREDICTION_COLUMN]
    ).copy()
    columns = feature_columns(train_model)
    x_train = train_model[columns].replace({pd.NA: np.nan})
    x_validation = validation_model[columns].replace({pd.NA: np.nan})

    for spec in residual_model_specs():
        pipeline = Pipeline(
            [
                ("preprocess", build_preprocessor(train_model, columns, scale_numeric=spec.scale_numeric)),
                ("model", clone(spec.estimator)),
            ]
        )
        try:
            pipeline.fit(x_train, train_model["__residual_target"])
            residuals = pd.Series(pipeline.predict(x_validation), index=validation_model.index)
        except Exception as exc:  # noqa: BLE001 - model libraries raise varied exception types.
            LOGGER.warning("Skipping residual model %s in pruning audit: %s", spec.name, exc)
            continue
        predictions = final_residual_prediction(
            validation_model[BASELINE_PREDICTION_COLUMN],
            residuals,
        )
        rows.append(
            _prediction_frame(
                validation=validation_model,
                model_name=f"residual_{spec.name}",
                predictions=predictions,
            )
        )
    return rows


def _two_stage_predictions(train: pd.DataFrame, validation: pd.DataFrame) -> list[pd.DataFrame]:
    if NEXT_60_COLUMN not in train.columns:
        return []
    train_model = train.dropna(subset=[TARGET_COLUMN, NEXT_60_COLUMN]).copy()
    validation_model = validation.dropna(subset=[TARGET_COLUMN]).copy()
    if train_model.empty or validation_model.empty:
        return []
    columns = feature_columns(train_model)
    x_train = train_model[columns].replace({pd.NA: np.nan})
    x_validation = validation_model[columns].replace({pd.NA: np.nan})
    classifier = _classification_pipeline(train_model, columns)
    fallback = clone(sklearn_model_specs()[0].estimator)
    regressor_60_plus = _fit_conditional_regressor(
        train_model,
        columns,
        condition_value=True,
        fallback_estimator=fallback,
    )
    regressor_under_60 = _fit_conditional_regressor(
        train_model,
        columns,
        condition_value=False,
        fallback_estimator=fallback,
    )
    classifier.fit(x_train, train_model[NEXT_60_COLUMN])
    probability_60_plus = _predict_positive_probability(classifier, x_validation)
    predictions = pd.Series(
        probability_60_plus * regressor_60_plus.predict(x_validation)
        + (1 - probability_60_plus) * regressor_under_60.predict(x_validation),
        index=validation_model.index,
    )
    return [
        _prediction_frame(
            validation=validation_model,
            model_name="two_stage_minutes_points",
            predictions=predictions,
        )
    ]


def _position_strategy_predictions(train: pd.DataFrame, validation: pd.DataFrame) -> list[pd.DataFrame]:
    if POSITION_COLUMN not in train.columns or POSITION_COLUMN not in validation.columns:
        return []
    train_model = train.dropna(subset=[TARGET_COLUMN, POSITION_COLUMN]).copy()
    validation_model = validation.dropna(subset=[TARGET_COLUMN, POSITION_COLUMN]).copy()
    if train_model.empty or validation_model.empty:
        return []
    estimator = clone(sklearn_model_specs()[0].estimator)
    predictions = pd.DataFrame(index=validation_model.index)
    predictions["global_model"] = fit_predict_direct_model(
        train_model,
        validation_model,
        estimator=estimator,
        include_position=True,
        add_interactions=False,
    )
    predictions["global_plus_position_interactions"] = fit_predict_direct_model(
        train_model,
        validation_model,
        estimator=estimator,
        include_position=True,
        add_interactions=True,
    )
    position_wise = pd.Series(index=validation_model.index, dtype="float64")
    for position, validation_position in validation_model.groupby(POSITION_COLUMN, dropna=False):
        position_key = str(position)
        train_position = train_model.loc[train_model[POSITION_COLUMN].astype(str) == position_key]
        if len(train_position) < MIN_POSITION_TRAIN_ROWS:
            position_wise.loc[validation_position.index] = predictions.loc[
                validation_position.index, "global_model"
            ]
            continue
        position_wise.loc[validation_position.index] = fit_predict_direct_model(
            train_position,
            validation_position,
            estimator=estimator,
            include_position=False,
            add_interactions=False,
        )
    predictions["position_wise_models"] = position_wise
    return [
        _prediction_frame(validation=validation_model, model_name=model_name, predictions=predictions[model_name])
        for model_name in predictions.columns
    ]


def collect_supported_predictions(frame: pd.DataFrame, *, min_season: str = "2020-21") -> pd.DataFrame:
    validate_dataset(frame)
    data = season_filtered_frame(frame, min_season)
    validate_dataset(data)
    data = normalize_position_column(data)
    data = add_baseline_prediction_features(data)
    data["season"] = data["season"].astype(str)
    data = data.sort_values(["season", "gw"]).reset_index(drop=True)

    rows = []
    for season in validation_seasons(data):
        train, validation = split_train_validation(data, season)
        if train.empty or validation.empty:
            continue
        LOGGER.info("Collecting pruning-audit predictions for %s", season)
        rows.extend(_baseline_predictions(validation))
        rows.extend(_direct_model_predictions(train, validation))
        rows.extend(_residual_model_predictions(train, validation))
        rows.extend(_two_stage_predictions(train, validation))
        rows.extend(_position_strategy_predictions(train, validation))
    if not rows:
        raise ValueError("No pruning audit predictions were produced.")
    return pd.concat(rows, ignore_index=True)


def _segment_metric_row(predictions: pd.DataFrame, *, segment_type: str, segment: str) -> dict[str, Any]:
    return {
        "model": str(predictions["model"].iloc[0]),
        "segment_type": segment_type,
        "segment": segment,
        "n": len(predictions),
        "mae": mae(predictions["actual"], predictions["predicted"]),
        "rmse": rmse(predictions["actual"], predictions["predicted"]),
        "spearman": spearman_rank_correlation(predictions["actual"], predictions["predicted"]),
        "top_10_precision": top_k_precision(predictions["actual"], predictions["predicted"], 10),
        "top_20_precision": top_k_precision(predictions["actual"], predictions["predicted"], 20),
        "top_50_precision": top_k_precision(predictions["actual"], predictions["predicted"], 50),
    }


def summarize_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model, model_predictions in predictions.groupby("model", sort=False):
        rows.append(_segment_metric_row(model_predictions, segment_type="overall", segment="all"))
        for season, season_predictions in model_predictions.groupby("season", sort=True):
            rows.append(
                _segment_metric_row(
                    season_predictions,
                    segment_type="season",
                    segment=str(season),
                )
            )
        for bucket, start, end in EARLY_GW_BUCKETS:
            mask = model_predictions["gw"].ge(start)
            if end is not None:
                mask &= model_predictions["gw"].le(end)
            bucket_predictions = model_predictions.loc[mask]
            if not bucket_predictions.empty:
                rows.append(
                    _segment_metric_row(
                        bucket_predictions,
                        segment_type="gameweek_bucket",
                        segment=bucket,
                    )
                )
        if POSITION_COLUMN in model_predictions.columns:
            for position in POSITIONS:
                position_predictions = model_predictions.loc[
                    model_predictions[POSITION_COLUMN].astype(str) == position
                ]
                if not position_predictions.empty:
                    rows.append(
                        _segment_metric_row(
                            position_predictions,
                            segment_type="position",
                            segment=position,
                        )
                    )
    return pd.DataFrame(rows)


def add_competitiveness_flags(summary: pd.DataFrame) -> pd.DataFrame:
    data = summary.copy()
    for column in METRIC_COLUMNS:
        data[f"is_best_{column}"] = False
        data[f"is_near_best_{column}"] = False

    for _, index in data.groupby(["segment_type", "segment"]).groups.items():
        segment = data.loc[index]
        for column in ERROR_COLUMNS:
            best = segment[column].min()
            data.loc[index, f"is_best_{column}"] = segment[column].eq(best)
            data.loc[index, f"is_near_best_{column}"] = segment[column].le(best * 1.01)
        best_spearman = segment["spearman"].max()
        data.loc[index, "is_best_spearman"] = segment["spearman"].eq(best_spearman)
        data.loc[index, "is_near_best_spearman"] = segment["spearman"].ge(best_spearman - 0.01)
        for column in TOP_K_COLUMNS:
            best = segment[column].max()
            if best <= 0:
                continue
            data.loc[index, f"is_best_{column}"] = segment[column].eq(best)
            data.loc[index, f"is_near_best_{column}"] = segment[column].ge(best - 0.01)
    near_columns = [column for column in data.columns if column.startswith("is_near_best_")]
    best_columns = [column for column in data.columns if column.startswith("is_best_")]
    data["is_near_best_any_metric"] = data[near_columns].any(axis=1)
    data["is_best_any_metric"] = data[best_columns].any(axis=1)
    return data


def classify_models(audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model, model_rows in audit.groupby("model", sort=True):
        overall = model_rows.loc[model_rows["segment_type"] == "overall"]
        early = model_rows.loc[model_rows["segment_type"] == "gameweek_bucket"]
        position = model_rows.loc[model_rows["segment_type"] == "position"]
        season = model_rows.loc[model_rows["segment_type"] == "season"]
        ranking_columns = [f"is_near_best_{column}" for column in TOP_K_COLUMNS]
        primary_columns = ["is_near_best_mae", "is_near_best_rmse", "is_near_best_spearman"]
        overall_primary_competitive = bool(overall[primary_columns].any(axis=1).any())
        overall_competitive = bool(overall["is_near_best_any_metric"].any())
        early_competitive = bool(early["is_near_best_any_metric"].any())
        position_competitive = bool(position["is_near_best_any_metric"].any())
        season_competitive = bool(season["is_near_best_any_metric"].any())
        ranking_competitive = bool(model_rows[ranking_columns].any(axis=1).any())
        ever_best = bool(model_rows["is_best_any_metric"].any())
        ever_near = bool(model_rows["is_near_best_any_metric"].any())

        if overall_primary_competitive and (ever_best or ranking_competitive):
            classification = "keep_core"
        elif ever_near:
            classification = "keep_specialist"
        else:
            classification = "remove_candidate"
        if model_rows[list(METRIC_COLUMNS)].isna().any().any():
            classification = "investigate"
        rows.append(
            {
                "model": model,
                "classification": classification,
                "overall_competitive": overall_competitive,
                "overall_primary_competitive": overall_primary_competitive,
                "early_competitive": early_competitive,
                "position_competitive": position_competitive,
                "season_competitive": season_competitive,
                "ranking_competitive": ranking_competitive,
                "ever_best": ever_best,
                "ever_near_best": ever_near,
            }
        )
    return pd.DataFrame(rows).sort_values(["classification", "model"])


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "None."
    headers = list(frame.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in frame.iterrows():
        values = []
        for value in row:
            if isinstance(value, float):
                values.append(f"{value:.4f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _best_by_metric(audit: pd.DataFrame, segment_type: str, segment: str) -> pd.DataFrame:
    rows = []
    subset = audit.loc[(audit["segment_type"] == segment_type) & (audit["segment"] == segment)]
    for column in ERROR_COLUMNS:
        row = subset.loc[subset[column].idxmin()]
        rows.append({"metric": column, "model": row["model"], "value": row[column]})
    for column in (*CORRELATION_COLUMNS, *TOP_K_COLUMNS):
        row = subset.loc[subset[column].idxmax()]
        rows.append({"metric": column, "model": row["model"], "value": row[column]})
    return pd.DataFrame(rows)


def _model_rows(audit: pd.DataFrame, models: list[str], segment_type: str, segment: str) -> pd.DataFrame:
    return audit.loc[
        audit["model"].isin(models)
        & audit["segment_type"].eq(segment_type)
        & audit["segment"].eq(segment),
        ["model", *METRIC_COLUMNS, "is_near_best_any_metric", "is_best_any_metric"],
    ].sort_values("model")


def write_audit_report(audit: pd.DataFrame, classifications: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    overall = audit.loc[audit["segment_type"].eq("overall")].sort_values("mae")
    gw_1_5 = audit.loc[
        audit["segment_type"].eq("gameweek_bucket") & audit["segment"].eq("GW1-5")
    ].sort_values("mae")
    residual_models = sorted(model for model in audit["model"].unique() if model.startswith("residual_"))
    tree_models = ["XGBoost", "LightGBM", "CatBoost", "residual_XGBoost", "residual_LightGBM", "residual_CatBoost"]
    position_models = ["global_model", "position_wise_models", "global_plus_position_interactions"]
    baseline_early = gw_1_5.loc[gw_1_5["model"].eq(BASELINE_REFERENCE)]
    early_beaters = gw_1_5.loc[
        gw_1_5["mae"].lt(float(baseline_early["mae"].iloc[0]))
    ][["model", "mae", "rmse", "spearman"]] if not baseline_early.empty else pd.DataFrame()

    lines = [
        "# Model Pruning Audit",
        "",
        "Supported-season rolling-origin audit for model pruning. The audit replays predictions "
        "for seasons included by `--min-season 2020-21`; it does not change model code.",
        "",
        "## Classification",
        "",
        markdown_table(classifications),
        "",
        "## Best Overall By Metric",
        "",
        markdown_table(_best_by_metric(audit, "overall", "all")),
        "",
        "## Overall Metrics",
        "",
        markdown_table(overall[["model", *METRIC_COLUMNS, "is_near_best_any_metric", "is_best_any_metric"]]),
        "",
        "## Early-Season Metrics: GW1-5",
        "",
        markdown_table(gw_1_5[["model", *METRIC_COLUMNS, "is_near_best_any_metric", "is_best_any_metric"]]),
        "",
        "## Models Beating Minutes-Adjusted Baseline In GW1-5 By MAE",
        "",
        markdown_table(early_beaters),
        "",
        "## Residual Model Early-Season Check",
        "",
        markdown_table(_model_rows(audit, residual_models, "gameweek_bucket", "GW1-5")),
        "",
        "## Ridge And ElasticNet Check",
        "",
        markdown_table(_model_rows(audit, ["Ridge", "ElasticNet", "residual_Ridge", "residual_ElasticNet"], "overall", "all")),
        "",
        "## Tree/Boosting Model Check",
        "",
        markdown_table(_model_rows(audit, tree_models, "overall", "all")),
        "",
        "## Position Strategy Check",
        "",
        markdown_table(_model_rows(audit, position_models, "overall", "all")),
        "",
        "## Season-By-Season Performance",
        "",
        markdown_table(
            audit.loc[audit["segment_type"].eq("season"), ["model", "segment", *METRIC_COLUMNS]]
            .sort_values(["segment", "mae"])
        ),
        "",
        "## Position-Specific Performance",
        "",
        markdown_table(
            audit.loc[audit["segment_type"].eq("position"), ["model", "segment", *METRIC_COLUMNS]]
            .sort_values(["segment", "mae"])
        ),
        "",
        "## Classification Rules",
        "",
        "- `keep_core`: competitive overall and best or ranking-competitive somewhere.",
        "- `keep_specialist`: not core, but near-best in at least one early, position, season, or ranking context.",
        "- `remove_candidate`: not competitive overall, early-season, by position, by season, or on ranking metrics.",
        "- `investigate`: incomplete or invalid metric coverage.",
        "",
        "Near-best thresholds: within 1% of best MAE/RMSE, within 0.01 Spearman, "
        "or within 0.01 precision for top-k metrics.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_audit(
    frame: pd.DataFrame,
    *,
    min_season: str = "2020-21",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    predictions = collect_supported_predictions(frame, min_season=min_season)
    audit = add_competitiveness_flags(summarize_predictions(predictions))
    classifications = classify_models(audit)
    return audit.merge(classifications[["model", "classification"]], on="model", how="left"), classifications


def write_audit_outputs(audit: pd.DataFrame, classifications: pd.DataFrame) -> None:
    DEFAULT_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(DEFAULT_RESULTS_PATH, index=False)
    write_audit_report(audit, classifications, DEFAULT_REPORT_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--min-season", default="2020-21")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    args = parse_args()
    audit, classifications = run_audit(read_dataset(args.input), min_season=args.min_season)
    write_audit_outputs(audit, classifications)
    print(f"Wrote: {DEFAULT_RESULTS_PATH}")
    print(f"Wrote: {DEFAULT_REPORT_PATH}")


if __name__ == "__main__":
    main()
