"""Causal forecast folds, reusable prediction artifacts and paired diagnostics."""
from pathlib import Path
import importlib.util
import sys
import time
import re
import numpy as np
import pandas as pd
from .common import ROOT, read, digest, sha, atomic_json, runtime, implementation, claim, resolve, verify_files

KEY = ['season', 'round', 'code']


def pipeline_modules():
    folder = ROOT / 'datasets/fpl_model_pipeline_v1'
    # Import the existing pipeline under private names, leaving old modules intact.
    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m
    return load('_lab_loader', folder / 'loader.py'), load('_lab_pipeline', folder / 'pipeline.py')


def causal_training(rows, at, horizon, window_days=None):
    at = pd.Timestamp(at)
    if at.tzinfo is None: raise ValueError('Forecast time needs a timezone')
    target = 'target_total_points' if horizon == 1 else f'target_points_h{horizon}'
    mask = (rows.forecast_at < at) & (rows[f'target_h{horizon}_available_at'] < at) & rows[target].notna()
    if window_days is not None:
        if type(window_days) is not int or window_days <= 0: raise ValueError('Invalid history window')
        mask &= rows.forecast_at >= at - pd.Timedelta(days=window_days)
    train = rows.loc[mask].copy()
    if train.empty: raise ValueError('No causally available training labels')
    if not np.isfinite(train[target].to_numpy(float)).all(): raise ValueError('Nonfinite label')
    return train, target


def fit_predict(train, pred, target, features, schema, model, pipeline):
    # New adapters receive feature-only prediction inputs; never outcomes.
    if model['backend'] == 'custom':
        path = resolve(ROOT, model['adapter'])
        spec = importlib.util.spec_from_file_location('_lab_custom_' + sha(path)[:12], path)
        m = importlib.util.module_from_spec(spec); sys.modules[spec.name] = m; spec.loader.exec_module(m)
        config = dict(model.get('parameters', {})); config.setdefault('seed', model.get('seed', 20261014))
        values = m.fit_predict(train[features].copy(), train[target].copy(), pred[features].copy(), config)
    elif model['backend'] == 'mean':
        values = np.full(len(pred), float(train[target].mean()))
    else:
        pipe = pipeline.make_pipeline(schema, model['backend'], model['feature_set'],
            seed=model['seed'], model_params=model.get('parameters', {}))
        pipe.fit(train[features], train[target]); values = pipe.predict(pred[features])
    values = np.asarray(values, dtype=float)
    if values.shape != (len(pred),) or not np.isfinite(values).all(): raise ValueError('Invalid forecast output')
    return values


def diagnostics(predictions):
    scored = predictions[predictions.actual_points.notna()].copy()
    if scored.empty: raise ValueError('No known evaluation labels')
    groups = []
    for (model, season), g in scored.groupby(['model', 'season'], sort=True):
        error = g.predicted_points - g.actual_points
        groups.append({'model': model, 'season': season, 'rows': len(g),
            'rmse': float(np.sqrt(np.mean(error ** 2))), 'mae': float(np.mean(np.abs(error))),
            'bias': float(error.mean())})
    return groups


def validate(spec):
    if spec.get('version') != 1: raise ValueError('Unsupported forecast spec')
    for key in ['id', 'purpose', 'seasons', 'rounds', 'models', 'reference', 'clock', 'input_hashes', 'max_fits']:
        if not spec.get(key): raise ValueError(f'Missing {key}')
    if spec['purpose'] not in ['framework_validation', 'registered_research']: raise ValueError('Declare purpose')
    if spec['purpose'] == 'registered_research':
        proposal = read(resolve(ROOT, spec['proposal']))
        if proposal.get('fingerprint') != spec.get('proposal_fingerprint'): raise ValueError('Bind registered proposal')
        from scripts.research import fingerprint
        if fingerprint(proposal) != proposal['fingerprint']: raise ValueError('Registered proposal changed')
        if spec['clock'] != proposal['clock'] or not set(spec['seasons']) <= set(proposal['seasons']): raise ValueError('Proposal clock/seasons mismatch')
        if not set(proposal['input_hashes'].items()) <= set(spec['input_hashes'].items()): raise ValueError('Proposal inputs must remain bound')
        if proposal['candidate_id'] not in [m['id'] for m in spec['models']]: raise ValueError('Registered candidate missing')
        candidate = next(m for m in spec['models'] if m['id'] == proposal['candidate_id'])
        if proposal['features'] != candidate['feature_set']: raise ValueError('Proposal feature set changed')
        params = {k: candidate.get(k, {}) for k in ['backend', 'seed', 'parameters']}
        if proposal['model_parameters'] != params: raise ValueError('Proposal model parameters changed')
        policy = {'stage': 'forecast', 'horizon': spec['horizon'], 'reference': spec['reference'],
                  'rounds': spec['rounds'], 'window_days': spec.get('window_days')}
        if proposal['decision_policy'] != policy: raise ValueError('Proposal forecast evaluation changed')
        if spec['max_fits'] > proposal['resources'].get('maximum_fits', 0): raise ValueError('Proposal fit budget missing/exceeded')
    if spec.get('horizon') not in [1, 3, 6]: raise ValueError('Horizon must be 1, 3 or 6')
    if type(spec['max_fits']) is not int or spec['max_fits'] < 1: raise ValueError('Invalid fit budget')
    if len(set(spec['rounds'])) != len(spec['rounds']) or any(type(r) is not int or not 1 <= r <= 38 for r in spec['rounds']): raise ValueError('Invalid rounds')
    if len(set(spec['seasons'])) != len(spec['seasons']): raise ValueError('Repeated seasons')
    ids = [m['id'] for m in spec['models']]
    if len(set(ids)) != len(ids) or spec['reference'] not in ids: raise ValueError('Model IDs/reference invalid')
    if any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,80}', i) for i in ids): raise ValueError('Use simple safe model IDs')
    for m in spec['models']:
        if m.get('backend') not in ['mean', 'ridge', 'catboost', 'lightgbm', 'custom']: raise ValueError('Unknown backend')
        if m.get('feature_set') not in ['baseline', 'extended']: raise ValueError('Unknown feature set')
        if type(m.get('seed')) is not int: raise ValueError('Explicit seed required')
        if m['backend'] == 'custom' and m.get('adapter') not in spec['input_hashes']: raise ValueError('Bind custom adapter source')
    needed = {'datasets/fpl_model_pipeline_v1/manifest.json', 'datasets/fpl_model_pipeline_v1/schema.json',
              f'datasets/fpl_model_pipeline_v1/{spec["clock"]}.csv.xz'}
    if not needed <= set(spec['input_hashes']): raise ValueError('Bind pipeline manifest, schema and chosen feature table')
    verify_files(ROOT, spec['input_hashes'])


def run(spec, output):
    validate(spec)
    loader, pipeline = pipeline_modules()
    rows, schema = loader.load_rows(clock=spec['clock'])
    if rows.duplicated(KEY).any(): raise ValueError('Duplicate data keys')
    origins = rows[rows.season.isin(spec['seasons']) & rows['round'].isin(spec['rounds'])][['season', 'round', 'forecast_at']].drop_duplicates().sort_values('forecast_at')
    expected = {(s, r) for s in spec['seasons'] for r in spec['rounds']}
    if set(zip(origins.season, origins['round'])) != expected or origins.duplicated(['season', 'round']).any(): raise ValueError('Missing or ambiguous forecast origins; no fabricated rounds')
    if len(origins) * len(spec['models']) > spec['max_fits']: raise ValueError('Requested folds exceed declared fit budget')
    contract = {'spec': spec, 'runtime': runtime(), 'implementation': implementation()}
    directory = Path(output) / 'runs' / digest(contract)
    completed = claim(directory, contract)
    if completed: return dict(completed, reused_completed_run=True, directory=str(directory))
    started = time.monotonic(); cpu = time.process_time(); combined = []; reused = 0
    try:
        for season, rd, at in origins.itertuples(index=False, name=None):
            pred = rows[(rows.season == season) & (rows['round'] == rd)].copy().sort_values('code')
            train, target = causal_training(rows, at, spec['horizon'], spec.get('window_days'))
            for model in spec['models']:
                features = schema[model['feature_set'] + '_features']
                cache_code = {n: h for n, h in contract['implementation'].items()
                              if n in ['model_lab/common.py', 'model_lab/forecast.py'] or n.startswith('datasets/')}
                key = {'model': {k: v for k, v in model.items() if k != 'id'}, 'origin': [season, int(rd), str(at)], 'horizon': spec['horizon'],
                    'window_days': spec.get('window_days'), 'inputs': spec['input_hashes'],
                    'explicit_attempt': spec.get('cache_attempt', 0),
                    'implementation': cache_code, 'runtime': contract['runtime']}
                cache = Path(output) / 'forecast_cache' / digest(key)
                if (cache / 'complete.json').exists():
                    receipt = read(cache / 'complete.json'); verify_files(cache, receipt['outputs'])
                    values = np.asarray(read(cache / 'predictions.json')['values'], float)
                    if read(cache / 'predictions.json')['keys'] != pred[KEY].values.tolist(): raise ValueError('Cache universe changed')
                    reused += 1
                else:
                    claim(cache, key)
                    t = time.monotonic(); values = fit_predict(train, pred, target, features, schema, model, pipeline)
                    audit = {'forecast_at': str(at), 'training_rows': len(train),
                        'latest_training_forecast': str(train.forecast_at.max()),
                        'latest_label_available': str(train[f'target_h{spec["horizon"]}_available_at'].max()),
                        'negative_training_labels': int((train[target] < 0).sum()), 'seconds': time.monotonic() - t,
                        'features': features, 'prediction_universe': 'observed player-round diagnostic rows, not a verified buyable roster'}
                    atomic_json(cache / 'predictions.json', {'keys': pred[KEY].values.tolist(), 'values': values.tolist()})
                    atomic_json(cache / 'audit.json', audit)
                    atomic_json(cache / 'complete.json', {'contract_hash': digest(key), 'outputs': {n: sha(cache / n) for n in ['predictions.json', 'audit.json']}})
                if values.shape != (len(pred),) or not np.isfinite(values).all(): raise ValueError('Invalid cached forecast')
                part = pred[KEY].copy(); part['model'] = model['id']; part['predicted_points'] = values
                part['actual_points'] = pred[target].to_numpy(); combined.append(part)
        predictions = pd.concat(combined, ignore_index=True)
        predictions.to_csv(directory / 'predictions.csv', index=False, lineterminator='\n')
        metrics = diagnostics(predictions)
        ref = {m['season']: m for m in metrics if m['model'] == spec['reference']}
        for m in metrics:
            m['rmse_delta_vs_reference'] = m['rmse'] - ref[m['season']]['rmse']
        summary = {'status': 'completed', 'purpose': spec['purpose'], 'metrics': metrics,
            'fits_requested': len(origins) * len(spec['models']), 'cached_folds_reused': reused,
            'seconds': time.monotonic() - started, 'process_cpu_seconds': time.process_time() - cpu,
            'model_promoted': False, 'interpretation': 'Paired forecast diagnostics only. No legal-manager or primary-benchmark superiority claim.'}
        atomic_json(directory / 'summary.json', summary)
        receipt = {'contract_hash': digest(contract), 'outputs': {n: sha(directory / n) for n in ['summary.json', 'predictions.csv']}}
        atomic_json(directory / 'complete.json', receipt)
        return dict(receipt, directory=str(directory), summary=summary)
    except Exception as exc:
        atomic_json(directory / 'failure.json', {'error': str(exc), 'type': type(exc).__name__, 'automatic_retry': False})
        raise
