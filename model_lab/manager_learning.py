"""Bounded episodic manager-learning campaign using the frozen forecast archive.

Usage: python -m model_lab.manager_learning {preflight,freeze,run,audit,report} CONFIG
The configuration is frozen and registered before any new training/evaluation.
"""
import os
for _name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']:
    os.environ[_name] = '1'
import argparse
import copy
import importlib.util
from pathlib import Path
import time
import traceback
import numpy as np
import pandas as pd
from .common import ROOT, read, sha, digest, atomic_json, verify_files, runtime
from .simulation import backend, BENCHMARK
from . import manager_policy as policy

OLD = ROOT / 'reports/learned_manager_2026_10_15'
CANDIDATE = 'episodic_manager_v1'
CONTROL = 'same_proposals_unlearned_v1'
EVALUATIONS = ('2023-24', '2024-25')


def old():
    spec = importlib.util.spec_from_file_location('_manager_fixed_inputs', OLD / 'experiment.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class Environment:
    """Inputs and outcomes have separate methods; decisions are saved first."""
    def __init__(self):
        self.e = old(); self.helpers = self.e.settlement_helpers()
        self.store = self.helpers.OutcomeStore(ROOT)
        master = pd.read_csv(ROOT / 'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz', usecols=['season', 'kickoff_time'])
        self.labels = (pd.to_datetime(master.kickoff_time, utc=True) + pd.Timedelta(hours=24)).groupby(master.season).max()
        self.loaded = {}

    def inputs(self, season, gw):
        key = (season, gw)
        if key not in self.loaded:
            pool, xp, manifest = self.e.inputs(season, gw)
            path = self.e.CACHE / season / f'gw{gw:02d}' / 'features.csv.gz'
            if sha(path) != manifest['files']['features.csv.gz']: raise ValueError('Manager history input changed')
            frame = pd.read_csv(path, usecols=['code', 'forecast_at', *policy.HISTORY])
            if frame.code.duplicated().any() or not (pd.to_datetime(frame.forecast_at, utc=True) == pd.Timestamp(manifest['forecast_at'])).all():
                raise ValueError('Wrong manager history origin')
            frame = frame.set_index('code').reindex(pool.code)
            if frame.forecast_at.isna().any(): raise ValueError('Missing held-player history row')
            history = {}
            for pid, (_, row) in zip(pool.pid, frame.iterrows()):
                history[int(pid)] = {c: float(row[c]) if pd.notna(row[c]) and np.isfinite(float(row[c]))
                                     else (1. if c == 'f_history_missing' else 0.) for c in policy.HISTORY}
            self.loaded[key] = (pool, xp, manifest, history)
        p, xp, m, h = self.loaded[key]
        return p.copy(), xp.copy(), copy.deepcopy(m), copy.deepcopy(h)

    def outcomes(self, season, gw, choice, pool):
        rows = self.helpers.enrich_outcomes(season, gw, self.store.for_round(season, gw, choice['squad']), pool)
        return self.helpers.clean(rows.astype(object).where(rows.notna(), None).to_dict('records'))

    def teacher(self, season, source, cutoff):
        """Existing complete demonstrations, scored through GW38 as training."""
        logs = []; _, adapter = backend()
        for gw in range(1, 39):
            raw = read(OLD / 'runs' / f'{season}__{source}' / f'gw{gw:02d}.json')
            pool, xp, manifest, history = self.inputs(season, gw)
            before, after = self.e.state_json(raw['state_before']), self.e.state_json(raw['state_after'])
            choice = copy.deepcopy(raw['decision'])
            x = policy.encode(pool, xp, history, before, after, choice, adapter.engine, gw)
            reserve = 0. if raw['chip'] is None else adapter.policy.reserve_value(raw['chip'], gw)
            base = 100*x[9] + .9*100*x[14] + .81*100*x[15] - reserve
            logs.append({'gw': gw, 'net_points': raw['net_points'], 'forecast_at': manifest['forecast_at'],
                'episode': f'teacher__{season}__{source}',
                'selected': {'features': x, 'base_score': float(base), 'id': policy.identity(choice)}})
        return policy.episode_samples(logs, season, str(self.labels.loc[season]))


def validate_config(config):
    expected = {'id': 'season-manager-20261015-v1', 'candidate': CANDIDATE,
        'evaluation_seasons': list(EVALUATIONS), 'new_training_seasons': ['2022-23', '2023-24'],
        'episodes_per_training_season': 2, 'epsilons': [.30, .15], 'alpha': 50.,
        'seed': 20261015, 'node_limit': 16, 'max_calls_per_decision': 40,
        'max_new_full_seasons': 8, 'max_new_decisions': 304, 'max_fit_cpu_seconds': 5.}
    for key, value in expected.items():
        if config.get(key) != value: raise ValueError(f'Unexpected preregistered setting: {key}')
    return config


def preflight(config, here):
    validate_config(config)
    env = Environment(); results = []
    for gw in [1, 10, 20]:
        p, xp, manifest, history = env.inputs('2022-23', gw)
        raw = read(OLD / 'runs' / f'2022-23__{BENCHMARK}' / f'gw{gw:02d}.json')
        state = env.e.state_json(raw['state_before']); _, adapter = backend(16, 40)
        options = policy.proposals(adapter, p, xp, history, state, gw)
        for option in options:
            expected, _ = adapter.engine.apply_decision(state, option['choice'], p.to_dict('records'), gw)
            if expected != option['after']: raise ValueError('Proposal transition mismatch')
        chips = {r['choice']['chip'] for r in options}
        if not {None, *adapter.engine.available_chips(state, gw)} <= chips: raise ValueError('Missing legal chip family')
        results.append({'round': gw, 'proposals': len(options), 'solver_calls': len(adapter.ledger),
                        'chips': sorted(c for c in chips if c), 'outcomes_read': False})
    atomic_json(here / 'preflight.json', {'status': 'pass', 'checks': results, 'scope': 'Outcome-blind integration, no policy training or evaluation.'})
    return results


def freeze(config, config_path, here):
    validate_config(config)
    if read(here / 'preflight.json')['status'] != 'pass': raise ValueError('Preflight required')
    prior = read(OLD / 'audit.json')
    if prior['status'] != 'pass' or prior['rounds_recomputed'] != 228: raise ValueError('Prior comparisons not audited')
    files = dict(read(OLD / 'protocol.json')['files'])
    files.update(read(OLD / 'result.json')['evidence_hashes'])
    paths = [config_path, OLD / 'result.json', OLD / 'audit.py', here / 'preflight.json']
    paths += [p for p in (ROOT / 'model_lab').rglob('*.py') if '__pycache__' not in p.parts]
    e = old()
    for season in ('2022-23', '2023-24', '2024-25'):
        for gw in range(1, 39): paths.append(e.CACHE / season / f'gw{gw:02d}' / 'features.csv.gz')
    files.update({str(p.relative_to(ROOT)): sha(p) for p in paths})
    verify_files(ROOT, files)
    protocol = {'version': 1, 'experiment': config['id'], 'config': config,
        'separate_campaign_configurations': 1,
        'old_campaign_limit_unchanged': True,
        'authorization': 'User requests learning full round-by-round season management, all chips, and asks to continue.',
        'forecast': 'Unchanged frozen arrays and pre-deadline history; no forecast fits.',
        'intervention': 'Episodic return-to-go residual ranking of complete legal proposals; all four chips, transfers/roll, XI, bench order, captain and vice.',
        'proposal_limits': 'H3 plans for all available chips, H1 ordinary and retained squad; four deterministic lineup/captain/bench variants. This is a bounded action set, not all possible FPL actions.',
        'objective': 'Undiscounted full-season net points after transfer costs; no win-probability claim.',
        'training': 'Two epsilon-exploratory complete episodes per training season; season-frozen scaler/Ridge alpha50; fit on full-season Monte Carlo residual returns. Prior full trajectories reused rather than replayed.',
        'data_split': 'Train on 2022-23 before evaluating 2023-24. Then add 2023-24 training for evaluation 2024-25. No 2025-26 read. Development seasons previously studied.',
        'controls': [BENCHMARK, 'learned_chip_wait_v1', CONTROL],
        'reference_reuse': 'First two controls reuse the audited previous experiment byte for byte: identical cache, targets, openings and solver caps. Same-proposal control is a new full-season run.',
        'success_criterion': 'Positive net gain over all three controls in each of both evaluation seasons; no automatic promotion.',
        'resources': 'Same one-thread 16-node/40-call decision caps for new learned and unlearned controls. Common allocated training ceiling four full episodes/152 decisions and fits <=5 CPU seconds each; actual use reported. Training is additional work, not claimed free or identical actual CPU.',
        'stop': 'Stop on invalid/missing selected outcome, source/runtime change, unavailable training label, solver failure or resource breach. No automatic retry or tuning.',
        'limitations': 'Four new historical training episodes are correlated replays, not independent seasons. Fixed player forecasts; deterministic historical environment; full action selection within bounded proposals, not end-to-end unrestricted neural RL or an opponent simulator.',
        'runtime': runtime(), 'files': files}
    atomic_json(here / 'protocol.json', protocol)
    return protocol


def settle(adapter, env, season, gw, selected, pool):
    choice = selected['choice']; outcomes = env.outcomes(season, gw, choice, pool)
    indexed = {int(r['code']): r for r in outcomes}
    result = adapter.engine.settle(choice['starters'], choice['bench'], choice['captain'], choice['vice'],
        dict(zip(pool.pid, pool.pos)), {i: indexed[i]['points'] for i in choice['squad']},
        {i: indexed[i]['appeared'] for i in choice['squad']}, choice['chip'])
    if any(not indexed[i]['known'] for i in choice['squad']): raise ValueError('Unknown selected outcome')
    return outcomes, result, float(result['gross'] - 4*choice['paid'])


def episode(env, season, name, directory, config, model=None, epsilon=0., seed=None):
    """No evaluation label can be read until the whole proposal set is locked."""
    atomic_json(directory / 'started.json', {'season': season, 'episode': name, 'model_sha256': digest(model), 'epsilon': epsilon, 'seed': seed})
    _, initial = backend(); state = initial.engine.initial_state(); logs = []
    rng = np.random.default_rng(seed) if seed is not None else None
    started_wall = time.monotonic(); started_cpu = time.process_time()
    for gw in range(1, 39):
        pool, xp, manifest, history = env.inputs(season, gw); _, adapter = backend(16, 40)
        options = policy.proposals(adapter, pool, xp, history, state, gw, bool(manifest.get('official_all_blank_forced_wait')))
        index, scores, exploratory = policy.select(options, model, rng, epsilon)
        selected = options[index]
        lock = {'season': season, 'gw': gw, 'episode': name, 'forecast_at': manifest['forecast_at'],
            'forecast_array_sha256': digest(xp.tolist()), 'state_before': state,
            'options': options, 'selected_index': index, 'selected': selected,
            'scores': scores, 'exploratory': exploratory, 'solver_calls': adapter.ledger,
            'model_sha256': digest(model), 'outcomes_read': False}
        clean = env.helpers.clean(lock)
        atomic_json(directory / f'gw{gw:02d}.decision.json', clean)
        outcomes, result, net = settle(adapter, env, season, gw, selected, pool)
        row = {**clean, 'outcomes_read': True, 'outcomes': outcomes, 'settlement': result,
               'net_points': net, 'hit_cost': 4*selected['choice']['paid']}
        atomic_json(directory / f'gw{gw:02d}.json', row)
        logs.append(row); state = selected['after']
        print(f'{name} GW{gw:02d} settled', flush=True)
    summary = {'season': season, 'episode': name, 'complete_season': True, 'net_points': sum(r['net_points'] for r in logs),
        'hit_cost': sum(r['hit_cost'] for r in logs), 'solver_calls': sum(len(r['solver_calls']) for r in logs),
        'solver_seconds': sum(c['seconds'] for r in logs for c in r['solver_calls']),
        'seconds': time.monotonic()-started_wall, 'process_cpu_seconds': time.process_time()-started_cpu,
        'exploratory_rounds': sum(r['exploratory'] for r in logs),
        'chip_usage': {c: [r['gw'] for r in logs if r['selected']['choice']['chip'] == c] for c in policy.CHIPS},
        'proposed_chip_rounds': {c: sum(any(o['choice']['chip'] == c for o in r['options']) for r in logs) for c in policy.CHIPS}}
    atomic_json(directory / 'summary.json', summary)
    return logs


def run(config, here):
    protocol = read(here / 'protocol.json'); verify_files(ROOT, protocol['files'])
    if protocol['config'] != config or protocol['runtime'] != runtime(): raise ValueError('Configuration/runtime changed')
    from scripts.research import fingerprint
    registration = read(here / 'registration.json'); proposal = read(ROOT / registration['proposal'])
    if fingerprint(proposal) != registration['fingerprint'] or proposal['input_hashes'].get(str((here/'protocol.json').relative_to(ROOT))) != sha(here/'protocol.json'):
        raise ValueError('Registered contract mismatch')
    atomic_json(here / 'started.json', {'protocol_sha256': sha(here/'protocol.json'), 'automatic_retry': False})
    env = Environment(); samples = []; newly_run = []; fits = []
    for stage, (train_season, evaluation) in enumerate(zip(config['new_training_seasons'], EVALUATIONS)):
        cutoff = env.inputs(evaluation, 1)[2]['forecast_at']
        samples += env.teacher(train_season, BENCHMARK, cutoff)
        # The 2022 cold policy exactly duplicates the teacher; do not count it
        # twice. The 2023 learned chip trajectory is distinct and available only
        # when training for 2024 evaluation.
        if train_season == '2023-24': samples += env.teacher(train_season, 'learned_chip_wait_v1', cutoff)
        for fit_number in range(3):
            t = time.process_time(); model = policy.fit(samples, cutoff, config['alpha']); seconds = time.process_time()-t
            if seconds > config['max_fit_cpu_seconds']: raise ValueError('Fit resource budget exceeded')
            fit_name = f'{evaluation}__fit{fit_number}'
            atomic_json(here / 'training' / f'{fit_name}.json', {'model': model, 'samples': samples, 'fit_cpu_seconds': seconds})
            fits.append({'name': fit_name, 'cpu_seconds': seconds, 'rows': len(samples)})
            if fit_number == 2: break
            name = f'train__{train_season}__episode{fit_number+1}'
            logs = episode(env, train_season, name, here/'episodes'/name, config, model,
                           config['epsilons'][fit_number], config['seed']+100*stage+fit_number)
            samples += policy.episode_samples(logs, train_season, str(env.labels.loc[train_season]))
            newly_run.append(name)
        atomic_json(here / 'models' / f'{evaluation}.json', model)
        for candidate in [CONTROL, CANDIDATE]:
            name = f'eval__{evaluation}__{candidate}'
            episode(env, evaluation, name, here/'episodes'/name, config, None if candidate == CONTROL else model)
            newly_run.append(name)
    if len(newly_run) != 8: raise ValueError('Unexpected episode count')
    verify_files(ROOT, protocol['files'])
    atomic_json(here / 'complete.json', {'protocol_sha256': sha(here/'protocol.json'), 'full_seasons': len(newly_run),
        'new_training_seasons': 4, 'new_evaluation_seasons': 4, 'decisions': 304, 'fits': fits, 'benchmark_promoted': False})


def audit(config, here):
    protocol = read(here/'protocol.json'); verify_files(ROOT, protocol['files'])
    complete = read(here/'complete.json')
    if complete['protocol_sha256'] != sha(here/'protocol.json') or complete['decisions'] != 304:
        raise ValueError('Completion differs from frozen contract')
    env = Environment(); _, adapter = backend(); rules = adapter.engine
    verified = []; summaries = []; samples = []; fits = []

    def check_episode(season, name, model, epsilon=0., seed=None):
        directory = here/'episodes'/name; state = rules.initial_state(); logs = []
        rng = np.random.default_rng(seed) if seed is not None else None
        for gw in range(1, 39):
            lock = read(directory/f'gw{gw:02d}.decision.json'); row = read(directory/f'gw{gw:02d}.json')
            if lock['outcomes_read'] is not False or row['outcomes_read'] is not True: raise ValueError('Outcome barrier failed')
            if any(row[k] != v for k, v in lock.items() if k != 'outcomes_read'): raise ValueError('Changed locked action')
            if env.e.state_json(lock['state_before']) != state or lock['model_sha256'] != digest(model): raise ValueError('State/model chain failed')
            pool, xp, manifest, history = env.inputs(season, gw)
            if lock['forecast_array_sha256'] != digest(xp.tolist()) or lock['forecast_at'] != manifest['forecast_at']:
                raise ValueError('Forecast changed')
            options = lock['options']; ids = set(); chips = set()
            if not 1 <= len(options) <= 36: raise ValueError('Proposal budget exceeded')
            for option in options:
                choice = copy.deepcopy(option['choice']); choice['prices'] = {int(k): v for k, v in choice['prices'].items()}
                after, choice = rules.apply_decision(state, choice, pool.to_dict('records'), gw)
                if after != env.e.state_json(option['after']): raise ValueError('Invalid proposal transition')
                x = policy.encode(pool, xp, history, state, after, choice, rules, gw)
                if x != option['features'] or option['id'] != policy.identity(choice): raise ValueError('Proposal feature/action identity changed')
                reserve = 0. if choice['chip'] is None else adapter.policy.reserve_value(choice['chip'], gw)
                expected = 0. if manifest.get('official_all_blank_forced_wait') else 100*x[9]+.9*100*x[14]+.81*100*x[15]-reserve
                if abs(expected-option['base_score']) > 1e-10: raise ValueError('Short-horizon prior changed')
                if option['id'] in ids: raise ValueError('Duplicate legal proposal')
                ids.add(option['id']); chips.add(choice['chip'])
            if not manifest.get('official_all_blank_forced_wait') and not {None, *rules.available_chips(state, gw)} <= chips:
                raise ValueError('An available chip family was omitted')
            index, scores, exploratory = policy.select(options, model, rng, epsilon)
            if index != lock['selected_index'] or options[index] != lock['selected'] or scores != lock['scores'] or exploratory != lock['exploratory']:
                raise ValueError('Policy selection does not reproduce')
            selected = options[index]
            outcomes, settlement, net = settle(adapter, env, season, gw, selected, pool)
            if outcomes != row['outcomes'] or env.helpers.clean(settlement) != row['settlement'] or net != row['net_points']:
                raise ValueError('Target/settlement does not reproduce')
            for call in row['solver_calls']:
                if call['options'] != adapter.options or call['nodes'] > 16 or not call['full_mip_feasible']:
                    raise ValueError('Solver resource/feasibility violation')
            if len(row['solver_calls']) > 40: raise ValueError('Decision solver-call budget exceeded')
            state = env.e.state_json(selected['after']); logs.append(row)
        summary = read(directory/'summary.json')
        if sum(r['net_points'] for r in logs) != summary['net_points'] or sum(len(r['solver_calls']) for r in logs) != summary['solver_calls']:
            raise ValueError('Episode summary failed')
        verified.append(name); summaries.append(summary)
        return logs

    for stage, (train_season, evaluation) in enumerate(zip(config['new_training_seasons'], EVALUATIONS)):
        cutoff = env.inputs(evaluation, 1)[2]['forecast_at']
        samples += env.teacher(train_season, BENCHMARK, cutoff)
        if train_season == '2023-24': samples += env.teacher(train_season, 'learned_chip_wait_v1', cutoff)
        for fit_number in range(3):
            name = f'{evaluation}__fit{fit_number}'; saved = read(here/'training'/f'{name}.json')
            model = policy.fit(samples, cutoff, config['alpha'])
            if saved['samples'] != samples or saved['model'] != model or saved['fit_cpu_seconds'] > 5.:
                raise ValueError('Training/fit chronology or coefficients do not reproduce')
            fits.append(name)
            if fit_number == 2: break
            episode_name = f'train__{train_season}__episode{fit_number+1}'
            logs = check_episode(train_season, episode_name, model, config['epsilons'][fit_number], config['seed']+100*stage+fit_number)
            samples += policy.episode_samples(logs, train_season, str(env.labels.loc[train_season]))
        if read(here/'models'/f'{evaluation}.json') != model: raise ValueError('Frozen evaluation model changed')
        for candidate in (CONTROL, CANDIDATE):
            check_episode(evaluation, f'eval__{evaluation}__{candidate}', None if candidate == CONTROL else model)
    if len(verified) != 8 or len(fits) != 6: raise ValueError('Incomplete experiment')
    result = {'status': 'pass', 'rounds_recomputed': 304, 'complete_episodes': 8,
        'training_episodes': 4, 'evaluation_episodes': 4, 'fits_reproduced': 6,
        'all_available_chip_families_proposed': True, 'all_proposals_legal_and_features_recomputed': True,
        'full_season_return_targets_reproduced': True, 'chronology_and_frozen_evaluation_models': True,
        'same_frozen_forecasts_and_resource_caps': True, 'outcomes_rebuilt_from_frozen_targets': True,
        'summaries': summaries, 'auditor_sha256': sha(Path(__file__)), 'protocol_sha256': sha(here/'protocol.json')}
    atomic_json(here/'audit.json', result)
    return {k: v for k, v in result.items() if k != 'summaries'}


def report(config, here):
    import csv
    audit = read(here/'audit.json')
    if audit['status'] != 'pass' or audit['rounds_recomputed'] != 304: raise ValueError('Require completed audit')
    records = {r['episode']: r for r in audit['summaries']}
    results = []; resource = []; chips = []; rounds = []
    for season in EVALUATIONS:
        values = {}
        for name in [BENCHMARK, 'learned_chip_wait_v1']:
            saved = read(OLD/'runs'/f'{season}__{name}'/'summary.json'); values[name] = saved['net_points']
        for name in [CONTROL, CANDIDATE]:
            saved = records[f'eval__{season}__{name}']; values[name] = saved['net_points']
        results.append({'season': season, **values, 'gain_vs_benchmark': values[CANDIDATE]-values[BENCHMARK],
            'gain_vs_chip_policy': values[CANDIDATE]-values['learned_chip_wait_v1'],
            'gain_vs_same_proposals': values[CANDIDATE]-values[CONTROL]})
    success = all(r[k] > 0 for r in results for k in ['gain_vs_benchmark', 'gain_vs_chip_policy', 'gain_vs_same_proposals'])
    mean = lambda k: sum(r[k] for r in results)/len(results)
    conclusion = f"Episodisk manager ga {mean('gain_vs_benchmark'):+.1f} netto poeng mot benchmark, {mean('gain_vs_chip_policy'):+.1f} mot chip-policyen og {mean('gain_vs_same_proposals'):+.1f} mot samme forslag uten læring i sesongsnitt. "
    conclusion += 'Pilotkravet bestått; benchmark beholdt inntil separat vurdering.' if success else 'Pilotkravet ikke bestått; dagens benchmark beholdes.'
    for name, summary in records.items():
        resource.append({k: summary[k] for k in ['episode', 'season', 'net_points', 'hit_cost', 'solver_calls', 'solver_seconds', 'seconds', 'process_cpu_seconds', 'exploratory_rounds']})
        for chip in policy.CHIPS:
            chips.append({'episode': name, 'chip': chip, 'used_rounds': ','.join(map(str, summary['chip_usage'][chip])),
                          'proposed_rounds': summary['proposed_chip_rounds'][chip]})
        if name.startswith('eval__'):
            for gw in range(1, 39):
                row = read(here/'episodes'/name/f'gw{gw:02d}.json'); c = row['selected']['choice']
                rounds.append({'episode': name, 'round': gw, 'net_points': row['net_points'], 'chip': c['chip'],
                    'transfers': c['transfers'], 'hit_cost': row['hit_cost'], 'captain': c['captain'],
                    'proposal_family': row['selected']['family'], 'legal_proposals': len(row['options'])})
    def table(filename, rows):
        with (here/filename).open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    table('results.csv', results); table('resources.csv', resource); table('chips.csv', chips); table('rounds.csv', rounds)
    lines = ['# Lært manager gjennom hele sesongen', '', conclusion, '',
        'Policyen velger en komplett handling runde for runde. Bytter, å spare gratisbytter, tropp, startellever, '
        'benkerekkefølge, kaptein/visekaptein og Wildcard, Free Hit, Bench Boost og Triple Captain inngår i valgene. '
        'Valgene er avgrenset til lovlige forslag fra den eksisterende planleggeren og faste alternativer. '
        'Dette dekker beslutningstypene, ikke alle mulige kombinasjoner av spillere og handlinger.', '',
        '| Sesong | Benchmark | Første lærte chip-policy | Samme forslag uten læring | Episodisk lært manager |',
        '|---|---:|---:|---:|---:|']
    for r in results:
        lines.append(f"| {r['season']} | {r[BENCHMARK]:.0f} | {r['learned_chip_wait_v1']:.0f} | {r[CONTROL]:.0f} | {r[CANDIDATE]:.0f} |")
    lines += ['', '| Sesong | Mot benchmark | Mot chip-policy | Læringens tillegg mot samme forslag |', '|---|---:|---:|---:|']
    for r in results:
        lines.append(f"| {r['season']} | {r['gain_vs_benchmark']:+.0f} | {r['gain_vs_chip_policy']:+.0f} | {r['gain_vs_same_proposals']:+.0f} |")
    lines += ['', 'Alle poeng er etter overgangskostnader. Siste kolonne isolerer effekten av den lærte rangeringen '
        'innenfor de samme forslagsreglene. Selve forslagene kan avvike når managernes egne lag har utviklet seg forskjellig.', '',
        '## Slik foregår læringen', '',
        'En enkel verdi-/handlingsmodell lærer fra hele historiske sesongforløp. Hver treningsrad får faktisk '
        'poengsum fra den valgte runden til og med GW38 som mål, fratrukket en felles kortsiktig forventningsverdi. '
        'Dermed kan et valg belønnes eller straffes gjennom senere følger for tropp, bank, gratisbytter og chips. '
        'Den lærte justeringen legges til den samme kortsiktige verdien ved valg av handling.', '',
        'Modellen er StandardScaler og Ridge med alpha 50. Den får 40 før-frist-felt om handlingen, laget, '
        'bank, bytter, chipbeholdning, gjenværende tid, uendrede poengprognoser og noen eksisterende historikkfelt '
        'for spilletid. Ingen spiller-ID brukes som feature. Ingen prognosemodell trenes på nytt.', '',
        'For 2023/24 brukes eksisterende 2022/23-forløp og to nye treningsforløp gjennom 2022/23. '
        'For 2024/25 gjenbrukes disse og suppleres med to eksisterende 2023/24-forløp og to nye treningsforløp gjennom 2023/24. '
        'De nye treningsforløpene prøver alternative lovlige handlinger med fast utforskingsandel 30 og 15 prosent. '
        'Modellen oppdateres etter et helt forløp og fryses før hvert evalueringsår. '
        'Alle treningsmål må være tilgjengelige før første frist i evalueringsåret.', '',
        'Dette er avgrenset episodisk Monte Carlo-læring fra historisk simulator, med en enkel modell for rangering. '
        'Gjentatte forløp gjennom samme fotballsesong er korrelerte og gir ikke nye uavhengige sesonger. '
        'Modellen optimaliserer netto poeng; et konkurrentfelt og vinnsannsynlighet er ikke modellert.', '',
        '## Sammenligning og ressurser', '',
        'Prognoser, poengmål, før-frist-data, startregler og regelmotor er felles. Benchmark og første chip-policy '
        'gjenbrukes fra det foregående fullførte og kontrollerte forsøket med nøyaktig samme input og grenser; '
        'deres løserarbeid gjentas ikke. Kontrollen uten læring og den episodiske policyen kjøres på nytt for begge år. '
        'Begge nye policyer har samme forslagssystem, én tråd og grenser på 16 noder per kall og 40 kall per beslutning.', '',
        'Læring krever ekstra arbeid: fire nye komplette treningsforløp, 152 treningsbeslutninger og seks små modelltilpasninger. '
        'I tillegg er det fire evalueringsforløp med 152 beslutninger. Samlet er 304 nye runder kjørt. '
        'Tildelt treningsramme er felles, men faktisk arbeid er ikke identisk med en kontroll som ikke trener. '
        'Tilpasningstiden måler modelltilpasning; forarbeid/uttrekk av lærerdata har ikke separat CPU-måling. '
        'Detaljer per forløp finnes i [ressurstabellen](resources.csv).', '',
        '## Kontroller og konklusjon', '',
        'Etterkontrollen beregner alle 304 oppgjør på nytt fra fryste utfall, validerer samtlige lagrede forslag '
        'og tilstandsoverganger, kontrollerer alle tilgjengelige chipfamilier, gjenskaper utvalg og utforsking, '
        'sesonglange treningsmål, seks modelltilpasninger, frister, prognosehash og løsergrenser. '
        'Avgjørelser og hele forslagssettet er lagret før rundens utfall leses. Ukjente valgte utfall blir ikke nuller. '
        'Kontrollen bruker den eksisterende regelmotoren; den er ikke en ekstern kvalifisering av FPL-regler eller dataproxyer.', '',
        ('Kandidaten sendes til videre vurdering, uten automatisk oppgradering av benchmark.' if success else
         'Denne kandidatversjonen oppfyller ikke oppgraderingskravet. Behold det dokumenterte utfallet og unngå å gjenta '
         'samme variant eller bruke evalueringsresultatene til ubundet parameterjakt.'), '',
        'Begge evalueringsår er tidligere studerte utviklingsdata. To år og et lite antall fotballsesonger gir '
        'begrenset bevis for generalisering. 2025/26 er ikke brukt. Best-effort-poengmål, estimater og historiske '
        'tilgjengelighetsproxyer følger det uendrede datasettet.', '',
        '- [Fryst protokoll](protocol.json), [konfigurasjon](config.json), [registrering](registration.json), [etterkontroll](audit.json).',
        '- [Resultater](results.csv), [rundebeslutninger](rounds.csv), [alle chips](chips.csv), [ressurser](resources.csv).',
        '- `models/` og `training/`: fryste evalueringsmodeller, treningsrader og tilpasninger. `episodes/`: alle låste forslag og oppgjør.', '']
    (here/'RESULTATER.md').write_text('\n'.join(lines))
    evidence = [here/n for n in ['audit.json', 'complete.json', 'protocol.json', 'config.json', 'RESULTATER.md', 'results.csv', 'resources.csv', 'chips.csv', 'rounds.csv']]
    for folder in ['models', 'training', 'episodes']: evidence += sorted((here/folder).rglob('*.json'))
    result = {'conclusion': conclusion, 'decision': 'promote_to_review' if success else 'reject',
        'results': {'seasons': results, 'pilot_success': success, 'mean_gain_vs_benchmark': mean('gain_vs_benchmark'),
            'mean_gain_vs_chip_policy': mean('gain_vs_chip_policy'), 'mean_gain_vs_same_proposals': mean('gain_vs_same_proposals'),
            'benchmark_promoted': False, 'forecast_fits': 0},
        'evidence_hashes': {str(p.relative_to(ROOT)): sha(p) for p in evidence}}
    atomic_json(here/'result.json', result)
    return {'conclusion': conclusion, 'decision': result['decision']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['preflight', 'freeze', 'run', 'audit', 'report'])
    parser.add_argument('config', type=Path); args = parser.parse_args()
    path = args.config.resolve(); here = path.parent; config = validate_config(read(path))
    if args.command == 'run' and (here/'started.json').exists():
        parser.error('This experiment already started. Inspect saved status; no duplicate execution or automatic retry.')
    try:
        result = freeze(config, path, here) if args.command == 'freeze' else globals()[args.command](config, here)
        if args.command != 'run': print(str(result)[:2000])
    except BaseException as exc:
        if args.command == 'run' and not (here/'failure.json').exists():
            atomic_json(here/'failure.json', {'type': type(exc).__name__, 'error': str(exc), 'traceback': traceback.format_exc(), 'automatic_retry': False})
        raise


if __name__ == '__main__':
    main()
