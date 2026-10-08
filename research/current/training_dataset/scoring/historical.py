"""Deterministic historical inventory, basic-point audit and gated candidates.

The calculation is deliberately separate from qualification. No candidate is
exported as a training target while the required global gates remain open.
"""
from pathlib import Path
import ast
import hashlib
import json
import lzma

import pandas as pd

try:
    from .core import (basic_component_account, bonus_for_complete_fixture,
                       bps_candidate, total_candidate)
except ImportError:
    from core import (basic_component_account, bonus_for_complete_fixture,
                      bps_candidate, total_candidate)

P = Path(__file__).resolve().parent
R = P.parents[1]
S = R / 'scoring_2026_27'
K = ['season', 'fixture', 'code']
SEASONS = [f'{year}-{str(year+1)[2:]}' for year in range(2019, 2026)]
BASIC_FIELDS = ['minutes', 'goals_scored', 'assists', 'own_goals', 'clean_sheets',
                'goals_conceded', 'saves', 'penalties_saved', 'penalties_missed',
                'yellow_cards', 'red_cards', 'bps', 'bonus', 'total_points']
OUTPUTS = ['historical_inventory.csv.xz', 'player_match_candidates.csv.xz',
           'bps_component_changes.csv.xz', 'fixture_status.csv',
           'original_point_residuals.csv', 'source_population_gaps.csv',
           'fixture_source_disagreements.csv', 'duplicate_resolution.csv',
           'historical_bonus_residuals.csv', 'statistic_coverage.csv',
           'summary.json', 'manifest.json']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_read(path, hashes):
    hashes[str(path.relative_to(R))] = digest(path)
    return pd.read_csv(path, low_memory=False)


def resolve_duplicates(gw, fixtures, season):
    """Resolve only a unique observation at the official event and kickoff."""
    gw = gw.drop_duplicates().copy()
    duplicates = gw.duplicated(['element', 'fixture'], keep=False)
    keep = ~duplicates
    logs = []
    for (element, fixture), group in gw[duplicates].groupby(['element', 'fixture'], sort=True):
        official = fixtures.loc[fixture]
        match = group.GW.eq(official.event) & pd.to_datetime(group.kickoff_time, utc=True).eq(pd.to_datetime(official.kickoff_time, utc=True))
        if match.sum() != 1:
            raise ValueError(f'Ambiguous FPL snapshot: {season}/{fixture}/{element}')
        keep.loc[group.index] = match
        logs.append(dict(season=season, fixture=fixture, element=element,
                         discarded=int((~match).sum()), method='official_event_and_kickoff'))
    return gw[keep].copy(), logs


def load_inventory(hashes):
    frames, duplicate_logs, fixture_disagreements = [], [], []
    fixture_sources = {}
    for season in SEASONS:
        folder = R / 'project/data'
        gw = checked_read(folder / f'{season}_gw.csv.gz', hashes)
        players = checked_read(folder / f'{season}_players.csv.gz', hashes)
        fixtures = checked_read(folder / f'{season}_fixtures.csv.gz', hashes).set_index('id')
        teams = checked_read(folder / f'{season}_teams.csv.gz', hashes).set_index('id')
        gw, logs = resolve_duplicates(gw, fixtures, season)
        duplicate_logs.extend(logs)
        register = players[['id', 'code', 'element_type']].rename(columns={'element_type': 'register_type'})
        gw = gw.merge(register, how='left', left_on='element', right_on='id', validate='many_to_one')
        if gw.code.isna().any():
            raise ValueError('Missing historical player identity')
        # Assistant-manager observations are not player training observations.
        gw = gw[gw.register_type.isin([1, 2, 3, 4])].copy()
        mapped = gw.register_type.map({1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'})
        if 'position' in gw and not gw.position.replace({'GKP': 'GK'}).eq(mapped).all():
            raise ValueError('Historical position/register mismatch')
        gw['position'] = mapped
        gw['season'] = season
        ref = fixtures.reindex(gw.fixture)
        if ref.team_h.isna().any() or not ref.finished.all():
            raise ValueError('Missing or unfinished historical fixture')
        home = gw.was_home.to_numpy()
        gw['historical_team_id'] = ref.team_h.to_numpy()
        gw.loc[~home, 'historical_team_id'] = ref.team_a.to_numpy()[~home]
        gw['historical_team'] = gw.historical_team_id.map(teams.name)
        opponent = ref.team_a.to_numpy().copy()
        opponent[~home] = ref.team_h.to_numpy()[~home]
        if not gw.opponent_team.eq(opponent).all():
            raise ValueError('Historical fixture side/opponent mismatch')
        # Administrative GW numbering is retained beside the fixture event.
        gw['fixture_event'] = ref.event.to_numpy()
        gw['fixture_kickoff_time'] = ref.kickoff_time.to_numpy()
        same_time = pd.to_datetime(gw.kickoff_time, utc=True).to_numpy() == pd.to_datetime(ref.kickoff_time, utc=True).to_numpy()
        gw['kickoff_sources_agree'] = same_time
        for mismatch in gw.loc[~same_time, ['fixture', 'kickoff_time', 'fixture_kickoff_time']].drop_duplicates().itertuples():
            fixture_disagreements.append(dict(season=season, fixture=mismatch.fixture,
                element=None, field='kickoff_time', history_value=mismatch.kickoff_time,
                fixture_value=mismatch.fixture_kickoff_time, reason='official_source_timing_disagreement'))
        gw['source_file'] = f'project/data/{season}_gw.csv.gz'
        gw['source_key'] = gw.element.astype(str) + ':' + gw.fixture.astype(str)
        # Keep current-style statistics even where an earlier season lacks them.
        for field in ['expected_goals', 'expected_assists', 'expected_goal_involvements',
                      'expected_goals_conceded', 'starts', 'clearances_blocks_interceptions',
                      'tackles', 'recoveries', 'defensive_contribution']:
            if field not in gw:
                gw[field] = float('nan')
        gw['before_deadline_metadata_qualified'] = False
        event_signal = gw[BASIC_FIELDS].drop(columns=['minutes']).ne(0).any(axis=1)
        gw['scoring_relevant_inventory'] = gw.minutes.gt(0) | event_signal
        by_element = gw.set_index(['fixture', 'element'])
        for fixture, row in fixtures.sort_index().iterrows():
            fixture_sources[(season, int(fixture))] = row
            for entry in ast.literal_eval(row.stats):
                field = entry['identifier']
                if field not in BASIC_FIELDS:
                    continue
                for side in ('h', 'a'):
                    for observation in entry[side]:
                        key = (fixture, observation['element'])
                        if key not in by_element.index:
                            fixture_disagreements.append(dict(season=season, fixture=fixture,
                                element=observation['element'], field=field, history_value=None,
                                fixture_value=observation['value'], reason='fixture_observation_missing_from_gw'))
                        elif by_element.loc[key, field] != observation['value']:
                            fixture_disagreements.append(dict(season=season, fixture=fixture,
                                element=observation['element'], field=field,
                                history_value=by_element.loc[key, field], fixture_value=observation['value'],
                                reason='official_source_revision_disagreement'))
        gw = gw.drop(columns=['id', 'register_type'])
        frames.append(gw)
    inventory = pd.concat(frames, ignore_index=True).sort_values(K).reset_index(drop=True)
    if inventory.duplicated(K).any():
        raise ValueError('Duplicate canonical historical identity')
    return inventory, duplicate_logs, fixture_disagreements, fixture_sources


def load_defcon(hashes):
    root = R / 'rescoring_2025/harmonized/dataset'
    sha_path = root / 'sha256.json'
    hashes[str(sha_path.relative_to(R))] = digest(sha_path)
    expected = json.loads(sha_path.read_text())
    frames = []
    for name, sha in sorted(expected.items()):
        if not name.startswith('labels/'):
            continue
        path = root / name
        if digest(path) != sha:
            raise ValueError(f'Frozen defensive-award partition changed: {name}')
        frame = checked_read(path, hashes)
        frame['season'] = path.parent.name
        frames.append(frame[K + ['position', 'minutes', 'total_points', 'defcon_award', 'quality']])
    labels = pd.concat(frames, ignore_index=True)
    if labels.duplicated(K).any():
        raise ValueError('Duplicate frozen defensive award')
    return labels


def save(frame, path):
    raw = frame.to_csv(index=False, lineterminator='\n').encode()
    path.write_bytes(lzma.compress(raw) if path.suffix == '.xz' else raw)


def build(output=None):
    output = Path(output) if output else P / 'results'
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    current_path = S / 'bulk_reconciliation/CURRENT.json'
    current = json.loads(current_path.read_text())
    hashes[str(current_path.relative_to(R))] = digest(current_path)
    req_path = current_path.parent / current['requirements']
    if digest(req_path) != current['requirements_sha256']:
        raise ValueError('Current requirement fingerprint differs')
    req = checked_read(req_path, hashes)
    baseline = checked_read(S / 'fpl_authority/fpl_baseline.csv.gz', hashes)
    if baseline.duplicated(K).any() or req.duplicated(K + ['field']).any():
        raise ValueError('Duplicate baseline/requirement identity')
    if int(req.is_open.sum()) != current['open_fields']:
        raise ValueError('Current open requirement count differs')
    inventory, duplicates, source_disagreements, fixture_sources = load_inventory(hashes)
    labels = load_defcon(hashes)
    inv_keys = pd.MultiIndex.from_frame(inventory[K])
    if not pd.MultiIndex.from_frame(baseline[K]).isin(inv_keys).all():
        raise ValueError('Requirement population missing from full FPL source')
    comparison = baseline.merge(inventory[K + BASIC_FIELDS + ['position']], on=K,
                                validate='one_to_one', suffixes=('', '_source'))
    for field in BASIC_FIELDS + ['position']:
        if not comparison[field].eq(comparison[field + '_source']).all():
            raise ValueError(f'Canonical baseline differs from source: {field}')
    inventory = inventory.merge(labels, on=K, how='left', validate='one_to_one',
                                suffixes=('', '_defcon'))
    for field in ['minutes', 'position', 'total_points']:
        if not inventory[field].eq(inventory[field + '_defcon']).all():
            raise ValueError(f'Frozen defensive award identity differs: {field}')
    if inventory.defcon_award.isna().any() or not inventory.defcon_award.isin([0, 2]).all():
        raise ValueError('Missing/unqualified defensive award')
    inventory['defcon_points'] = inventory.defcon_award.astype(int)
    inventory['original_basic_component_points'] = [sum(basic_component_account(row, row['defcon_points']).values())
                                                   for row in inventory.to_dict('records')]
    inventory['original_point_residual'] = inventory.total_points - inventory.bonus - inventory.original_basic_component_points
    residuals = inventory[inventory.original_point_residual.ne(0)][K + ['name', 'minutes', 'total_points', 'bonus', 'original_basic_component_points', 'original_point_residual']]
    relevant = inventory[inventory.scoring_relevant_inventory]
    old_bonus_residuals = []
    for fixture_key, group in relevant.groupby(['season', 'fixture'], sort=True):
        scores = dict(zip(group.code, group.bps))
        bonus = bonus_for_complete_fixture(scores, group.code)
        for row in group.itertuples():
            if bonus[row.code] != row.bonus:
                old_bonus_residuals.append(dict(season=row.season, fixture=row.fixture,
                    code=row.code, original_bonus=row.bonus, recomputed_bonus=bonus[row.code],
                    original_bps=row.bps))
    source_gaps = relevant[~pd.MultiIndex.from_frame(relevant[K]).isin(pd.MultiIndex.from_frame(baseline[K]))]
    # Open ledger values stay missing, even if the raw exception contains zero.
    usable = req.copy()
    usable.loc[usable.is_open, 'value'] = float('nan')
    values = usable.pivot(index=K, columns='field', values='value')
    open_counts = req.groupby(K, sort=False).is_open.sum()
    candidates = baseline.set_index(K).join(values.add_prefix('input_')).join(open_counts.rename('open_fields'))
    candidates = candidates.join(inventory.set_index(K)[['defcon_points', 'original_point_residual', 'element', 'fixture_event', 'historical_team_id']])
    revisions = checked_read(S / 'official_revision/counter_supplement.csv', hashes)
    blocked_revision = set(map(tuple, revisions[['season', 'fixture']].drop_duplicates().to_numpy()))
    qualification_path = P / 'qualification.json'
    qualification = json.loads(qualification_path.read_text())
    hashes[str(qualification_path.relative_to(R))] = digest(qualification_path)
    if qualification['training_labels_enabled']:
        raise ValueError('This candidate builder cannot approve training labels')
    terms_rows = []
    for mode in ['clipped', 'signed']:
        candidates[f'bps_candidate_{mode}'] = float('nan')
        candidates[f'bonus_candidate_{mode}'] = float('nan')
        candidates[f'total_points_candidate_{mode}'] = float('nan')
    candidates['revision_bundle_blocked'] = [key[:2] in blocked_revision for key in candidates.index]
    candidates['calculation_input_ready'] = candidates.open_fields.eq(0) & ~candidates.revision_bundle_blocked & candidates.original_point_residual.eq(0)
    values_by_key = values.to_dict('index')
    ready_rows = candidates[candidates.calculation_input_ready]
    scores_by_mode = {'clipped': [], 'signed': []}
    for original in ready_rows.reset_index().to_dict('records'):
        key = tuple(original[name] for name in K)
        target = values_by_key[key]
        for mode in ['clipped', 'signed']:
            value, terms = bps_candidate(original, target, mode)
            scores_by_mode[mode].append(value)
            terms_rows.append(dict(zip(K, key), legacy_mode=mode, **terms))
    for mode, scores in scores_by_mode.items():
        candidates.loc[ready_rows.index, f'bps_candidate_{mode}'] = scores
    fixture_rows = []
    complete_rows = []
    extra_fixture_keys = set(map(tuple, source_gaps[['season', 'fixture']].to_numpy()))
    source_bad_keys = {(r['season'], r['fixture']) for r in source_disagreements}
    source_bad_keys.update((r['season'], r['fixture']) for r in old_bonus_residuals)
    for fixture_key, group in candidates.groupby(level=['season', 'fixture'], sort=True):
        codes = list(group.index.get_level_values('code'))
        sides = group.groupby('historical_team_id').minutes.apply(lambda v: int(v.gt(0).sum()))
        roster_ok = len(sides) == 2 and sides.ge(11).all() and fixture_key not in extra_fixture_keys
        ready = bool(group.calculation_input_ready.all() and roster_ok and fixture_key not in source_bad_keys)
        status = dict(season=fixture_key[0], fixture=fixture_key[1], player_matches=len(group),
                      open_fields=int(group.open_fields.sum()), all_ledger_inputs_available=bool(group.open_fields.eq(0).all()),
                      revision_bundle_blocked=fixture_key in blocked_revision,
                      source_population_gap=fixture_key in extra_fixture_keys,
                      official_source_disagreement=fixture_key in source_bad_keys,
                      roster_inventory_check=bool(roster_ok), whole_match_candidates_computed=ready,
                      scoring_qualified=False, training_ready=False)
        if ready:
            for mode in ['clipped', 'signed']:
                scores = dict(zip(codes, group[f'bps_candidate_{mode}']))
                bonuses = bonus_for_complete_fixture(scores, codes)
                for original in group.reset_index().to_dict('records'):
                    key = tuple(original[name] for name in K)
                    bonus = int(bonuses[key[2]])
                    total, _ = total_candidate(original, values_by_key[key], bonus, int(original['defcon_points']))
                    complete_rows.append(dict(zip(K, key), legacy_mode=mode, bonus=bonus, total=total))
        fixture_rows.append(status)
    complete = pd.DataFrame(complete_rows)
    if not complete.empty:
        for mode in ['clipped', 'signed']:
            matched = complete[complete.legacy_mode.eq(mode)].set_index(K)
            candidates.loc[matched.index, f'bonus_candidate_{mode}'] = matched.bonus
            candidates.loc[matched.index, f'total_points_candidate_{mode}'] = matched.total
    candidates['scoring_qualified'] = False
    candidates['training_ready'] = False
    for field in ['assists_2026_27', 'bps_2026_27', 'bonus_2026_27', 'total_points_2026_27']:
        candidates[field] = float('nan')
    fixture_status = pd.DataFrame(fixture_rows)
    differing = candidates.bps_candidate_clipped.notna() & candidates.bps_candidate_clipped.ne(candidates.bps_candidate_signed)
    bonus_diff = candidates.bonus_candidate_clipped.notna() & candidates.bonus_candidate_clipped.ne(candidates.bonus_candidate_signed)
    summary = dict(status='candidate_calculation_only_not_training_ready', inventory_rows=len(inventory),
                   historical_ledger_player_matches=len(baseline), historical_fixtures=len(fixture_rows),
                   original_point_residual_rows=len(residuals), scoring_relevant_rows_outside_ledger=len(source_gaps),
                   historical_bonus_residual_rows=len(old_bonus_residuals),
                   official_fixture_source_disagreements=len(source_disagreements),
                   open_fields=int(req.is_open.sum()), input_complete_player_matches=int(candidates.open_fields.eq(0).sum()),
                   input_complete_fixtures=int(fixture_status.all_ledger_inputs_available.sum()),
                   calculated_player_matches=int(candidates.bps_candidate_clipped.notna().sum()),
                   calculated_whole_fixtures=int(fixture_status.whole_match_candidates_computed.sum()),
                   qualified_historical_fixtures=0, training_ready_historical_rows=0,
                   legacy_hypothesis_bps_differing_rows=int(differing.sum()),
                   legacy_hypothesis_bonus_differing_rows=int(bonus_diff.sum()),
                   legacy_hypothesis_bonus_differing_fixtures=int(candidates[bonus_diff].reset_index()[['season', 'fixture']].drop_duplicates().shape[0]),
                   open_global_gates=qualification['open_gates'])
    save(inventory, output / 'historical_inventory.csv.xz')
    save(candidates.reset_index(), output / 'player_match_candidates.csv.xz')
    save(pd.DataFrame(terms_rows), output / 'bps_component_changes.csv.xz')
    save(fixture_status, output / 'fixture_status.csv')
    save(residuals, output / 'original_point_residuals.csv')
    save(source_gaps[K + ['element', 'name', 'position'] + BASIC_FIELDS], output / 'source_population_gaps.csv')
    save(pd.DataFrame(source_disagreements, columns=['season', 'fixture', 'element', 'field', 'history_value', 'fixture_value', 'reason']), output / 'fixture_source_disagreements.csv')
    save(pd.DataFrame(duplicates, columns=['season', 'fixture', 'element', 'discarded', 'method']), output / 'duplicate_resolution.csv')
    save(pd.DataFrame(old_bonus_residuals, columns=['season', 'fixture', 'code', 'original_bonus', 'recomputed_bonus', 'original_bps']), output / 'historical_bonus_residuals.csv')
    coverage_rows = []
    statistics = ['expected_goals', 'expected_assists', 'expected_goal_involvements',
                  'expected_goals_conceded', 'starts', 'clearances_blocks_interceptions',
                  'tackles', 'recoveries', 'defensive_contribution']
    for season, group in inventory.groupby('season', sort=True):
        active = group[group.scoring_relevant_inventory]
        for field in statistics:
            coverage_rows.append(dict(season=season, field=field, inventory_rows=len(group),
                populated_rows=int(group[field].notna().sum()), scoring_relevant_rows=len(active),
                populated_scoring_relevant_rows=int(active[field].notna().sum()),
                scope='original_fpl_source_only_not_derived_completion'))
    save(pd.DataFrame(coverage_rows), output / 'statistic_coverage.csv')
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    code_hashes = {str(path.relative_to(R)): digest(path) for path in [Path(__file__), P / 'core.py']}
    manifest = dict(version='historical_changed_components_candidates_v1', training_labels_enabled=False,
                    input_sha256=hashes, code_sha256=code_hashes,
                    output_sha256={name: digest(output / name) for name in OUTPUTS if name != 'manifest.json'},
                    counts=summary, basis='Historical FPL plus changed-component hypotheses; no global qualification implied.')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'open_global_gates'}, indent=2))
    return summary


if __name__ == '__main__':
    build()
