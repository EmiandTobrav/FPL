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
