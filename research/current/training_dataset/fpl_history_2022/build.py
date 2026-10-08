"""Audit late FPL histories without overwriting any frozen canonical observation."""
from pathlib import Path
import json
import io
import tarfile
import hashlib

import pandas as pd

from plan import P, R, digest
from collect import check_plan

K = ['season', 'fixture', 'code']


def save(frame, name):
    import lzma
    raw = frame.to_csv(index=False, lineterminator='\n').encode()
    (P / name).write_bytes(lzma.compress(raw) if name.endswith('.xz') else raw)


def differences(frame, fields):
    result = []
    for field in fields:
        if field in K:
            continue  # Exact merge keys; unmatched keys are recorded separately.
        same = frame[field].eq(frame[field + '_source'])
        same |= frame[field].isna() & frame[field + '_source'].isna()
        for row in frame.loc[~same, K + [field, field + '_source']].itertuples(index=False, name=None):
            result.append(dict(zip(K, row[:3]), field=field, original=row[3], source=row[4]))
    return pd.DataFrame(result, columns=K + ['field', 'original', 'source'])


def main():
    check_plan()
    protocol = json.loads((P / 'protocol.json').read_text())
    gates = protocol['gates']
    manifest = json.loads((P / 'raw_manifest.json').read_text())
    if digest(P / 'raw_inputs.tar.gz') != manifest['archive_sha256'] or digest(P / 'plan_lock.json') != manifest['plan_lock_sha256']:
        raise ValueError('Late-history archive/plan changed')
    register = pd.read_csv(R / 'project/data/2022-23_players.csv.gz').set_index('id')
    frames = []
    with tarfile.open(P / 'raw_inputs.tar.gz') as archive:
        for row in manifest['entries']:
            if row['status'] != 'archived':
                continue
            raw = archive.extractfile(row['file']).read()
            if hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('Late-history member bytes changed')
            data = pd.read_csv(io.BytesIO(raw))
            if not data.element.eq(row['element']).all():
                raise ValueError('Archived player identity mismatch')
            data['season'], data['code'] = '2022-23', int(register.loc[row['element'], 'code'])
            data['source_file'], data['source_sha256'] = row['file'], row['sha256']
            frames.append(data)
    source = pd.concat(frames, ignore_index=True).sort_values(K)
    duplicate_count = int(source.duplicated(K, keep=False).sum())
    save(source, 'late_player_history.csv.xz')
    if duplicate_count:
        raise ValueError('Duplicate late-history fixture identity')
    original = pd.read_csv(P.parent / 'scoring/results/historical_inventory.csv.xz', low_memory=False)
    original = original[original.season.eq('2022-23')]
    combined = original.merge(source, on=K, how='outer', validate='one_to_one', suffixes=('', '_source'), indicator=True)
    save(combined[combined._merge.ne('both')][K + ['element', 'element_source', '_merge']], 'source_inventory_gaps.csv')
    both = combined[combined._merge.eq('both')].copy()
    identity = differences(both, protocol['identity_fields'])
    anchors = differences(both, protocol['performance_anchors'])
    save(identity, 'identity_disagreements.csv')
    save(anchors, 'performance_disagreements.csv')
    controls = both[both.fixture_event.ge(16) & ~both.element.isin([318,407,346])].copy()
    fields = [x for x in protocol['target_fields'] if x != 'starts']
    stat_rows = []
    for field in fields:
        difference = (controls[field] - controls[field + '_source']).abs()
        valid = controls[field].notna() & controls[field + '_source'].notna()
        errors = valid & difference.gt(gates['maximum_late_xg_absolute_rounding_difference'])
        stat_rows.append(dict(field=field, controls=int(valid.sum()), errors=int(errors.sum()),
            maximum_difference=float(difference.max())))
    save(pd.DataFrame(stat_rows), 'late_xg_controls.csv')
    failures = []
    for field in fields:
        valid = controls[field].notna() & controls[field + '_source'].notna()
        bad = valid & (controls[field] - controls[field + '_source']).abs().gt(gates['maximum_late_xg_absolute_rounding_difference'])
        for row in controls.loc[bad, K + [field, field + '_source']].itertuples(index=False, name=None):
            failures.append(dict(zip(K,row[:3]), field=field, original=row[3], source=row[4]))
    save(pd.DataFrame(failures, columns=K + ['field','original','source']), 'late_xg_disagreements.csv')
    late_start_errors = int((~controls.starts.eq(controls.starts_source)).sum())
    primary = pd.read_csv(P.parent / 'lineups/primary_reference/explicit_lineups.csv.xz')
    primary = primary[primary.season.eq('2022-23')]
    direct = source.merge(primary[K + ['reference_starts']], on=K, validate='one_to_one')
    primary_errors = int((~direct.starts.eq(direct.reference_starts)).sum())
    additivity = (source.expected_goal_involvements - source.expected_goals - source.expected_assists).abs()
    add_errors = int(additivity.gt(gates['maximum_xgi_additivity_difference']).sum())
    season_checks = []
    for code, group in source.groupby('code', sort=True):
        native = register[register.code.eq(code)].iloc[0]
        for field in protocol['target_fields']:
            delta = abs(float(group[field].sum()) - float(native[field]))
            tolerance = 0 if field == 'starts' else len(group) * gates['maximum_season_total_difference_per_summed_row'] + gates['season_total_fixed_rounding_allowance']
            season_checks.append(dict(code=code, field=field, rows=len(group), match_sum=float(group[field].sum()),
                native_total=float(native[field]), absolute_difference=delta, tolerance=tolerance,
                passed=bool(group[field].notna().all() and delta <= tolerance)))
    save(pd.DataFrame(season_checks), 'season_total_checks.csv.xz')
    totals_passed = all(x['passed'] for x in season_checks)
    qualified = len(identity) == 0 and len(anchors) == 0 and controls.fixture.nunique() >= gates['minimum_control_fixtures'] and controls.code.nunique() >= gates['minimum_control_players'] and late_start_errors == 0 and primary_errors == 0 and direct.fixture.nunique() == 136 and add_errors == 0 and totals_passed and all(x['errors'] == 0 for x in stat_rows)
    early = both[both.fixture_event.lt(16)]
    diagnose = both[K + ['fixture_event','element','expected_goals','expected_assists','expected_goal_involvements']].copy()
    diagnose['original_xgi_additivity_error'] = (diagnose.expected_goal_involvements - diagnose.expected_goals - diagnose.expected_assists).abs()
    diagnose['original_xgi_inconsistent'] = diagnose.original_xgi_additivity_error.gt(gates['maximum_xgi_additivity_difference'])
    save(diagnose[diagnose.original_xgi_inconsistent], 'original_xgi_semantic_conflicts.csv')
    conflict_rows = pd.DataFrame(failures)
    if len(conflict_rows):
        conflict_rows = conflict_rows.merge(both[K + ['fixture_event']], on=K, validate='many_to_one')
        grouped = conflict_rows.groupby(['field','fixture_event'], sort=True).size().rename('disagreements').reset_index()
    else:
        grouped = pd.DataFrame(columns=['field','fixture_event','disagreements'])
    save(grouped, 'disagreement_groups.csv')
    outputs = ['late_player_history.csv.xz','source_inventory_gaps.csv','identity_disagreements.csv',
        'performance_disagreements.csv','late_xg_controls.csv','late_xg_disagreements.csv','season_total_checks.csv.xz',
        'original_xgi_semantic_conflicts.csv','disagreement_groups.csv']
    summary = dict(status='qualified_late_fpl_history' if qualified else 'unqualified_late_fpl_history',
        qualified=bool(qualified), source_rows=len(source), canonical_matched_rows=len(both),
        source_unmatched_rows=int(combined._merge.eq('right_only').sum()), original_unmatched_rows=int(combined._merge.eq('left_only').sum()),
        early_candidate_rows=len(early), control_fixtures=int(controls.fixture.nunique()), control_players=int(controls.code.nunique()),
        identity_disagreements=len(identity), anchor_disagreements=len(anchors),
        late_start_disagreements=late_start_errors, direct_primary_rows=len(direct), direct_primary_disagreements=primary_errors,
        xgi_additivity_disagreements=add_errors, season_total_failed_checks=sum(not x['passed'] for x in season_checks),
        xg_groups=stat_rows, protocol_sha256=digest(P / 'protocol.json'), raw_manifest_sha256=digest(P / 'raw_manifest.json'),
        code_sha256=digest(Path(__file__)), scoring_qualified=False, historical_feature_availability_qualified=False,
        evidence_type=protocol['design'], output_sha256={name:digest(P / name) for name in outputs})
    (P / 'validation_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
