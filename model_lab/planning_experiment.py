"""Frozen paired H2 planning experiment; no manager or forecast fitting."""
import os
for _k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_k] = '1'
import argparse
import copy
import time
from .common import ROOT, read, sha, digest, atomic_json, verify_files, runtime
from .simulation import backend, BENCHMARK
from .manager_learning import Environment, OLD, settle
from . import joint_planning as planner

HERE = ROOT / 'reports/explicit_planning_2026_10_15'
CANDIDATE = 'joint_plan_h2_no_reserve_v1'
CONTROL = 'joint_plan_h2_legacy_reserve_v1'
SEASONS = ('2022-23', '2023-24', '2024-25')


def preflight():
    env = Environment(); rows = []
    for gw in (1, 18, 19, 20, 38):
        pool, xp, manifest, _ = env.inputs(SEASONS[0], gw)
        state = env.e.state_json(read(OLD/'runs'/f'{SEASONS[0]}__{BENCHMARK}'/f'gw{gw:02d}.json')['state_before'])
        _, adapter = backend(16, 40)
        options = planner.plans(adapter, pool, xp, state, gw, bool(manifest.get('official_all_blank_forced_wait')))
        selected, scores = planner.select(options)
        rows.append({'gw': gw, 'plans': len(options), 'solver_calls': len(adapter.ledger),
                     'selected_schedule': options[selected]['schedule'], 'outcomes_read': False})
    atomic_json(HERE/'preflight.json', {'status': 'pass', 'checks': rows})


def freeze():
    from scripts import research
    if read(HERE/'preflight.json')['status'] != 'pass': raise ValueError('Preflight required')
    files = dict(read(OLD/'protocol.json')['files'])
    files.update(read(OLD/'result.json')['evidence_hashes'])
    paths = [p for p in (ROOT/'model_lab').rglob('*.py') if '__pycache__' not in p.parts]
    paths += [HERE/'preflight.json']
    files.update({str(p.relative_to(ROOT)): sha(p) for p in paths})
    verify_files(ROOT, files)
    protocol = {'id': 'explicit-planning-20261015-v1', 'candidate': CANDIDATE, 'control': CONTROL,
        'seasons': list(SEASONS), 'horizon': 2, 'forecast_fits': 0, 'manager_fits': 0,
        'resources': {'node_limit': 16, 'max_calls_per_decision': 40, 'threads': 1,
                      'maximum_full_seasons': 6, 'maximum_decisions': 228},
        'objective': 'Sum of expected counted player/captain points minus four per paid transfer, undiscounted. No reserve, bench bonus, transfer friction or learned correction.',
        'paired_control': 'Identical planner/forecasts/caps; subtract the pinned legacy reserve for chips in the proposed two-round schedule. This is an ablation, not the old benchmark algorithm.',
        'selection': 'Choose first action of highest scoring legal H2 plan; replan at next origin. H1 at GW38. All legal chip sequences enumerated. Official blank retains team.',
        'free_hit': 'Sequential segments restore original ownership/cash after FH; greedy between FH/non-FH segments, not joint global optimization across them.',
        'restrictions': 'Pinned shortlist; frozen current market/club/position/buyability at future offsets. Initially owned players cannot be rebought within a plan. Finite-node feasible incumbents, not optimality proof. Same-team BB/TC feasible variants improve weak incumbents without extra solves.',
        'terminal_limit': 'Two-round horizon has no learned terminal value and can be short-sighted; this is a mechanism test, not full-season optimal planning or a trained policy.',
        'comparison': 'New paired runs on all three development seasons. Reuse audited previous benchmark and learned-chip control only as secondary historical references; H2 vs H3 policy differs. No unseen-season generalization claim.',
        'success_criterion': 'Candidate strictly beats paired reserve control and both historical references in each season; otherwise no promotion. All legality, outcome, causality and resource checks pass.',
        'stop_rule': 'Stop on changed source/runtime, solver failure, unknown selected outcome, illegal action or budget breach. No retries or tuning.',
        'files': files, 'runtime': runtime()}
    atomic_json(HERE/'protocol.json', protocol)
    spec = {'id': protocol['id'], 'dataset_id': 'fpl_2026_27_best_effort_v1',
        'input_hashes': {'datasets/fpl_2026_27_best_effort_v1/manifest.json': sha(ROOT/'datasets/fpl_2026_27_best_effort_v1/manifest.json'),
                         str((HERE/'protocol.json').relative_to(ROOT)): sha(HERE/'protocol.json')},
        'clock': 'operational_proxy_v1', 'features': 'unchanged archived benchmark forecasts',
        'candidate_id': CANDIDATE, 'model_parameters': {'forecast_fits': 0, 'manager_fits': 0},
        'decision_policy': {'horizon': 2, 'objective': protocol['objective'], 'control': CONTROL},
        'benchmark_id': BENCHMARK, 'seasons': list(SEASONS), 'resources': protocol['resources'],
        'hypothesis': 'Eksplisitte chipplaner uten reservekostnader gir bedre sesongpoeng.',
        'change': 'Joint H2 point-only planning, explicit chip inventory and FH restoration; paired legacy reserve ablation.',
        'related_work': ['season-manager-20261015-v1', 'learned-manager-20261015-v1'],
        'success_criterion': protocol['success_criterion'], 'stop_rule': protocol['stop_rule'], 'maximum_runs': 6}
    fp = research.validate(spec); spec['fingerprint'] = fp
    proposal = ROOT/'experiments'/f'{fp}.proposal.json'; research.exclusive(proposal, spec)
    atomic_json(HERE/'registration.json', {'proposal': str(proposal.relative_to(ROOT)), 'fingerprint': fp})


def run():
    protocol = read(HERE/'protocol.json'); verify_files(ROOT, protocol['files'])
    if runtime() != protocol['runtime']: raise ValueError('Runtime changed')
    from scripts.research import fingerprint
    registration = read(HERE/'registration.json'); proposal = read(ROOT/registration['proposal'])
    if fingerprint(proposal) != registration['fingerprint'] or proposal['input_hashes'][str((HERE/'protocol.json').relative_to(ROOT))] != sha(HERE/'protocol.json'):
        raise ValueError('Registration changed')
    atomic_json(HERE/'started.json', {'protocol_sha256': sha(HERE/'protocol.json'), 'automatic_retry': False})
    env = Environment()
    try:
        for season in SEASONS:
            for name in (CONTROL, CANDIDATE):
                _, a = backend(); state = a.engine.initial_state(); logs = []
                started = time.monotonic(); cpu = time.process_time()
                directory = HERE/'runs'/f'{season}__{name}'
                for gw in range(1, 39):
                    pool, xp, manifest, _ = env.inputs(season, gw); _, adapter = backend(16, 40)
                    options = planner.plans(adapter, pool, xp, state, gw, bool(manifest.get('official_all_blank_forced_wait')))
                    j, scores = planner.select(options, adapter.policy.reserve_value if name == CONTROL else None)
                    selected = options[j]; step = selected['steps'][0]
                    lock = env.helpers.clean({'season': season, 'gw': gw, 'policy': name, 'state_before': state,
                        'forecast_at': manifest['forecast_at'], 'forecast_array_sha256': digest(xp.tolist()),
                        'options': options, 'selected_index': j, 'scores': scores,
                        'solver_calls': adapter.ledger, 'outcomes_read': False})
                    atomic_json(directory/f'gw{gw:02d}.decision.json', lock)
                    outcomes, settlement, net = settle(adapter, env, season, gw, step, pool)
                    row = {**lock, 'outcomes_read': True, 'outcomes': outcomes, 'settlement': settlement,
                           'net_points': net, 'state_after': env.helpers.clean(step['state_after'])}
                    atomic_json(directory/f'gw{gw:02d}.json', row)
                    logs.append(row); state = copy.deepcopy(step['state_after'])
                    print(season, name, f'GW{gw:02d}', flush=True)
                atomic_json(directory/'summary.json', {'season': season, 'policy': name,
                    'net_points': sum(r['net_points'] for r in logs), 'complete_season': True,
                    'solver_calls': sum(len(r['solver_calls']) for r in logs),
                    'solver_seconds': sum(c['seconds'] for r in logs for c in r['solver_calls']),
                    'wall_seconds': time.monotonic()-started, 'cpu_seconds': time.process_time()-cpu,
                    'chip_usage': {chip: [r['gw'] for r in logs if r['options'][r['selected_index']]['steps'][0]['choice']['chip'] == chip] for chip in adapter.engine.CHIPS}})
    except Exception as exc:
        atomic_json(HERE/'failure.json', {'season': season, 'policy': name, 'gw': gw, 'error': str(exc), 'type': type(exc).__name__, 'automatic_retry': False})
        raise


def audit():
    protocol = read(HERE/'protocol.json'); verify_files(ROOT, protocol['files'])
    env = Environment(); checked = 0; results = []; evidence = {}
    for season in SEASONS:
        reference = {}
        for name in (BENCHMARK, 'learned_chip_wait_v1'):
            rows = [read(OLD/'runs'/f'{season}__{name}'/f'gw{gw:02d}.json') for gw in range(1,39)]
            reference[name] = sum(r['net_points'] for r in rows)
        scores_by_policy = {}
        for name in (CONTROL, CANDIDATE):
            directory = HERE/'runs'/f'{season}__{name}'; _, a = backend(); state = a.engine.initial_state(); total = 0
            for gw in range(1,39):
                path = directory/f'gw{gw:02d}.json'; row = read(path); lockpath = directory/f'gw{gw:02d}.decision.json'; lock = read(lockpath)
                if any(row[k] != v for k,v in lock.items() if k != 'outcomes_read') or lock['outcomes_read']:
                    raise ValueError('Locked decision changed')
                if env.e.state_json(row['state_before']) != state: raise ValueError('State discontinuity')
                pool, xp, manifest, _ = env.inputs(season,gw)
                if digest(xp.tolist()) != row['forecast_array_sha256'] or row['forecast_at'] != manifest['forecast_at']: raise ValueError('Input mismatch')
                if not manifest.get('official_all_blank_forced_wait'):
                    expected_schedules = {tuple(s) for s in planner.schedules(a.engine,state,gw,min(2,39-gw))}
                    actual_schedules = [tuple(o['schedule']) for o in row['options']]
                    if len(actual_schedules) != len(expected_schedules) or set(actual_schedules) != expected_schedules:
                        raise ValueError('Incomplete/duplicate schedule enumeration')
                for option in row['options']:
                    current = copy.deepcopy(state); expected = 0.
                    if not manifest.get('official_all_blank_forced_wait') and option['schedule'] not in planner.schedules(a.engine,state,gw,min(2,39-gw)):
                        raise ValueError('Illegal schedule')
                    for step in option['steps']:
                        if env.e.state_json(step['state_before']) != current: raise ValueError('Invalid future opening')
                        choice = copy.deepcopy(step['choice']); choice['prices'] = {int(k):v for k,v in choice['prices'].items()}
                        after, legal = a.engine.apply_decision(current, choice, pool.to_dict('records'), step['gw'], choice['chip'])
                        if after != env.e.state_json(step['state_after']): raise ValueError('Invalid future state')
                        points = planner.expected_points(legal,pool,xp[:,step['gw']-gw])
                        if abs(points-step['expected_net_points']) > 1e-5: raise ValueError('Non-point objective')
                        expected += points; current = after
                    if abs(expected-option['expected_net_points']) > 1e-5: raise ValueError('Invalid plan sum')
                j,scores = planner.select(row['options'],a.policy.reserve_value if name==CONTROL else None)
                if j != row['selected_index'] or scores != row['scores']: raise ValueError('Selection mismatch')
                if len(row['solver_calls']) > 40 or any(c['nodes'] > 16 or not c['full_mip_feasible'] for c in row['solver_calls']): raise ValueError('Resource/feasibility breach')
                step = row['options'][j]['steps'][0]
                outcomes,settlement,net = settle(a,env,season,gw,step,pool)
                if outcomes != row['outcomes'] or env.helpers.clean(settlement) != row['settlement'] or net != row['net_points']: raise ValueError('Settlement mismatch')
                if row['state_after'] != step['state_after']: raise ValueError('Selected transition changed')
                state = env.e.state_json(row['state_after']); total += net; checked += 1
                evidence[str(path.relative_to(ROOT))] = sha(path); evidence[str(lockpath.relative_to(ROOT))] = sha(lockpath)
            summarypath = directory/'summary.json'; summary = read(summarypath)
            if summary['net_points'] != total: raise ValueError('Total mismatch')
            scores_by_policy[name] = total; evidence[str(summarypath.relative_to(ROOT))] = sha(summarypath)
        results.append({'season': season, **scores_by_policy, **reference,
                        'gain_vs_reserve': scores_by_policy[CANDIDATE]-scores_by_policy[CONTROL],
                        'gain_vs_benchmark': scores_by_policy[CANDIDATE]-reference[BENCHMARK],
                        'gain_vs_chip_policy': scores_by_policy[CANDIDATE]-reference['learned_chip_wait_v1']})
    atomic_json(HERE/'audit.json', {'status':'pass','rounds_recomputed':checked,'all_saved_plans_revalidated':True,'results':results,'evidence_hashes':evidence})
    print(results,flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action',choices=['preflight','freeze','run','audit'])
    globals()[parser.parse_args().action]()
