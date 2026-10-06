"""Predeclared upside and decision-relevance models; features exclude current outcomes."""
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor
THRESHOLD=8
CANDIDATES=['upside_only','mix_upside_25','weighted_mean','mix_weighted_50']

def estimator():
    return make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),
        HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=15,
        min_samples_leaf=60,l2_regularization=20,early_stopping=False,random_state=173))

def tail_target(y):
    y=np.asarray(y,dtype=float)
    return np.where(y>=THRESHOLD,y,0.)

def relevance_weights(x):
    # Feature-only weights; never condition on realized current/future points or identity.
    form=x.historic_m6.fillna(0).clip(0,4).to_numpy()/4
    minutes=x.minutes_m6.fillna(0).clip(0,60).to_numpy()/60
    new=x.n_history.fillna(0).to_numpy()<12
    return 1.+3.*form*minutes+new.astype(float)

def candidate_scores(reference,tail,weighted):
    return {'upside_only':tail,'mix_upside_25':.75*reference+.25*tail,
            'weighted_mean':weighted,'mix_weighted_50':.5*reference+.5*weighted}
