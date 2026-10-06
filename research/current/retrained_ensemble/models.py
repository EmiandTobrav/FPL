import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import ExtraTreesRegressor
NEW=['ridge_refresh','extra_refresh','re_refresh','three_refresh','three_frozen']
CANDIDATES=NEW[:4]+['rich_refresh']

def estimators():
    def pipe(model):return make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),model)
    return dict(ridge=pipe(Ridge(alpha=100)),extra=pipe(ExtraTreesRegressor(n_estimators=48,max_depth=12,min_samples_leaf=40,max_features=.8,n_jobs=1,random_state=173)))

def combine(ridge,extra,rich,frozen_ridge,frozen_extra,frozen_rich):
    return {'ridge_refresh':ridge,'extra_refresh':extra,'re_refresh':.5*ridge+.5*extra,
            'three_refresh':(ridge+extra+rich)/3,'three_frozen':(frozen_ridge+frozen_extra+frozen_rich)/3}
