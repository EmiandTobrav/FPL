"""Antisymmetric paired terminal differences, using unchanged terminal features."""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from .terminal_value import FEATURES, features, predict, attach


def fit(samples, cutoff):
    if not samples or any(pd.Timestamp(s['label_available_at'])>=pd.Timestamp(cutoff) or pd.Timestamp(s['forecast_at'])>=pd.Timestamp(cutoff) for s in samples):
        raise ValueError('Unavailable paired training labels')
    x=np.array([s['features'] for s in samples],float);y=np.array([s['target'] for s in samples],float)
    if x.shape[1]!=len(FEATURES) or not np.isfinite(x).all() or not np.isfinite(y).all(): raise ValueError('Invalid pairs')
    # No centering/intercept: reversing the pair reverses its prediction exactly.
    scale=np.sqrt(np.mean(x*x,axis=0));scale[scale==0]=1.
    reg=Ridge(alpha=50.,fit_intercept=False).fit(x/scale,y)
    return dict(features=FEATURES,mean=[0.]*len(FEATURES),scale=scale.tolist(),coef=reg.coef_.tolist(),intercept=0.,
        alpha=50.,cutoff=cutoff,rows=len(samples),training_seasons=sorted({s['season'] for s in samples}),
        latest_label_available_at=max(s['label_available_at'] for s in samples),
        target='tail_return_branch1_minus_branch0',interpretation='Only differences are identified; scalar potential is arbitrary up to a common offset.')
