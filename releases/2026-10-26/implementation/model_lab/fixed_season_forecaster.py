"""Operational fixed-season calibration; archived base forecaster stays unchanged.

Build as-of season features with the frozen experiment.make_features, then call
fit_models at GW1,5,9,... and forecast with that model bundle. Future outcomes
may be present in the archive but are filtered strictly before the fit cutoff.
Never relabel an old base forecast as a fresh forecast.
"""
from pathlib import Path
import importlib.util
import sys
import numpy as np
import pandas as pd
from .common import ROOT, read, sha

ID = 'fixed_season_h8_adaptive_v1'
RECIPE = ROOT / 'reports/season_role_gate_2026_10_24'

def recipe():
    for filename in ['season_gate.py', 'experiment.py']:
        expected = read(RECIPE/'proposal.json')['input_hashes'][str((RECIPE/filename).relative_to(ROOT))]
        if sha(RECIPE/filename) != expected:
            raise ValueError('Frozen calibration implementation changed')
    spec = importlib.util.spec_from_file_location('season_gate', RECIPE/'season_gate.py')
    gate = importlib.util.module_from_spec(spec); sys.modules['season_gate'] = gate; spec.loader.exec_module(gate)
    spec = importlib.util.spec_from_file_location('_fixed_season_recipe', RECIPE/'experiment.py')
    implementation = importlib.util.module_from_spec(spec); spec.loader.exec_module(implementation)
    return gate, implementation

def load_training_archive():
    if sha(RECIPE/'data.pkl') != read(RECIPE/'data_lock.json')['sha256']:
        raise ValueError('Training archive changed')
    return pd.read_pickle(RECIPE/'data.pkl')

def fit_models(data, cutoff, season, refit_round):
    if refit_round not in range(1,39,4):
        raise ValueError('Use frozen four-round refit schedule')
    cutoff = pd.Timestamp(cutoff)
    if cutoff.tzinfo is None: raise ValueError('Timezone required')
    gate, implementation = recipe(); models = {}; audits = []
    for pos in ['GK','DEF','MID','FWD']:
        for j in range(8):
            train = implementation.training(data, cutoff, pos, j)
            if len(train)<100: raise ValueError('Insufficient qualified archived training rows')
            key = f'{pos}_{j}'; models[key] = gate.fit(train, learned=False)
            audits.append(dict(key=key,rows=len(train),max_origin=str(train.forecast_at.max()),max_label=str(train[f'label_at_{j}'].max())))
    return dict(model_id=ID,season=season,refit_round=refit_round,cutoff=str(cutoff),models=models,audits=audits)

def forecast(features, bundle):
    if bundle['model_id'] != ID: raise ValueError('Wrong calibration bundle')
    if features.duplicated(['season','round','code']).any(): raise ValueError('Duplicate origin/player')
    at = pd.to_datetime(features.forecast_at,utc=True)
    if not features.season.eq(bundle['season']).all(): raise ValueError('Season mismatch')
    if not features['round'].between(bundle['refit_round'], min(bundle['refit_round']+3,38)).all(): raise ValueError('Stale calibration: refit required')
    if not at.ge(pd.Timestamp(bundle['cutoff'])).all(): raise ValueError('Future model fit')
    if 'latest_feature_available' in features:
        latest = pd.to_datetime(features.latest_feature_available,utc=True)
        if not (latest.isna() | latest.lt(at)).all(): raise ValueError('Unavailable history')
    if 'old_season' in features:
        known = features.old_season.notna()
        if not features.loc[known,'old_season'].lt(features.loc[known,'season']).all(): raise ValueError('Incorrect season boundary')
    gate,_ = recipe(); result = features[['season','round','code','forecast_at']].copy()
    for j in range(8):
        result[f'base_xp_{j}'] = features[f'xp_{j}']
        result[f'xp_{j}'] = np.nan
        valid = features['round']+j<=38
        for pos in ['GK','DEF','MID','FWD']:
            q=features[valid & features.position.eq(pos)].copy()
            if q.empty: continue
            model=bundle['models'][f'{pos}_{j}']
            if model['learned'] or model['theta'] != [0.,1.,0.]: raise ValueError('Learned weights are not authorized')
            q['xp_0']=q[f'xp_{j}']; result.loc[q.index,f'xp_{j}']=gate.predict(q,model)[0]
        if not np.isfinite(result.loc[valid,f'xp_{j}']).all(): raise ValueError('Missing/nonfinite forecast')
    return result

def make_features(players, matches):
    """Matches use frozen normalized schema, include zero appearances and UTC available.
    Reuse the archived assembler: within-season last10, no cross-season mixing
    until fixed sample-size weighting. Caller supplies fresh base xp_0..xp_7.
    """
    _,implementation=recipe()
    return players.merge(implementation.make_features(players,matches),on=['season','round','code'],validate='one_to_one')
