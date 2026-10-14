"""One shared policy and rule engine; models only supply origin-time forecasts."""
from pathlib import Path
import copy
import importlib.util
from itertools import combinations
import shutil
import time
import numpy as np
import pandas as pd
from .common import ROOT, read, sha, digest, resolve, verify_files, atomic_json, runtime, implementation, claim

BENCHMARK = 'fixture_full_h3_adaptive_tc_harmonized_causal_v1'
VENDOR = Path(__file__).parent / 'vendor/fpl_rules_v1'


def backend(node_limit=16, max_calls=40):
    provenance = read(VENDOR / 'PROVENANCE.json')
    verify_files(VENDOR, {n: r['sha256'] for n, r in provenance['files'].items()})
    spec = importlib.util.spec_from_file_location('_lab_controlled_policy', VENDOR / 'controlled_policy_v1.py')
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module; spec.loader.exec_module(module)
    module.OLD = VENDOR
    return module, module.ControlledPolicy(module.Budget(node_limit=node_limit, max_calls=max_calls))


def pool_input(bundle, origin, model):
    directory = Path(bundle)
    p = pd.read_csv(resolve(directory, origin['pool']))
    f = pd.read_csv(resolve(directory, origin['forecasts'][model]))
    if p.code.duplicated().any() or f.code.duplicated().any() or p.code.tolist() != f.code.tolist():
        raise ValueError('Pool and forecast must have identical unique ordered codes')
    at = pd.Timestamp(origin['forecast_at'])
    if at.tzinfo is None or not (pd.to_datetime(f.forecast_at, utc=True) == at).all(): raise ValueError('Wrong forecast origin')
    cols = [f'xp_{i}' for i in range(origin['horizon'])]
    if [c for c in f if c.startswith('xp_')] != cols: raise ValueError('Invalid trajectory horizon')
    if 'metadata_complete' in p: p = p[p.metadata_complete].copy()
    if p.empty: raise ValueError('Empty decision pool')
    for col in ['price_available_at', 'position_available_at', 'club_available_at']:
        if not (pd.to_datetime(p[col], utc=True) < at).all(): raise ValueError(f'Future or missing pool metadata: {col}')
    for col in ['pid', 'pos', 'market']: p[col] = p[col].astype(int)
    if not p.can_buy.isin([True, False]).all(): raise ValueError('Invalid buyability')
    p['can_buy'] = p.can_buy.astype(bool)
    xp = f.set_index('code').loc[p.code, cols].to_numpy(float)
    if not np.isfinite(xp).all(): raise ValueError('Missing forecast values')
    return p.sort_values('code').reset_index(drop=True), xp[np.argsort(p.code.to_numpy())]


def export_cache(cache, season, rounds, models, output):
    """Copy a bounded set of already-frozen origins; never rebuild old forecasts."""
    cache = Path(cache); output = Path(output)
    if output.exists(): raise ValueError('Use a fresh bundle directory')
    if rounds != list(range(rounds[0], rounds[-1] + 1)) or rounds[0] != 1:
        raise ValueError('Independent manager bundles must start GW1 and be contiguous')
    if BENCHMARK not in models or len(set(models)) != len(models): raise ValueError('Include the active benchmark exactly once')
    bank = ROOT / 'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz'
    labels = pd.read_csv(bank, usecols=['season', 'round', 'code', 'target_total_points', 'native_minutes', 'native_yellow_cards', 'native_red_cards'])
    output.mkdir(parents=True); files = {}; origins = []
    for gw in rounds:
        source = cache / season / f'gw{gw:02d}'; manifest = read(source / 'manifest.json')
        if manifest['season'] != season or manifest['round'] != gw: raise ValueError('Source origin mismatch')
        verify_files(source, manifest['files'])
        folder = output / f'gw{gw:02d}'; folder.mkdir()
        names = ['pool.csv.gz', 'features.csv.gz', 'snapshot_audit.json'] + [m + '.csv.gz' for m in models]
        for name in names:
            if name not in manifest['files']: raise ValueError('Required payload not bound in source manifest')
            shutil.copy2(resolve(source, name), folder / name)
        shutil.copy2(source / 'manifest.json', folder / 'source_manifest.json')
        subset = labels[(labels.season == season) & (labels['round'] == gw)]
        if subset.code.duplicated().any(): raise ValueError('Duplicate outcome keys')
        outcomes = {}
        for row in subset.itertuples(index=False):
            if any(pd.isna(v) for v in [row.target_total_points, row.native_minutes, row.native_yellow_cards, row.native_red_cards]): continue
            outcomes[str(int(row.code))] = {'points': float(row.target_total_points),
                'active': bool(row.native_minutes > 0 or row.native_yellow_cards > 0 or row.native_red_cards > 0)}
        blank = bool(manifest.get('official_all_blank_forced_wait', False))
        if blank:
            audit = read(folder / 'snapshot_audit.json')
            if (season, gw) != ('2022-23', 7) or not audit.get('official_all_blank'): raise ValueError('Unqualified blanket zero')
            if outcomes: raise ValueError('Blank conflicts with observed outcomes')
            outcomes = {str(int(i)): {'points': 0., 'active': False} for i in pd.read_csv(folder / 'pool.csv.gz').code}
        atomic_json(folder / 'outcomes.json', outcomes)
        for p in folder.iterdir(): files[str(p.relative_to(output))] = sha(p)
        prefix = f'gw{gw:02d}/'
        origins.append({'season': season, 'round': gw, 'forecast_at': manifest['forecast_at'],
            'horizon': manifest['horizon'], 'pool': prefix + 'pool.csv.gz', 'features': prefix + 'features.csv.gz',
            'outcomes': prefix + 'outcomes.json', 'official_blank': blank,
            'forecasts': {m: prefix + m + '.csv.gz' for m in models}})
    atomic_json(output / 'bundle.json', {'version': 1, 'benchmark': BENCHMARK, 'origins': origins, 'files': files,
        'outcome_bank_sha256': sha(bank), 'scope': 'Frozen existing research-proxy decision inputs; source manifests retain provenance. Not proof of verified historical buyability.'})
    return str(output / 'bundle.json')


def add_forecasts(spec, bundle, output):
    """Fit from causal history and predict the frozen pool at each existing origin."""
    from .forecast import validate, pipeline_modules, causal_training, fit_predict
    validate(spec)
    if spec['horizon'] != 1 or spec.get('trajectory') != 'repeat_h1_diagnostic':
        raise ValueError('Built-in trajectory is explicitly repeated H1 only; fixture-aware adapters need a separately validated extension')
    bundle = Path(bundle); output = Path(output); source = read(bundle / 'bundle.json'); verify_files(bundle, source['files'])
    if spec['clock'] != 'operational_proxy_v1': raise ValueError('Bundle origins use operational_proxy_v1')
    if len(source['origins']) * len(spec['models']) > spec['max_fits']: raise ValueError('Fit budget exceeded')
    if output.exists(): raise ValueError('Use a fresh output bundle')
    loader, pipeline = pipeline_modules(); rows, schema = loader.load_rows(clock=spec['clock'])
    output.mkdir(parents=True)
    for rel in source['files']:
        dest = output / rel; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(resolve(bundle, rel), dest)
    updated = copy.deepcopy(source)
    for origin in updated['origins']:
        if origin['season'] not in spec['seasons'] or origin['round'] not in spec['rounds']: raise ValueError('Bundle outside declared forecast origins')
        at = pd.Timestamp(origin['forecast_at']); train, target = causal_training(rows, at, 1, spec.get('window_days'))
        pred = pd.read_csv(resolve(output, origin['features']))
        if not (pd.to_datetime(pred.forecast_at, utc=True) == at).all(): raise ValueError('Feature origin mismatch')
        for model in spec['models']:
            if model['id'] in origin['forecasts']: raise ValueError('Cannot replace an existing frozen forecast')
            values = fit_predict(train, pred, target, schema[model['feature_set'] + '_features'], schema, model, pipeline)
            result = pred[['code', 'forecast_at']].copy()
            for j in range(origin['horizon']): result[f'xp_{j}'] = values
            rel = f'gw{origin["round"]:02d}/{model["id"]}.csv.gz'
            result.to_csv(output / rel, index=False, compression={'method': 'gzip', 'mtime': 0}, lineterminator='\n')
            origin['forecasts'][model['id']] = rel
            updated['files'][rel] = sha(output / rel)
    updated['new_forecast_contract'] = {'spec': spec, 'runtime': runtime(), 'implementation': implementation(),
        'trajectory': 'H1 repeated at the current origin; diagnostic proxy, not independently calibrated fixture trajectories'}
    atomic_json(output / 'bundle.json', updated)
    return str(output / 'bundle.json')


def run(spec, output):
    bundle = resolve(ROOT, spec['bundle']).parent; manifest = read(bundle / 'bundle.json')
    if sha(bundle / 'bundle.json') != spec['bundle_sha256']: raise ValueError('Bundle contract changed')
    verify_files(bundle, manifest['files'])
    if spec.get('purpose') not in ['framework_validation', 'registered_research']: raise ValueError('Declare simulation purpose')
    if spec['purpose'] == 'registered_research':
        from scripts.research import fingerprint
        proposal = read(resolve(ROOT, spec['proposal']))
        if proposal.get('fingerprint') != spec.get('proposal_fingerprint') or fingerprint(proposal) != proposal['fingerprint']: raise ValueError('Registered proposal changed')
        if proposal['candidate_id'] not in spec['models'] or proposal['benchmark_id'] != spec['reference']: raise ValueError('Proposal models mismatch')
        if spec['max_decisions'] > proposal['resources'].get('maximum_decisions', 0): raise ValueError('Proposal decision budget missing/exceeded')
        bound = str((bundle / 'bundle.json').relative_to(ROOT))
        if proposal['input_hashes'].get(bound) != spec['bundle_sha256']: raise ValueError('Proposal must bind simulation bundle')
        policy = {k: spec[k] for k in ['policy', 'node_limit', 'max_calls_per_decision', 'fixed_chips'] if k in spec}
        if proposal['decision_policy'] != policy: raise ValueError('Proposal policy mismatch')
    if spec['reference'] != manifest['benchmark'] or spec['reference'] not in spec['models']: raise ValueError('Use the supplied active benchmark')
    if len(set(spec['models'])) != len(spec['models']): raise ValueError('Duplicate models')
    if spec.get('policy') not in ['adaptive', 'fixed']: raise ValueError('Declare shared policy')
    origins = manifest['origins']
    if not origins or len(origins) * len(spec['models']) > spec['max_decisions']: raise ValueError('Decision budget exceeded')
    if len({o['season'] for o in origins}) != 1 or [o['round'] for o in origins] != list(range(1, len(origins) + 1)):
        raise ValueError('One season per run, contiguous from GW1; no invented missing origins')
    times = [pd.Timestamp(o['forecast_at']) for o in origins]
    if any(a >= b for a, b in zip(times, times[1:])): raise ValueError('Origins must increase')
    for o in origins:
        if any(m not in o['forecasts'] for m in spec['models']): raise ValueError('Model coverage differs')
        if any(name not in manifest['files'] for name in [o['pool'], o['outcomes'], *o['forecasts'].values()]):
            raise ValueError('Unbound bundle payload')
    contract = {'spec': spec, 'runtime': runtime(), 'implementation': implementation()}
    directory = Path(output) / 'simulations' / digest(contract)
    prior = claim(directory, contract)
    if prior: return dict(prior, reused_completed_run=True, directory=str(directory))
    started = time.monotonic(); totals = []; logs = []
    try:
        fixed = {int(k): v for k, v in spec.get('fixed_chips', {}).items()}
        for model in spec['models']:
            module, adapter = backend(spec['node_limit'], spec['max_calls_per_decision'])
            state = adapter.engine.initial_state(); total = 0.; calls = 0
            for origin in origins:
                pool, xp = pool_input(bundle, origin, model)
                if not set(state['owned']) <= set(pool.pid): raise ValueError('Held metadata missing from common pool')
                adapter.ledger.clear()
                if origin.get('official_blank'):
                    if not state['owned']: raise ValueError('Blank needs an inherited owned squad')
                    pos = dict(zip(pool.pid, pool.pos)); ids = sorted(state['owned'])
                    start = next((list(c) for c in combinations(ids, 11) if adapter.engine.legal_positions(c, pos)), None)
                    if start is None: raise ValueError('No legal retained lineup')
                    bench = sorted(set(ids) - set(start), key=lambda i: (pos[i] != 1, i))
                    decision = {'chip': None, 'squad': ids, 'starters': start, 'bench': bench, 'captain': start[0], 'vice': start[1]}
                else:
                    planned = adapter.decide(pool, xp, state, origin['round']) if spec['policy'] == 'adaptive' else adapter.plan(pool, xp, state, origin['round'], fixed.get(origin['round']), fixed)
                    decision = copy.deepcopy(planned['choice'])
                    # The existing adapter serializes integer price keys for JSON.
                    # Restore the pure rule engine's integer-key API boundary.
                    if 'prices' in decision:
                        decision['prices'] = {int(k): int(v) for k, v in decision['prices'].items()}
                atomic_json(directory / 'locked_decisions' / model / f'gw{origin["round"]:02d}.json',
                    module.clean({'decision': decision, 'state_before': state, 'solver': adapter.ledger,
                                  'forecast_at': origin['forecast_at'], 'outcomes_read': False}))
                # Outcomes are loaded only after the outcome-blind decision has finished.
                outcomes = {int(k): v for k, v in read(resolve(bundle, origin['outcomes'])).items()}
                after, log = adapter.engine.play_round(state, decision, pool.to_dict('records'), outcomes, origin['round'])
                log['model'] = model; log['solver'] = copy.deepcopy(adapter.ledger)
                logs.append(module.clean(log)); calls += len(adapter.ledger); total += float(log['net_points']); state = after
            totals.append({'model': model, 'net_points': total, 'rounds': len(origins), 'solver_calls': calls,
                'complete_season': len(origins) == 38, 'season': origins[0]['season']})
        reference = next(r['net_points'] for r in totals if r['model'] == spec['reference'])
        for row in totals: row['gain_vs_reference'] = row['net_points'] - reference
        atomic_json(directory / 'decisions.json', logs)
        atomic_json(directory / 'summary.json', {'status': 'completed', 'purpose': spec['purpose'], 'results': totals,
            'seconds': time.monotonic() - started, 'benchmark_promoted': False,
            'interpretation': 'Frozen-proxy legal manager validation; partial scores are not full-season results. Equal node/call caps do not imply equal total compute.'})
        receipt = {'contract_hash': digest(contract), 'outputs': {n: sha(directory / n) for n in ['decisions.json', 'summary.json']}}
        atomic_json(directory / 'complete.json', receipt)
        return dict(receipt, directory=str(directory))
    except Exception as exc:
        atomic_json(directory / 'failure.json', {'error': str(exc), 'type': type(exc).__name__, 'automatic_retry': False,
                    'model': locals().get('model'), 'origin': locals().get('origin')})
        raise
