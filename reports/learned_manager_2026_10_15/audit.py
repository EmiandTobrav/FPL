"""Recompute settlements, state chains and chronological/resource contracts."""
from pathlib import Path
import importlib.util
import json
import sys
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from model_lab.common import read, sha, verify_files, atomic_json, digest
spec = importlib.util.spec_from_file_location('_learned_experiment_audit_import', HERE / 'experiment.py')
e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)


def audit():
    protocol = read(HERE / 'protocol.json'); verify_files(ROOT, protocol['files'])
    amendment = read(HERE / 'mechanical_resume_v002.json')
    verify_files(ROOT, amendment['new_files'])
    verify_files(HERE, amendment['preserved_round_prefix'])
    if not (HERE / 'complete.json').exists(): raise ValueError('Experiment not completed')
    _, adapter = e.backend(); rules = adapter.engine
    helpers = e.settlement_helpers(); store = helpers.OutcomeStore(ROOT)
    checks = 0; records = []; parity = []; different_actions = []
    for season in e.SEASONS:
        saved = read(HERE / 'training' / f'{season}_models.json')
        samples = read(HERE / 'training' / f'{season}_samples.json')
        cutoff = pd.Timestamp(saved['cutoff'])
        expected_prior = [s for s in e.SEASONS if s < season]
        if any(r['season'] not in expected_prior or pd.Timestamp(r['label_available_at']) >= cutoff for r in samples):
            raise ValueError('Training chronology violation')
        rebuilt = e.build_training_samples(expected_prior, str(cutoff), rules) if expected_prior else []
        if digest(rebuilt) != digest(samples): raise ValueError('Training samples not reproducible from frozen teacher')
        if e.fit(samples, cutoff) != saved['models']: raise ValueError('Fitted coefficients do not reproduce')
        if saved['fit_cpu_seconds'] > 5.: raise ValueError('Training resource cap exceeded')
        season_actions = {}
        for candidate in [e.BENCHMARK, e.CANDIDATE]:
            out = HERE / 'runs' / f'{season}__{candidate}'; state = rules.initial_state()
            points = 0.; calls = 0; actions = []; learned = 0
            for gw in range(1, 39):
                lock = read(out / f'gw{gw:02d}.decision.json'); log = read(out / f'gw{gw:02d}.json')
                if lock['outcomes_read'] is not False or log['outcomes_read'] is not True: raise ValueError('Decision/outcome barrier failed')
                for key in lock:
                    if key != 'outcomes_read' and log[key] != lock[key]: raise ValueError('Locked decision was changed')
                if e.state_json(log['state_before']) != state: raise ValueError('Broken state chain')
                p, xp, manifest = e.inputs(season, gw)
                if digest(xp.tolist()) != log['forecast_array_sha256']: raise ValueError('Forecast mutation')
                choice = log['decision']; choice['prices'] = {int(k): v for k, v in choice['prices'].items()}
                after, validated = rules.apply_decision(state, choice, p.to_dict('records'), gw, log['chip'])
                if after != e.state_json(log['state_after']): raise ValueError('State transition mismatch')
                rebuilt_outcomes = helpers.enrich_outcomes(season, gw, store.for_round(season, gw, choice['squad']), p)
                expected_outcomes = helpers.clean(rebuilt_outcomes.astype(object).where(rebuilt_outcomes.notna(), None).to_dict('records'))
                if digest(expected_outcomes) != digest(log['outcomes']):
                    raise ValueError('Saved outcomes differ from frozen target/qualified blank reconstruction')
                outcome = {int(r['code']): r for r in log['outcomes']}
                if any(not outcome[i]['known'] for i in choice['squad']): raise ValueError('Unknown selected outcome')
                args = (choice['starters'], choice['bench'], choice['captain'], choice['vice'], dict(zip(p.pid, p.pos)),
                        {i: outcome[i]['points'] for i in choice['squad']}, {i: outcome[i]['appeared'] for i in choice['squad']})
                settled = rules.settle(*args, log['chip'])
                net = settled['gross'] - 4 * validated['paid']
                if net != log['net_points'] or 4 * validated['paid'] != log['hit_cost']: raise ValueError('Settlement mismatch')
                for c in log['solver_calls']:
                    if c['options'] != adapter.options or c['nodes'] > 16 or not c['full_mip_feasible']:
                        raise ValueError('Solver contract mismatch')
                if len(log['solver_calls']) > 40: raise ValueError('Solver-call cap exceeded')
                x = e.features(p, xp, state, gw)
                for value in log['learned_reserves']:
                    model = saved['models'].get(value['chip'])
                    expected = float(adapter.policy.reserve_value(value['chip'], gw)) if model is None else e.component.predict(model, x)
                    if abs(value['reserve'] - expected) > 1e-10 or value['learned'] != (model is not None):
                        raise ValueError('Learned policy inference mismatch')
                    if value['learned'] and value['features'] != x: raise ValueError('Wrong policy inputs')
                learned += any(t['learned'] for t in log['learned_reserves'])
                actions.append({k: log['decision'][k] for k in ['squad', 'starters', 'bench', 'captain', 'vice', 'chip']})
                if candidate == e.BENCHMARK:
                    prior = read(e.prior_path(season) / f'gw{gw:02d}.json')
                    parity.append(net == prior['net_points'] and all(prior['decision'][k] == actions[-1][k] for k in actions[-1]))
                state = after; points += net; calls += len(log['solver_calls']); checks += 1
            summary = read(out / 'summary.json')
            if summary['net_points'] != points or summary['solver_calls'] != calls or not summary['complete_season']:
                raise ValueError('Summary mismatch')
            records.append(summary); season_actions[candidate] = actions
        changes = sum(a != b for a, b in zip(season_actions[e.BENCHMARK], season_actions[e.CANDIDATE]))
        if season == '2022-23' and changes: raise ValueError('Cold control not identical')
        different_actions.append({'season': season, 'different_round_decisions': changes})
    if not all(parity): raise ValueError('Fresh benchmark did not reproduce frozen reference actions/results')
    result = {'status': 'pass', 'rounds_recomputed': checks, 'fresh_reference_rounds_matching_prior': len(parity),
        'training_chronology_and_coefficients_verified': True, 'forecasts_unchanged': True,
        'same_solver_options_and_caps': True, 'unknowns_not_zero': True,
        'selected_outcomes_rebuilt_from_frozen_targets_and_qualified_blanks': True,
        'decision_changes': different_actions, 'records': records,
        'auditor_sha256': sha(HERE / 'audit.py'), 'protocol_sha256': sha(HERE / 'protocol.json')}
    atomic_json(HERE / 'audit.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
