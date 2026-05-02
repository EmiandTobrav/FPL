"""Evaluation metrics for FPL point predictions."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _valid_prediction_pairs(y_true: pd.Series, y_pred: pd.Series) -> tuple[pd.Series, pd.Series]:
    pairs = pd.concat([pd.Series(y_true), pd.Series(y_pred)], axis=1).dropna()
    if pairs.empty:
        raise ValueError("No valid prediction pairs after dropping missing values.")
    return pairs.iloc[:, 0], pairs.iloc[:, 1]


def mae(y_true: pd.Series, y_pred: pd.Series) -> float:
    """Mean absolute error."""
    actual, predicted = _valid_prediction_pairs(y_true, y_pred)
    return float((actual - predicted).abs().mean())


def rmse(y_true: pd.Series, y_pred: pd.Series) -> float:
    """Root mean squared error."""
    actual, predicted = _valid_prediction_pairs(y_true, y_pred)
    return float(np.sqrt(((actual - predicted) ** 2).mean()))


def spearman_rank_correlation(y_true: pd.Series, y_pred: pd.Series) -> float:
    """Spearman rank correlation using pandas rank correlation."""
    actual, predicted = _valid_prediction_pairs(y_true, y_pred)
    actual_rank = actual.rank(method="average")
    predicted_rank = predicted.rank(method="average")
    if actual_rank.nunique(dropna=True) < 2 or predicted_rank.nunique(dropna=True) < 2:
        return float("nan")
    correlation = actual_rank.corr(predicted_rank)
    return float(correlation)


def top_k_precision(y_true: pd.Series, y_pred: pd.Series, k: int) -> float:
    """Share of true top-k rows captured by predicted top-k rows."""
    valid = pd.concat([y_true.rename("actual"), y_pred.rename("predicted")], axis=1).dropna()
    valid["actual"] = pd.to_numeric(valid["actual"], errors="coerce")
    valid["predicted"] = pd.to_numeric(valid["predicted"], errors="coerce")
    valid = valid.dropna()
    if valid.empty:
        return float("nan")
    cutoff = min(k, len(valid))
    predicted_top = set(valid.nlargest(cutoff, "predicted").index)
    actual_top = set(valid.nlargest(cutoff, "actual").index)
    return len(predicted_top & actual_top) / cutoff


def average_actual_points_in_predicted_top_k(
    y_true: pd.Series,
    y_pred: pd.Series,
    k: int,
) -> float:
    """Average actual points among the predicted top-k rows."""
    valid = pd.concat([y_true.rename("actual"), y_pred.rename("predicted")], axis=1).dropna()
    valid["actual"] = pd.to_numeric(valid["actual"], errors="coerce")
    valid["predicted"] = pd.to_numeric(valid["predicted"], errors="coerce")
    valid = valid.dropna()
    if valid.empty:
        return float("nan")
    cutoff = min(k, len(valid))
    return float(valid.nlargest(cutoff, "predicted")["actual"].mean())
