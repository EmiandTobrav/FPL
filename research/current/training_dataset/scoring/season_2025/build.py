"""Qualify 2025/26 only; retain unresolved fixtures and inactive rows as missing."""
from pathlib import Path
import gzip
import hashlib
import json
import sys

import pandas as pd

P = Path(__file__).resolve().parent
R = P.parents[2]
S = R / 'scoring_2026_27'
sys.path.insert(0, str(P.parent))
from core import (basic_component_account, bonus_for_complete_fixture,
                  bps_candidate, total_candidate)
from historical import save

K = ['season', 'fixture', 'code']
OUTPUTS = ['player_matches.csv.xz', 'qualified_player_matches.csv.xz',
           'fixture_status.csv', 'changed_bps_components.csv.xz',
           'basic_components.csv.xz', 'inside_save_controls.csv',
           'times_tackled_controls.csv', 'big_chance_save_season_controls.csv',
           'keeper_primary_comparisons.csv', 'qualification.json', 'summary.json',
           'manifest.json']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def nonnegative_integer(value):
    if isinstance(value, bool) or pd.isna(value) or int(value) != value or value < 0:
        raise ValueError('Counter must be an explicit nonnegative integer')
    return int(value)

def season_exhaustion(values, season_total, appearances, expected_appearances):
    """Prove omitted counts only after exact, complete nonnegative conservation."""
    total = nonnegative_integer(season_total)
    if appearances != expected_appearances or len(values) != expected_appearances:
        raise ValueError('Incomplete primary season appearance inventory')
    explicit = [nonnegative_integer(v) for v in values if v is not None]
    if sum(explicit) != total:
        raise ValueError('Explicit match counts do not exhaust primary season total')
    return [0 if v is None else nonnegative_integer(v) for v in values]

def whole_fixture_eligible(group, ledger_keys, open_fixtures, blocked_fixtures):
    fixture = int(group.fixture.iloc[0])
    keys = set(map(tuple, group[K].to_numpy()))
    sides = group.groupby('historical_team_id').minutes.apply(lambda x: int(x.gt(0).sum()))
    return bool(keys <= ledger_keys and fixture not in open_fixtures
        and fixture not in blocked_fixtures and len(sides) == 2 and sides.ge(11).all()
        and group.original_point_residual.eq(0).all() and group.kickoff_sources_agree.all())

def primary_keeper_checks(inventory, req):
    plan = pd.read_csv(P / 'keeper_revision_plan.csv')
    manifest = pd.read_csv(P / 'keeper_revision_sources.csv')
    if plan.fixture.duplicated().any() or manifest.fixture.duplicated().any():
        raise ValueError('Duplicate primary source fixture')
    expected = inventory[inventory.code.eq(200720) & inventory.minutes.gt(0)]
    if set(plan.fixture) != set(expected.fixture) or len(plan) != 37:
        raise ValueError('Primary keeper plan is not full native appearance inventory')
    fixtures = pd.read_csv(R / 'project/data/2025-26_fixtures.csv.gz').set_index('id')
    for row in plan.itertuples():
        anchor = fixtures.loc[row.fixture]
        if row.pulse_id != anchor.pulse_id or row.fixture_code != anchor.code or row.kickoff_time != anchor.kickoff_time:
            raise ValueError('Primary fixture identity mismatch')
    stats = {}
    for row in manifest.itertuples():
        path = P / row.file
        raw = gzip.decompress(path.read_bytes())
        if sha(path) != row.file_sha256 or hashlib.sha256(raw).hexdigest() != row.raw_sha256:
            raise ValueError('Primary raw response fingerprint changed')
        obj = json.loads(raw)
        if obj['entity']['id'] != 14723 or obj['entity']['altIds']['opta'] != 'p200720':
            raise ValueError('Primary keeper identity mismatch')
        entries = obj['stats']
        if len({x['name'] for x in entries}) != len(entries):
            raise ValueError('Duplicate primary counter')
        values = {x['name']: x['value'] for x in entries}
        if row.fixture:
            anchor = plan.set_index('fixture').loc[row.fixture]
            url = f'https://footballapi.pulselive.com/football/stats/player/14723?fixtures={int(anchor.pulse_id)}&altIds=true'
            if row.url != url or values.get('appearances') != 1 or values.get('mins_played') != anchor.minutes:
                raise ValueError('Primary match scope/minutes mismatch')
        elif row.url != 'https://footballapi.pulselive.com/football/stats/player/14723?comps=1&compSeasons=777&altIds=true':
            raise ValueError('Primary season scope mismatch')
        stats[row.fixture] = values
    if set(stats) != {0, *plan.fixture}:
        raise ValueError('Incomplete collected primary fixture plan')
    ordered = sorted(plan.fixture)
    proved = season_exhaustion([stats[f].get('big_chance_saves') for f in ordered],
        stats[0].get('big_chance_saves'), stats[0].get('appearances'), len(expected))
    reference = req[req.code.eq(200720) & req.field.eq('big_chance_saves')].set_index('fixture')
    rows = [dict(season='2025-26', fixture=f, code=200720,
                 primary_explicit=stats[f].get('big_chance_saves'), primary_proved=v,
                 approved_value=int(reference.loc[f, 'value']),
                 agrees=v == reference.loc[f, 'value'],
                 proof='explicit' if stats[f].get('big_chance_saves') is not None else 'complete_season_exhaustion')
            for f, v in zip(ordered, proved)]
    return pd.DataFrame(rows), int(stats[0]['big_chance_saves'])

def build():
    out = P / 'results'
    out.mkdir(exist_ok=True)
    lock = json.loads((P / 'input_lock.json').read_text())
    for name, expected in lock['input_sha256'].items():
        if sha(R / name) != expected:
            raise ValueError(f'Frozen qualification input changed: {name}')
    protocol = json.loads((P / 'protocol.json').read_text())
    pointer = json.loads((P / 'inputs/ledger_CURRENT.json').read_text())
    req_path = S / 'bulk_reconciliation' / pointer['requirements']
    if sha(req_path) != pointer['requirements_sha256']:
        raise ValueError('Frozen ledger disagrees with qualification pointer')
    req = pd.read_csv(req_path, low_memory=False)
    if int(req.is_open.sum()) != pointer['open_fields']:
        raise ValueError('Frozen ledger open count differs')
    req = req[req.season.eq('2025-26')].copy()
    inv = pd.read_csv(R / 'training_dataset/scoring/results/historical_inventory.csv.xz', low_memory=False)
    inv = inv[inv.season.eq('2025-26')].copy().sort_values(K)
    if inv.duplicated(K).any() or req.duplicated(K + ['field']).any():
        raise ValueError('Duplicate canonical or requirement key')
    relevant = inv[inv.scoring_relevant_inventory].copy()
    source_disagreements = pd.read_csv(R / 'training_dataset/scoring/results/fixture_source_disagreements.csv')
    if not source_disagreements[source_disagreements.season.eq('2025-26')].empty:
        raise ValueError('2025/26 native FPL source disagreement')
    values = req.pivot(index=K, columns='field', values='value')
    ledger_keys = set(values.index)
    native = inv.set_index(K)
    checks = {}
    for field, original in [('assists_2026_27', 'assists'), ('historical_bps', 'bps'),
        ('clearances_blocks_interceptions', 'clearances_blocks_interceptions'),
        ('defensive_contribution', 'defensive_contribution'), ('saves', 'saves'),
        ('penalties_saved', 'penalties_saved')]:
        rows = req[req.field.eq(field)]
        keys = pd.MultiIndex.from_frame(rows[K])
        if not rows.status.eq('fpl_authoritative').all() or not rows.value.to_numpy().tolist() == native.loc[keys, original].to_numpy().tolist():
            raise ValueError(f'Native qualification input differs: {field}')
        checks[f'native_{field}'] = len(rows)
    primary = pd.read_csv(S / 'delta_input_audit/primary_comparisons.csv.gz')
    tt = primary[primary.season.eq('2025-26') & primary.field.eq('timesTackled')].copy()
    equal = tt[tt.comparison.eq('equal_explicit')]
    bad = tt[tt.comparison.eq('explicit_conflict')]
    if len(equal) != 68 or not equal.archive.eq(equal.primary).all() or set(zip(bad.fixture,bad.code)) != {(356,248875)}:
        raise ValueError('Frozen times-tackled qualification controls differ')
    for row in bad.itertuples():
        status = req[(req.fixture.eq(row.fixture)) & req.code.eq(row.code) & req.field.eq('times_tackled')]
        if len(status) != 1 or not status.is_open.all() or status.value.notna().any():
            raise ValueError('Known times-tackled conflict was silently accepted')
    checks['times_tackled_explicit_equal'] = len(equal)
    keeper = S / 'bulk_reconciliation/followup_2026_10_08/fotmob_keeper_location'
    keeper_manifest = json.loads((keeper / 'results/manifest.json').read_text())
    for name in ['keeper_predictions.csv','save_evidence.csv','control_comparisons.csv','findings.json']:
        if sha(keeper / 'results' / name) != keeper_manifest['outputs_sha256'][name]:
            raise ValueError('Qualified keeper producer output changed')
    preds = pd.read_csv(keeper / 'results/keeper_predictions.csv')
    evidence = pd.read_csv(keeper / 'results/save_evidence.csv')
    controls = pd.read_csv(keeper / 'results/control_comparisons.csv')
    if len(controls) != 40 or not controls.eligible.all() or not controls.agrees.all():
        raise ValueError('Frozen outside-save controls failed')
    counts = evidence.groupby(K).is_from_inside_box.sum()
    inside_rows = []
    for row in preds[preds.eligible].itertuples():
        key = (row.season, row.fixture, row.code)
        inside = int(counts.get(key, 0))  # zero only within a proved complete saved-shot inventory
        ref = values.loc[key, 'saves_inside_box']
        inside_rows.append(dict(zip(K,key), direct_inside=inside, reference_inside=ref, agrees=inside==ref,
            located_saves=row.located_saves, proof='qualified_complete_saved_shot_inventory'))
    inside = pd.DataFrame(inside_rows)
    if len(inside) != 543 or not inside.agrees.all():
        raise ValueError('Inside-save mapping failed eligible population check')
    checks['inside_save_population_equal'] = len(inside)
    checks['outside_save_frozen_controls_equal'] = len(controls)
    bc = pd.read_csv(S / 'keeper_recovery/current_season_validation.csv')
    explicit = bc[bc.explicit.notna()]
    if len(explicit) != 52 or not explicit.explicit.eq(explicit.derived).all() or bc.problems.notna().any():
        raise ValueError('Big-chance-save explicit target-season controls failed')
    checks['big_chance_save_explicit_controls_equal'] = len(explicit)
    fresh, primary_total = primary_keeper_checks(inv, req)
    changed = fresh[~fresh.agrees]
    if set(zip(changed.fixture,changed.code)) != {(337,200720)}:
        raise ValueError('Primary keeper audit has an unreviewed revision')
    season_rows = []
    for code, official in protocol['official_2025_big_chance_save_totals'].items():
        observed = int(req[req.code.eq(int(code)) & req.field.eq('big_chance_saves')].value.sum())
        reviewed = primary_total if int(code)==200720 else observed
        if reviewed != official:
            raise ValueError('Unresolved official big-chance-save season control')
        season_rows.append(dict(code=int(code), approved_season_sum=observed, official_total=official,
            primary_audited_total=primary_total if int(code)==200720 else None,
            exact_after_localized_quarantine=True, quarantined_fixture=337 if int(code)==200720 else None))
    blocked_fixtures = set(changed.fixture)
    open_fixtures = set(req[req.is_open].fixture)
    # Open values never enter a row calculation, even when a secondary raw column has a number.
    usable = req.copy()
    usable.loc[usable.is_open, 'value'] = float('nan')
    targets = usable.pivot(index=K, columns='field', values='value').to_dict('index')
    old_bonus_residuals = []
    statuses, labels, changes, basics = [], [], [], []
    for fixture, group in relevant.groupby('fixture', sort=True):
        old = bonus_for_complete_fixture(dict(zip(group.code, group.bps)), group.code)
        old_bonus_residuals.extend([(fixture,row.code) for row in group.itertuples() if old[row.code] != row.bonus])
        for row in group.to_dict('records'):
            component = basic_component_account(row, int(row['defcon_points']))
            if sum(component.values()) != row['total_points'] - row['bonus']:
                raise ValueError('Original independent basic-point account differs')
        eligible = whole_fixture_eligible(group, ledger_keys, open_fixtures, blocked_fixtures)
        statuses.append(dict(season='2025-26', fixture=fixture,
            scoring_relevant_player_matches=len(group),
            ledger_input_complete=fixture not in open_fixtures,
            open_fields=int(req[req.fixture.eq(fixture)].is_open.sum()),
            source_population_gap=not set(map(tuple,group[K].to_numpy())) <= ledger_keys,
            source_revision_quarantined=fixture in blocked_fixtures,
            scoring_qualified=eligible, training_ready=False))
        if not eligible:
            continue
        scores, term_values = {}, {}
        rows = group.to_dict('records')
        for row in rows:
            key = tuple(row[k] for k in K)
            score, terms = bps_candidate(row, targets[key], legacy_mode=None)
            if terms.get('assists') != 0 or set(terms) - {'cbi','remove_times_tackled','assists','keeper_saves'}:
                raise ValueError('Unexpected season-specific changed BPS term')
            scores[row['code']], term_values[row['code']] = score, terms
        bonuses = bonus_for_complete_fixture(scores, group.code)
        for row in rows:
            key = tuple(row[k] for k in K)
            target, bonus = targets[key], int(bonuses[row['code']])
            total, basic_delta = total_candidate(row, target, bonus, int(row['defcon_points']))
            account = basic_component_account(row, int(row['defcon_points']))
            if sum(basic_delta.values()) != 0 or sum(account.values()) + bonus != total:
                raise ValueError('Target basic account residual or defensive-award double count')
            labels.append(dict(zip(K,key), bps_2026_27=scores[row['code']], bonus_2026_27=bonus,
                assists_2026_27=int(target['assists_2026_27']), total_points_2026_27=total,
                defcon_points_2026_27=int(row['defcon_points'])))
            changes.append(dict(zip(K,key), original_bps=row['bps'], **term_values[row['code']],
                bps_2026_27=scores[row['code']]))
            basics.append(dict(zip(K,key), **account, bonus=bonus, total_points_2026_27=total, residual=0))
    if old_bonus_residuals:
        raise ValueError('Original whole-fixture bonus residual')
    fixture_status = pd.DataFrame(statuses)
    qualified = pd.DataFrame(labels)
    if qualified.duplicated(K).any() or len(fixture_status) != 380:
        raise ValueError('Incomplete or duplicate qualification inventory')
    inv = inv.merge(qualified, how='left', on=K, validate='one_to_one')
    inv['scoring_qualified'] = inv.total_points_2026_27.notna()
    # Publish the newly qualified counters beside labels, with ledger provenance.
    # Never manufacture keeper counters for outfield players or inactive rows.
    for field in ['times_tackled','saves_inside_box','saves_outside_box','big_chance_saves']:
        source = req[req.field.eq(field)].set_index(K)
        keys = pd.MultiIndex.from_frame(inv[K])
        inv[field] = source.value.reindex(keys).to_numpy()
        inv.loc[~inv.scoring_qualified, field] = float('nan')
        inv[f'{field}_source'] = source.provenance.reindex(keys).to_numpy()
        inv.loc[~inv.scoring_qualified, f'{field}_source'] = None
    inv['training_ready'] = False
    inv['points_version'] = protocol['version']
    inv['label_status'] = 'inactive_inventory_label_unqualified'
    inv.loc[inv.scoring_relevant_inventory, 'label_status'] = 'blocked_whole_fixture'
    inv.loc[inv.scoring_qualified, 'label_status'] = 'qualified_whole_fixture_scoring'
    for field in ['bps','bonus','total_points','assists']:
        inv[f'original_{field}'] = inv[field]
    inv['qualification_manifest'] = 'training_dataset/scoring/season_2025/results/manifest.json'
    checks['original_basic_account_rows'] = len(relevant)
    checks['original_bonus_checked_fixtures'] = len(fixture_status)
    qview = inv[inv.scoring_qualified].copy()
    summary = dict(status='qualified_partial_season_scoring_not_training_ready', source_season='2025-26',
        target_season='2026-27', points_version=protocol['version'],
        canonical_rows=len(inv), scoring_relevant_rows=len(relevant),
        qualified_player_matches=len(qualified), qualified_whole_fixtures=int(fixture_status.scoring_qualified.sum()),
        blocked_whole_fixtures=int((~fixture_status.scoring_qualified).sum()),
        remaining_2025_input_fields=int(req.is_open.sum()), historical_open_fields=pointer['open_fields'],
        changed_bonus_rows=int(qview.original_bonus.ne(qview.bonus_2026_27).sum()),
        changed_total_point_rows=int(qview.original_total_points.ne(qview.total_points_2026_27).sum()),
        target_basic_point_residuals=0, approved_keeper_values_modified=0,
        inactive_rows_with_invented_labels=0, training_ready_rows=0,
        source_revision_fixture=337, source_revision_code=200720,
        source_revision_old_big_chance_saves=0, source_revision_primary_big_chance_saves=1)
    qualification = dict(scope=protocol['scope'], passed=True, checks=checks,
        target_bonus_requires_whole_fixture=True, labels_enabled_only_for_qualified_fixtures=True,
        before_deadline_features_qualified=False, training_pipeline_connected=False,
        other_historical_season_rule_gates_unchanged=True, source_lineage=protocol['source_validation'])
    for frame,name in [(inv,'player_matches.csv.xz'),(qview,'qualified_player_matches.csv.xz'),
        (fixture_status,'fixture_status.csv'),(pd.DataFrame(changes),'changed_bps_components.csv.xz'),
        (pd.DataFrame(basics),'basic_components.csv.xz'),(inside,'inside_save_controls.csv'),
        (tt,'times_tackled_controls.csv'),(pd.DataFrame(season_rows),'big_chance_save_season_controls.csv'),
        (fresh,'keeper_primary_comparisons.csv')]:
        save(frame,out/name)
    for obj,name in [(qualification,'qualification.json'),(summary,'summary.json')]:
        (out/name).write_text(json.dumps(obj,indent=2)+'\n')
    manifest = dict(version=protocol['version'], path_root='research/current',
        input_sha256={**lock['input_sha256'], str((P/'input_lock.json').relative_to(R)):sha(P/'input_lock.json')},
        code_sha256={str(p.relative_to(R)):sha(p) for p in [Path(__file__),P.parent/'core.py',P.parent/'historical.py']},
        output_sha256={name:sha(out/name) for name in OUTPUTS if name!='manifest.json'}, counts=summary)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    build()
