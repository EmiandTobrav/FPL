"""One preregistered policy comparison; reuses forecasts, not old season scores."""
import os
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']:
    os.environ[name] = '1'
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
from itertools import combinations
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from model_lab.common import atomic_json, digest, read, sha, verify_files, runtime
from model_lab.simulation import backend, pool_input, BENCHMARK
_component_spec = importlib.util.spec_from_file_location('_learned_chip_component', HERE / 'policy.py')
component = importlib.util.module_from_spec(_component_spec); _component_spec.loader.exec_module(component)
CHIPS, FEATURES, fit, features, attach = component.CHIPS, component.FEATURES, component.fit, component.features, component.attach

OLD = ROOT / 'reports/fpl_simulator_2026_10_13'
CACHE = ROOT / 'reports/fpl_improvement_2026_10_14/cache'
PRIOR = ROOT / 'reports/fpl_improvement_2026_10_14/engine/runs'
SEASONS = ('2022-23', '2023-24', '2024-25')
CANDIDATE = 'learned_chip_wait_v1'


def prior_path(season):
    return PRIOR / f'manager__{season}__{BENCHMARK}__work_reference__f8678965bc35'


def state_json(state):
    state = copy.deepcopy(state)
    for k in ['owned', 'ownership_clubs']: state[k] = {int(i): v for i, v in state[k].items()}
    return state


def inputs(season, gw):
    d = CACHE / season / f'gw{gw:02d}'
    m = read(d / 'manifest.json')
    for name in ['pool.csv.gz', BENCHMARK + '.csv.gz', 'snapshot_audit.json']:
        if sha(d / name) != m['files'][name]: raise ValueError('Frozen forecast input changed')
    origin = {'forecast_at': m['forecast_at'], 'horizon': m['horizon'], 'pool': 'pool.csv.gz',
              'forecasts': {BENCHMARK: BENCHMARK + '.csv.gz'}}
    p, xp = pool_input(d, origin, BENCHMARK)
    return p, xp, m


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m


def settlement_helpers():
    # Existing imported definitions are used read-only; no archived runner is invoked.
    sys.path.insert(0, str(OLD))
    try: return module(OLD / 'run.py', '_learned_policy_settlement_helpers')
    finally: sys.path.remove(str(OLD))


def build_training_samples(seasons, cutoff, rules):
    """Monte Carlo value of waiting for the *observed baseline* chip use.

    No hindsight search for the best future round. Samples on baseline exercise
    dates or without observed later exercise are excluded, not labeled zero.
    This is a behavior-continuation surrogate, not an identified counterfactual.
    """
    master = pd.read_csv(ROOT / 'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz', usecols=['season', 'round', 'kickoff_time'])
    master['available'] = pd.to_datetime(master.kickoff_time, utc=True) + pd.Timedelta(hours=24)
    available = master.groupby(['season', 'round']).available.max()
    samples = []
    for season in seasons:
        if season >= cutoff[:7]: raise ValueError('Current/future season must not enter training')
        logs = {gw: read(prior_path(season) / f'gw{gw:02d}.json') for gw in range(1, 39)}
        for gw, log in logs.items():
            p, xp, m = inputs(season, gw); state = state_json(log['state_before'])
            x = features(p, xp, state, gw)
            end = 19 if gw <= 19 else 38
            for chip in CHIPS:
                if chip not in rules.available_chips(state, gw) or log['chip'] == chip: continue
                future = next((j for j in range(gw + 1, end + 1) if logs[j]['chip'] == chip), None)
                if future is None: continue
                target_log = logs[future]; choice = target_log['decision']; target_pool, _, _ = inputs(season, future)
                pos = dict(zip(target_pool.pid, target_pool.pos))
                outcomes = {int(r['code']): r for r in target_log['outcomes']}
                if any(not outcomes[i]['known'] for i in choice['squad']): raise ValueError('Unknown teacher outcome')
                points = {i: float(outcomes[i]['points']) for i in choice['squad']}
                active = {i: bool(outcomes[i]['appeared']) for i in choice['squad']}
                args = (choice['starters'], choice['bench'], choice['captain'], choice['vice'], pos, points, active)
                bonus = rules.settle(*args, chip)['gross'] - rules.settle(*args, None)['gross']
                at = available.loc[(season, future)]
                if not at < pd.Timestamp(cutoff): raise ValueError('Teacher label not available at fit time')
                samples.append({'season': season, 'round': gw, 'chip': chip, 'features': x,
                    'forecast_at': m['forecast_at'], 'future_exercise_round': future,
                    'incremental_bonus': bonus, 'wait_bonus': .9 ** (future - gw) * bonus,
                    'label_available_at': str(at), 'teacher_log_sha256': sha(prior_path(season) / f'gw{future:02d}.json')})
    return samples


def freeze():
    files = []
    for folder in [HERE, ROOT / 'model_lab']:
        files += [p for p in folder.rglob('*.py') if 'tests' not in p.parts]
    files += [ROOT / 'model_lab/vendor/fpl_rules_v1/PROVENANCE.json']
    files += [OLD / name for name in ['run.py', 'data_adapter.py', 'blank_settlement.py', 'forecast_adapter.py', 'engine.py', 'planner.py', 'policy.py', 'initial_optimizer.py']]
    files += [ROOT / 'datasets/fpl_2026_27_best_effort_v1' / n for n in ['manifest.json', 'player_rounds.csv.xz', 'player_matches.csv.xz']]
    files += [ROOT / 'reports/fpl_improvement_2026_10_14/evaluation/actual_s2_run_audit_v1.json']
    for season in SEASONS:
        files += [ROOT / f'FPL_training_dataset/research/current/project/data/{season}_{kind}.csv.gz' for kind in ['fixtures', 'teams']]
        files += [prior_path(season) / 'summary.json']
        for gw in range(1, 39):
            files += [CACHE / season / f'gw{gw:02d}' / n for n in ['manifest.json', 'pool.csv.gz', BENCHMARK + '.csv.gz', 'snapshot_audit.json']]
            files += [prior_path(season) / f'gw{gw:02d}.json']
    contract = {'version': 1, 'campaign': 'learned_manager_2026_10_15',
        'authorization': 'User requests learned manager policy with unchanged forecasts; matched data, seasons and resources.',
        'new_campaign_not_extension_of_old_configuration_cap': True, 'configurations': 1,
        'candidate': CANDIDATE, 'reference': BENCHMARK, 'seasons': list(SEASONS),
        'forecast_training_calls': 0, 'forecast': 'exact frozen benchmark arrays for every origin, both policies',
        'policy_intervention': 'Only reserve_value for TC and BB. All other fixed policy functions, constraints and existing future-option heuristic unchanged.',
        'learning': {'features': FEATURES, 'estimator': 'StandardScaler training-only + Ridge alpha10',
            'target': 'discounted realized incremental chip bonus at observed future benchmark exercise, same half; no hindsight best-round search',
            'discount': .9, 'alpha': 10., 'fit_rule': 'season-frozen, strictly prior seasons and labels available before GW1',
            'cold_2022_23': 'unchanged baseline reserve; explicit untrained parity control',
            'limitations': 'Small observational behavior-continuation surrogate; not end-to-end RL or identified counterfactual policy value.'},
        'resources': {'node_limit': 16, 'max_calls_per_decision': 40, 'threads': 1,
            'decision_workers': 1, 'policy_fit_cpu_seconds_per_season_cap_both': 5., 'automatic_retry': False,
            'actual_usage_recorded_not_claimed_equal': True},
        'primary_metric': 'paired full-season net points after hits; cold control shown separately',
        'pilot_success': 'both trained evaluation seasons positive and their mean positive; no automatic benchmark promotion',
        'stop': 'stop on any source change, future training label, invalid solve, unknown selected outcome or declared budget breach; no retry',
        'report_2025_26_not_read': True, 'no_hyperparameter_search': True,
        'runtime': runtime(), 'files': {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files))}}
    atomic_json(HERE / 'protocol.json', contract)
    return contract


def run():
    protocol = read(HERE / 'protocol.json'); verify_files(ROOT, protocol['files'])
    if runtime() != protocol['runtime']: raise ValueError('Runtime changed')
    atomic_json(HERE / 'started.json', {'protocol_sha256': sha(HERE / 'protocol.json'), 'automatic_retry': False})
    helpers = settlement_helpers(); store = helpers.OutcomeStore(ROOT)
    _, reference_adapter = backend(); rules = reference_adapter.engine
    for season in SEASONS:
        cutoff = read(CACHE / season / 'gw01/manifest.json')['forecast_at']
        previous = [s for s in SEASONS if s < season]
        samples = build_training_samples(previous, cutoff, rules) if previous else []
        atomic_json(HERE / 'training' / f'{season}_samples.json', samples)
        t = time.process_time(); models = fit(samples, cutoff)
        fit_cpu = time.process_time() - t
        if fit_cpu > 5.: raise ValueError('Policy fit CPU budget exceeded')
        atomic_json(HERE / 'training' / f'{season}_models.json', {'cutoff': cutoff, 'fit_cpu_seconds': fit_cpu, 'models': models})
        for candidate in [BENCHMARK, CANDIDATE]:
            out = HERE / 'runs' / f'{season}__{candidate}'
            atomic_json(out / 'started.json', {'protocol_sha256': sha(HERE / 'protocol.json')})
            state = rules.initial_state(); logs = []; start = time.monotonic(); cpu = time.process_time()
            for gw in range(1, 39):
                p, xp, manifest = inputs(season, gw); before_xp = digest(xp.tolist())
                m, adapter = backend(16, 40)
                trace = attach(adapter, models, p, xp, state, gw) if candidate == CANDIDATE else []
                if manifest.get('official_all_blank_forced_wait'):
                    # Same deterministic retained-squad wait as the frozen runner.
                    ids = sorted(state['owned']); pos = dict(zip(p.pid, p.pos))
                    start = next(list(c) for c in combinations(ids, 11) if rules.legal_positions(c, pos))
                    bench = sorted(set(ids) - set(start), key=lambda i: (pos[i] != 1, i))
                    result = {'chip': None, 'choice': {'squad': ids, 'starters': start, 'bench': bench,
                              'captain': start[0], 'vice': start[1]}}
                else: result = adapter.decide(p, xp, state, gw)
                if digest(xp.tolist()) != before_xp: raise ValueError('Forecast array was mutated')
                choice = result['choice']
                if 'prices' in choice: choice['prices'] = {int(k): int(v) for k, v in choice['prices'].items()}
                after, choice = rules.apply_decision(state, choice, p.to_dict('records'), gw, result['chip'])
                lock = m.clean({'gw': gw, 'candidate': candidate, 'state_before': state, 'state_after': after,
                    'decision': choice, 'chip': result['chip'], 'solver_calls': adapter.ledger,
                    'learned_reserves': trace, 'forecast_array_sha256': before_xp, 'outcomes_read': False})
                atomic_json(out / f'gw{gw:02d}.decision.json', lock)
                outcomes = helpers.enrich_outcomes(season, gw, store.for_round(season, gw, choice['squad']), p)
                settled = helpers.settle_rows({**choice, 'chip': result['chip']}, p, outcomes)
                row = {**lock, 'outcomes_read': True, 'outcomes': outcomes.astype(object).where(outcomes.notna(), None).to_dict('records'),
                    'settlement': settled, 'hit_cost': 4 * choice['paid'], 'net_points': settled['gross'] - 4 * choice['paid']}
                atomic_json(out / f'gw{gw:02d}.json', m.clean(row)); logs.append(row); state = after
                print(json.dumps({'season': season, 'policy': candidate, 'round': gw, 'settled': True}), flush=True)
            summary = {'season': season, 'policy': candidate, 'complete_season': len(logs) == 38,
                'net_points': float(sum(x['net_points'] for x in logs)), 'hit_cost': sum(x['hit_cost'] for x in logs),
                'seconds': time.monotonic() - start, 'decision_process_cpu_seconds': time.process_time() - cpu,
                'policy_fit_cpu_seconds': fit_cpu if candidate == CANDIDATE else 0.,
                'solver_calls': sum(len(x['solver_calls']) for x in logs),
                'learned_decision_rounds': sum(any(t['learned'] for t in x['learned_reserves']) for x in logs)}
            atomic_json(out / 'summary.json', summary)
    verify_files(ROOT, protocol['files'])
    atomic_json(HERE / 'complete.json', {'protocol_sha256': sha(HERE / 'protocol.json'), 'full_seasons': 6})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=['freeze', 'run']); args = parser.parse_args()
    try:
        freeze() if args.command == 'freeze' else run()
    except BaseException as exc:
        if args.command == 'run':
            atomic_json(HERE / 'failure.json', {'type': type(exc).__name__, 'error': str(exc), 'traceback': traceback.format_exc(), 'automatic_retry': False})
        raise
