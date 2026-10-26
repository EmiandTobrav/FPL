"""Registered H3 rollout pilot: prepare, run, audit. No automatic retries."""
import os
for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_key] = '1'
import argparse
import copy
import time
import traceback
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from .common import ROOT, read, sha, digest, atomic_json, verify_files, runtime
from .simulation import backend, BENCHMARK
from .manager_learning import Environment, settle
from . import manager_policy as base
from . import rollout_policy as rollout

HERE = ROOT / 'reports/rollout_2026_10_15'
PRIOR = ROOT / 'reports/season_manager_2026_10_15'
SEASONS = ('2023-24', '2024-25')
ID = 'rollout-h3-20261015-v1'
CONTROL = 'same_proposals_unlearned_v1'
CANDIDATE = 'bounded_rollout_h3_v1'


def previous(season):
    return PRIOR/'episodes'/f'eval__{season}__{CONTROL}'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def prepare():
    if (HERE/'protocol.json').exists():
        raise ValueError('Already frozen; do not overwrite')
    env = Environment(); probes = []
    # Outcome-blind parity at existing states, no new comparative score.
    for season, gw in [('2023-24', 1), ('2023-24', 19), ('2024-25', 38)]:
        archived = read(previous(season)/f'gw{gw:02d}.decision.json')
        pool, xp, manifest, history = env.inputs(season, gw)
        state = env.e.state_json(archived['state_before'])
        _, adapter = backend(16, 200)
        result = rollout.choose(adapter, pool, xp, history, state, gw)
        if env.helpers.clean(result['options']) != archived['options']:
            raise ValueError('Root proposals differ from audited control')
        if result['control_index'] != archived['selected_index']:
            raise ValueError('Reference selection differs')
        probes.append({'season': season, 'gw': gw, 'root_proposals_match': True,
                       'calls': len(adapter.ledger), 'outcomes_read': False})
    atomic_json(HERE/'preflight.json', {'status': 'pass', 'probes': probes})
    # Pin existing data/settlement dependencies and exact reusable control logs.
    files = dict(read(PRIOR/'protocol.json')['files'])
    files.update({str(p.relative_to(ROOT)): sha(p) for p in (ROOT/'model_lab').rglob('*.py')})
    files.update({str(p.relative_to(ROOT)): sha(p) for p in [HERE/'preflight.json', PRIOR/'audit.json', PRIOR/'results.csv']})
    for season in SEASONS:
        for p in previous(season).glob('*.json'):
            files[str(p.relative_to(ROOT))] = sha(p)
    if read(PRIOR/'audit.json')['status'] != 'pass':
        raise ValueError('Prior audit missing')
    verify_files(ROOT, files)
    protocol = {
        'id': ID, 'candidate': CANDIDATE, 'seasons': list(SEASONS), 'runtime': runtime(), 'files': files,
        'created_at_utc': stamp(), 'authorization': 'User requests documenting and starting the sequential test program.',
        'separate_campaign': True, 'configurations': 1, 'previous_campaign_limits_unchanged': True,
        'intervention': 'Same root proposals; top two distinct after-states by base_score, always including base winner. Rank by deterministic truncated unlearned-policy continuation.',
        'forecast': 'Unchanged benchmark; root proposal generator uses original full trajectory. Continuation sees only current-origin columns within H3; no future-origin files.',
        'future_information': 'Freeze pool, prices, can_buy and history. No hypothetical future actual outcomes, injuries or news.',
        'utility': 'Same .9 discount and original reserve_value; sum current plus two continuation net-xp-minus-reserve rewards; zero terminal value. Not a pure-points or learned-terminal experiment.',
        'controls': {'primary': CONTROL, 'secondary': [BENCHMARK, 'learned_chip_wait_v1']},
        'reuse': 'Primary two complete audited episodes reused byte-for-byte, with outcome-blind root-proposal parity probes and full saved-log verification. No existing source edited.',
        'resources': {'threads': 1, 'node_limit': 16, 'root_call_cap': 40, 'continuation_call_cap': 40,
                      'total_call_cap_per_origin': 200, 'new_full_seasons': 2, 'new_decisions': 76,
                      'forecast_fits': 0, 'policy_fits': 0, 'branch_width': 2, 'horizon': 3},
        'resource_interpretation': 'Same per-MIP resources, extra continuation work explicitly charged to candidate; not equal-total-compute evidence.',
        'pilot_success': 'Positive full-season net gain against primary control in both seasons; retain for research only, never automatic promotion.',
        'stop': 'Fail on source/runtime change, invalid transition, unknown selected outcome, solver failure or resource violation. No retry, tuning or silent fallback.',
        'limitations': 'Previously studied development years; frozen deterministic futures; no uncertainty calibration or rollout improvement theorem; primary control is proposal policy, not legacy benchmark.',
    }
    atomic_json(HERE/'protocol.json', protocol)
    proposal = {
        'id': ID, 'candidate_id': CANDIDATE, 'dataset_id': 'fpl_2026_27_best_effort_v1',
        'benchmark_id': BENCHMARK, 'clock': 'operational_proxy_v1', 'features': 'unchanged frozen forecasts and origin history',
        'hypothesis': 'Avgrenset H3-rollout forbedrer netto sesongpoeng mot samme forslag uten læring.',
        'change': protocol['intervention'], 'related_work': ['season-manager-20261015-v1', 'explicit-planning-20261015-v1'],
        'input_hashes': {**files, str((HERE/'protocol.json').relative_to(ROOT)): sha(HERE/'protocol.json')},
        'model_parameters': {'forecast': 'unchanged', 'fits': 0},
        'decision_policy': {'horizon': 3, 'width': 2, 'continuation': CONTROL, 'discount': .9},
        'seasons': list(SEASONS), 'resources': protocol['resources'], 'maximum_runs': 2,
        'success_criterion': protocol['pilot_success'], 'stop_rule': protocol['stop'],
    }
    atomic_json(HERE/'proposal_input.json', proposal)
    from scripts.research import validate, exclusive, RECORDS, refresh
    fp = validate(proposal)
    proposal.update(fingerprint=fp, registered_at_utc=stamp())
    dest = RECORDS/(fp+'.proposal.json'); exclusive(dest, proposal)
    atomic_json(HERE/'registration.json', {'fingerprint': fp, 'proposal': str(dest.relative_to(ROOT))})
    refresh()
    print('Registered', ID, flush=True)


def bound():
    protocol = read(HERE/'protocol.json'); verify_files(ROOT, protocol['files'])
    if protocol['runtime'] != runtime():
        raise ValueError('Runtime changed')
    from scripts.research import fingerprint
    registration = read(HERE/'registration.json'); proposal = read(ROOT/registration['proposal'])
    if fingerprint(proposal) != registration['fingerprint'] or proposal['input_hashes'][str((HERE/'protocol.json').relative_to(ROOT))] != sha(HERE/'protocol.json'):
        raise ValueError('Registration mismatch')
    return protocol


def run():
    bound()
    atomic_json(HERE/'started.json', {'at_utc': stamp(), 'protocol_sha256': sha(HERE/'protocol.json')})
    env = Environment()
    for season in SEASONS:
        _, rules_adapter = backend(); state = rules_adapter.engine.initial_state()
        logs = []; started = time.monotonic(); cpu = time.process_time()
        directory = HERE/'runs'/season
        for gw in range(1, 39):
            pool, xp, manifest, history = env.inputs(season, gw)
            _, adapter = backend(16, 200)
            calls = []
            def limited_proposals(*args, **kwargs):
                before = len(adapter.ledger)
                options = base.proposals(*args, **kwargs)
                count = len(adapter.ledger)-before
                if count > 40: raise ValueError('Per-proposal call cap exceeded')
                calls.append(count)
                return options
            selected = rollout.choose(adapter, pool, xp, history, state, gw,
                official_blank=bool(manifest.get('official_all_blank_forced_wait')), proposals=limited_proposals)
            lock = env.helpers.clean({**selected, 'season': season, 'gw': gw, 'state_before': state,
                'forecast_at': manifest['forecast_at'], 'forecast_array_sha256': digest(xp.tolist()),
                'solver_calls': adapter.ledger, 'proposal_call_counts': calls, 'outcomes_read': False})
            atomic_json(directory/f'gw{gw:02d}.decision.json', lock)
            outcomes, settlement, net = settle(adapter, env, season, gw, selected['selected'], pool)
            row = {**lock, 'outcomes_read': True, 'outcomes': outcomes,
                   'settlement': env.helpers.clean(settlement), 'net_points': net}
            atomic_json(directory/f'gw{gw:02d}.json', row)
            state = selected['selected']['after']; logs.append(row)
            print(f'{season} GW{gw:02d}: locked and settled; calls={len(adapter.ledger)}', flush=True)
        atomic_json(directory/'summary.json', {'season': season, 'net_points': sum(r['net_points'] for r in logs),
            'seconds': time.monotonic()-started, 'cpu_seconds': time.process_time()-cpu,
            'calls': sum(len(r['solver_calls']) for r in logs), 'rounds': len(logs)})
    bound()
    atomic_json(HERE/'complete.json', {'at_utc': stamp(), 'seasons': 2, 'decisions': 76,
                                      'protocol_sha256': sha(HERE/'protocol.json')})


def audit():
    bound(); complete = read(HERE/'complete.json')
    if complete['protocol_sha256'] != sha(HERE/'protocol.json'):
        raise ValueError('Wrong completion')
    env = Environment(); _, adapter = backend(16, 200); rules = adapter.engine
    results = []; rounds = []; verified = 0

    def option_check(option, pool, xp, history, state, gw, blank=False):
        choice = copy.deepcopy(option['choice'])
        choice['prices'] = {int(k): v for k, v in choice['prices'].items()}
        after, legal = rules.apply_decision(state, choice, pool.to_dict('records'), gw)
        if after != env.e.state_json(option['after']) or base.identity(legal) != option['id']:
            raise ValueError('Illegal action/transition')
        x = base.encode(pool, xp, history, state, after, legal, rules, gw)
        reserve = 0. if legal['chip'] is None else adapter.policy.reserve_value(legal['chip'], gw)
        score = 0. if blank else 100*x[9]+.9*100*x[14]+.81*100*x[15]-reserve
        if x != option['features'] or abs(score-option['base_score']) > 1e-9:
            raise ValueError('Changed base features/score')
        return after

    for season in SEASONS:
        totals = {}
        for label, folder in [('control', previous(season)), ('candidate', HERE/'runs'/season)]:
            state = rules.initial_state(); total = 0.
            for gw in range(1, 39):
                lock = read(folder/f'gw{gw:02d}.decision.json'); row = read(folder/f'gw{gw:02d}.json')
                if lock['outcomes_read'] or not row['outcomes_read'] or any(row[k] != v for k,v in lock.items() if k != 'outcomes_read'):
                    raise ValueError('Outcome barrier/lock changed')
                pool, xp, manifest, history = env.inputs(season, gw)
                if state != env.e.state_json(lock['state_before']) or lock['forecast_array_sha256'] != digest(xp.tolist()) or lock['forecast_at'] != manifest['forecast_at']:
                    raise ValueError('State chain/forecast mismatch')
                blank = bool(manifest.get('official_all_blank_forced_wait'))
                for option in lock['options']:
                    option_check(option, pool, xp, history, state, gw, blank)
                control_index = base.select(lock['options'], None)[0]
                if label == 'candidate':
                    if lock['control_index'] != control_index or lock['shortlist'] != rollout.shortlist(lock['options']):
                        raise ValueError('Shortlist changed')
                    if [b['root_index'] for b in lock['branches']] != lock['shortlist']:
                        raise ValueError('Missing branch')
                    horizon = min(3, xp.shape[1], 39-gw)
                    for branch in lock['branches']:
                        current = copy.deepcopy(state); score = 0.
                        if len(branch['steps']) != (1 if blank else horizon):
                            raise ValueError('Incomplete continuation')
                        for offset, step in enumerate(branch['steps']):
                            if step['gw'] != gw+offset or env.e.state_json(step['state_before']) != current:
                                raise ValueError('Branch chronology broken')
                            if offset == 0:
                                if step['selected'] != lock['options'][branch['root_index']]: raise ValueError('Wrong root action')
                            else:
                                for option in step['options']:
                                    option_check(option, pool, xp[:,offset:horizon], history, current, gw+offset)
                                j = base.select(step['options'], None)[0]
                                if j != step['selected_index'] or step['selected'] != step['options'][j]:
                                    raise ValueError('Continuation differs from base policy')
                            current = env.e.state_json(step['selected']['after'])
                            value = 0. if blank else rollout.reward(step['selected'], pool, xp[:,offset], adapter.policy.reserve_value, gw+offset)
                            if abs(value-step['reward']) > 1e-9: raise ValueError('Wrong branch reward')
                            score += .9**offset*value
                        if abs(score-branch['score']) > 1e-8: raise ValueError('Wrong rollout score')
                    best = max(lock['branches'], key=lambda b:(b['score'], b['root_index']==control_index, lock['options'][b['root_index']]['id']))
                    if lock['selected_index'] != best['root_index']: raise ValueError('Wrong rollout selection')
                    if max(lock['proposal_call_counts']) > 40 or sum(lock['proposal_call_counts']) != len(lock['solver_calls']) or len(lock['solver_calls']) > 200:
                        raise ValueError('Resource cap violated')
                    rounds.append({'season': season, 'gw': gw, 'changed_from_same_state_control': lock['selected_index'] != control_index,
                        'chip': lock['selected']['choice']['chip'], 'paid': lock['selected']['choice']['paid'],
                        'transfers': lock['selected']['choice']['transfers'], 'calls': len(lock['solver_calls']), 'net_points': row['net_points']})
                elif lock['selected_index'] != control_index:
                    raise ValueError('Reused control is not unlearned selection')
                if lock['selected'] != lock['options'][lock['selected_index']]: raise ValueError('Selected payload mismatch')
                for call in lock['solver_calls']:
                    if call['options'] != adapter.options or call['nodes'] > 16 or not call['full_mip_feasible']:
                        raise ValueError('Solver contract violated')
                outcomes, settled, net = settle(adapter, env, season, gw, lock['selected'], pool)
                if outcomes != row['outcomes'] or env.helpers.clean(settled) != row['settlement'] or net != row['net_points']:
                    raise ValueError('Settlement changed')
                total += net; state = env.e.state_json(lock['selected']['after']); verified += 1
            if total != read(folder/'summary.json')['net_points']: raise ValueError('Summary wrong')
            totals[label] = total
        old = pd.read_csv(PRIOR/'results.csv').set_index('season').loc[season]
        results.append({'season': season, **totals, 'difference': totals['candidate']-totals['control'],
                        'benchmark': float(old[BENCHMARK]), 'chip_policy': float(old['learned_chip_wait_v1'])})
    pd.DataFrame(results).to_csv(HERE/'results.csv', index=False)
    pd.DataFrame(rounds).to_csv(HERE/'rounds.csv', index=False)
    success = all(r['difference'] > 0 for r in results)
    mean = float(np.mean([r['difference'] for r in results]))
    conclusion = f'H3-rollout ga {mean:+.1f} netto poeng mot samme forslag uten læring i sesongsnitt. Pilotkrav {"bestått" if success else "ikke bestått"}; benchmark beholdes.'
    atomic_json(HERE/'audit.json', {'status': 'pass', 'rounds_recomputed': verified,
        'branches_and_legal_transitions_verified': True, 'frozen_origin_inputs': True,
        'result': results, 'pilot_success': success, 'auditor_sha256': sha(__file__)})
    lines = ['# Resultater fra avgrenset rollout', '', conclusion, '',
        '| Sesong | Kontroll | Rollout | Forskjell | Historisk benchmark |', '|---|---:|---:|---:|---:|']
    lines += [f'| {r["season"]} | {r["control"]:.0f} | {r["candidate"]:.0f} | {r["difference"]:+.0f} | {r["benchmark"]:.0f} |' for r in results]
    lines += ['', 'Samme komplette forslagssystem og fryste prognoser. Bare to ulike ettertilstander vurderes med tre runders deterministisk videreføring. Eksisterende rabatt og chipreserve beholdes; ingen verdi etter horisonten læres. Dette tester én avgrenset variant, ikke rollout generelt.', '',
        'Kandidaten får ekstra løserarbeid til videreføring. Samme nodegrense per kall betyr ikke lik total beregning. Kontrollen gjenbrukes fra en etterkontrollert kjøring; tre nye utfallsblinde prøver gjenskapte forslagene eksakt. Alle 152 kontroll- og kandidatrunder er avregnet på nytt, og lagrede hypotetiske tilstandsoverganger og valg er kontrollert uten nye optimeringer.', '',
        'Begge år er tidligere studerte utviklingsdata. Historisk frist, priser og kjøpbarhet følger eksisterende proxyer. Ingen prognosetrening, usikkerhetsmodell, konkurrentmodell eller påstand om fremtidig overlegenhet inngår.', '',
        '[Protokoll](protocol.json) · [Etterkontroll](audit.json) · [Rundediagnostikk](rounds.csv) · [Testprogram](../../overview/TEST_PROGRAM.md)', '']
    (HERE/'RESULTATER.md').write_text('\n'.join(lines))
    evidence = [p for p in HERE.rglob('*') if p.is_file() and p.name not in ('result.json',) and p.suffix in ('.json', '.csv', '.md')]
    atomic_json(HERE/'result.json', {'conclusion': conclusion, 'decision': 'retain_for_research' if success else 'reject',
        'results': {'seasons': results, 'pilot_success': success, 'benchmark_promoted': False},
        'evidence_hashes': {str(p.relative_to(ROOT)): sha(p) for p in evidence}})
    print(conclusion, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'run', 'audit']); args = parser.parse_args()
    if args.command == 'run' and (HERE/'started.json').exists():
        parser.error('Already started; no duplicate or automatic retry')
    try:
        globals()[args.command]()
    except BaseException as exc:
        if args.command == 'run' and not (HERE/'failure.json').exists():
            atomic_json(HERE/'failure.json', {'at_utc': stamp(), 'error': str(exc), 'traceback': traceback.format_exc(), 'automatic_retry': False})
        raise


if __name__ == '__main__':
    main()
