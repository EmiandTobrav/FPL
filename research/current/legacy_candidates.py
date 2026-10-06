"""Opt-in residual idea from the May repository, adapted to deadline-safe features.
Not the old fitted model: same current features, horizons and HGB parameters.
"""
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def minutes_baseline(frame):
    # An explicit shrinkage heuristic, NOT an independently fitted minutes model.
    return (frame['historic_m6'].fillna(0).to_numpy() *
            frame['minutes_m6'].fillna(0).clip(0, 90).to_numpy() / 90)


class ResidualHGB:
    def __init__(self):
        self.model = make_pipeline(SimpleImputer(add_indicator=True), StandardScaler(),
            HistGradientBoostingRegressor(max_iter=100, max_leaf_nodes=15,
                min_samples_leaf=60, l2_regularization=20,
                early_stopping=False, random_state=173))

    def fit(self, frame, y):
        self.model.fit(frame, np.asarray(y) - minutes_baseline(frame))
        return self

    def predict(self, frame):
        return minutes_baseline(frame) + self.model.predict(frame)
