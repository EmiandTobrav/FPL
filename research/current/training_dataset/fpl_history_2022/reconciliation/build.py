"""Verify real FPL snapshot objects and create a separate reconciled stats view."""
from pathlib import Path
import json
import hashlib
import tarfile

import numpy as np
import pandas as pd

from plan import P, R, FIELDS, digest
from collect import check_plan

K = ['season','fixture','code']


def save(frame, name):
    import lzma
    raw = frame.to_csv(index=False, lineterminator='\n').encode()
    (P / name).write_bytes(lzma.compress(raw) if name.endswith('.xz') else raw)


def verify_snapshot_objects(plan, directories, blobs, manifest, archive_path):
    planned_paths = {row['path'] for row in plan['players']}
    entry_paths = {row['path'] for row in manifest['entries']}
    directory_paths = {path.rsplit('/', 1)[0] for path in planned_paths}
    if (len(plan['players']) != 778 or len(planned_paths) != 778
            or directories.path.duplicated().any() or blobs.path.duplicated().any()
            or set(directories.path) != directory_paths or set(blobs.path) != planned_paths
            or entry_paths != planned_paths or len(manifest['entries']) != len(entry_paths)
            or len({row['element'] for row in manifest['entries']}) != 778
            or len({row['file'] for row in manifest['entries']}) != 778):
        raise ValueError('Duplicate/incomplete final snapshot identity inventory')
    trees = directories.set_index('path').tree_sha.to_dict()
    blob_ids = blobs.set_index('path').git_blob_sha.to_dict()
    if len(trees) != 778 or len(blob_ids) != 778 or len(manifest['entries']) != 778:
        raise ValueError('Incomplete final snapshot object inventory')
    for row in plan['players']:
        if trees.get(row['path'].rsplit('/',1)[0]) != row['directory_tree_sha']:
            raise ValueError('Archived directory changed after season end')
    rows = []
    with tarfile.open(archive_path) as archive:
        archive_files = [member.name for member in archive.getmembers() if member.isfile()]
        if (len(archive_files) != len(set(archive_files))
                or set(archive_files) != {row['file'] for row in manifest['entries']}):
            raise ValueError('Archive members do not match unique final inventory')
        for row in manifest['entries']:
            raw = archive.extractfile(row['file']).read()
            sha = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            if hashlib.sha256(raw).hexdigest() != row['sha256'] or sha != blob_ids.get(row['path']):
                raise ValueError('Final CSV bytes do not match archived 2023 Git object')
            rows.append(dict(element=row['element'], path=row['path'], git_blob_sha=sha,
                sha256=row['sha256'], verified=True))
    return pd.DataFrame(rows)


def transform(original, final):
    if (original.empty or not original.season.eq('2022-23').all()
            or not final.season.eq('2022-23').all()
            or original[K].isna().any().any() or final[K].isna().any().any()
            or original.duplicated(K).any() or final.duplicated(K).any()
            or set(map(tuple, original[K].to_numpy())) != set(map(tuple, final[K].to_numpy()))):
        raise ValueError('Expected complete unique 2022/23 original/final identities')
    if not original.fixture_event.between(1, 38).all():
        raise ValueError('Unknown canonical fixture event')
    if final[['source_file', 'source_sha256']].isna().any().any():
        raise ValueError('Missing final source provenance')
    result = original.merge(final[K + FIELDS + ['source_file','source_sha256']], on=K,
        how='left', validate='one_to_one', suffixes=('', '_final'))
    early, revised = result.fixture_event.lt(16), result.fixture_event.eq(16)
    for field in FIELDS:
        result[field + '_original'] = result[field]
        result[field + '_qualified'] = result[field]
        result[field + '_quality'] = 'native_compatible_fpl'
        result.loc[early, field + '_qualified'] = result.loc[early, field + '_final']
        result.loc[early, field + '_quality'] = 'direct_final_fpl_backfill'
        result.loc[revised, field + '_qualified'] = result.loc[revised, field + '_final']
        result.loc[revised, field + '_quality'] = 'documented_later_fpl_snapshot_revision'
    gi, xg, xa = 'expected_goal_involvements', 'expected_goals', 'expected_assists'
    sum_native = (result[xg] + result[xa]).round(2)
    corrected = result.fixture_event.eq(29) & (result[gi] - sum_native).abs().gt(.01000001)
    result.loc[corrected, gi + '_qualified'] = sum_native[corrected]
    result.loc[corrected, gi + '_quality'] = 'exact_native_xg_plus_xa_repair'
    allowed = early | revised
    for field in FIELDS:
        scope = allowed | (corrected if field == gi else False)
        if not result.loc[~scope, field + '_qualified'].eq(result.loc[~scope,field]).all():
            raise ValueError('A compatible original statistic was changed outside scope')
        values = result[field + '_qualified']
        if not values.notna().all() or not np.isfinite(values).all() or not values.ge(0).all():
            raise ValueError('Incomplete/nonfinite/negative expected statistic')
    result['historical_feature_availability_qualified'] = False
    return result, corrected


def season_checks(view, register, gates):
    checks = []
    for code, group in view.groupby('code', sort=True):
        native = register[register.code.eq(code)]
        if len(native) != 1:
            raise ValueError('Ambiguous final season register identity')
        for field in FIELDS:
            values = group[field + '_qualified']
            delta = abs(float(values.sum()) - float(native.iloc[0][field]))
            tolerance = (len(group) * gates['maximum_season_total_difference_per_summed_row']
                         + gates['season_total_fixed_rounding_allowance'])
            checks.append(dict(code=code, field=field, rows=len(group),
                qualified_sum=float(values.sum()), native_total=float(native.iloc[0][field]),
                absolute_difference=delta, tolerance=tolerance,
                passed=bool(values.notna().all() and delta <= tolerance)))
    return pd.DataFrame(checks)


def main():
    check_plan()
    evidence = json.loads((P / 'evidence_lock.json').read_text())
    for name, sha in evidence['input_sha256'].items():
        if digest(P / name) != sha:
            raise ValueError('Additional source evidence changed: ' + name)
    protocol = json.loads((P / 'protocol.json').read_text())
    prior = json.loads((P.parent / 'validation_summary.json').read_text())
    if prior['qualified'] or prior['identity_disagreements'] or prior['anchor_disagreements'] or prior['season_total_failed_checks'] or prior['late_start_disagreements'] or prior['direct_primary_disagreements'] or prior['xgi_additivity_disagreements'] or prior['source_unmatched_rows'] or prior['original_unmatched_rows']:
        raise ValueError('Required prior authenticity/algebra controls not established')
    meta = json.loads((P / 'source_metadata.json').read_text())
    if pd.Timestamp(meta['gw16_commit_date']) >= pd.Timestamp(meta['late_commit_date']):
        raise ValueError('Final snapshot is not chronologically later')
    sources = json.loads((P.parent / 'raw_manifest.json').read_text())
    source_plan = json.loads((P.parent / 'source_plan.json').read_text())
    objects = verify_snapshot_objects(source_plan, pd.read_csv(P / 'end_season_directory_trees.csv'),
        pd.read_csv(P / 'end_season_file_blobs.csv'), sources, P.parent / 'raw_inputs.tar.gz')
    save(objects, 'verified_final_objects.csv')
    weekly_meta = json.loads((P / 'weekly_source.json').read_text())
    if digest(P / 'gw16_2022_11_23.csv') != weekly_meta['sha256']:
        raise ValueError('Original weekly snapshot bytes changed')
    original = pd.read_csv(P.parents[1] / 'scoring/results/historical_inventory.csv.xz', low_memory=False)
    original = original[original.season.eq('2022-23')]
    weekly = pd.read_csv(P / 'gw16_2022_11_23.csv')
    reg = pd.read_csv(R / 'project/data/2022-23_players.csv.gz').set_index('id')
    weekly['code'], weekly['season'] = weekly.element.map(reg.code), '2022-23'
    compared = original[original.fixture_event.eq(16)].merge(weekly, on=K, how='outer',
        validate='one_to_one', suffixes=('', '_archived'), indicator=True)
    fields = ['element','was_home','opponent_team','team_h_score','team_a_score','kickoff_time',
        'minutes','goals_scored','own_goals','penalties_missed','penalties_saved','saves','yellow_cards','red_cards'] + FIELDS
    if not compared._merge.eq('both').all():
        raise ValueError('Old weekly snapshot does not match canonical inventory')
    checks = []
    for field in fields:
        errors = int((~compared[field].eq(compared[field + '_archived'])).sum())
        checks.append(dict(field=field, rows=len(compared), disagreements=errors))
    save(pd.DataFrame(checks), 'same_old_snapshot_checks.csv')
    if any(x['disagreements'] for x in checks):
        raise ValueError('Canonical GW16 does not reproduce the exact old FPL version')
    final = pd.read_csv(P.parent / 'late_player_history.csv.xz')
    view, corrected = transform(original, final)
    totals = season_checks(view, reg, protocol['unchanged_numeric_gates'])
    save(totals, 'qualified_season_total_checks.csv.xz')
    if not totals.passed.all():
        raise ValueError('Reconciled season aggregates fail unchanged rounding gates')
    algebra = (view.expected_goal_involvements_qualified - view.expected_goals_qualified - view.expected_assists_qualified).abs()
    if algebra.gt(protocol['unchanged_numeric_gates']['maximum_xgi_additivity_difference']).any():
        raise ValueError('Reconciled xGI is inconsistent with xG+xA')
    controls = view[view.fixture_event.ge(16) & ~view.element.isin([318,407,346])]
    control_rows = []
    for field in FIELDS:
        delta = (controls[field + '_qualified'] - controls[field + '_final']).abs()
        errors = int(delta.gt(protocol['unchanged_numeric_gates']['maximum_late_xg_absolute_rounding_difference']).sum())
        control_rows.append(dict(field=field, rows=len(controls), disagreements=errors, maximum_difference=float(delta.max())))
    save(pd.DataFrame(control_rows), 'reconciled_reference_checks.csv')
    if controls.fixture.nunique() < protocol['unchanged_numeric_gates']['minimum_control_fixtures'] or controls.code.nunique() < protocol['unchanged_numeric_gates']['minimum_control_players'] or any(x['disagreements'] for x in control_rows):
        raise ValueError('Reconciled official-version checks failed')
    native = reg[reg.code.eq(meta['official_final_season_control']['code'])].iloc[0]
    if any(float(native[field]) != value for field,value in meta['official_final_season_control'].items() if field != 'code'):
        raise ValueError('Final season register conflicts with independent official article')
    records = []
    for field in FIELDS:
        for row in view[K + [field + '_original',field + '_qualified',field + '_quality']].itertuples(index=False, name=None):
            if row[3] != row[4]:
                records.append(dict(zip(K,row[:3]), field=field, original=row[3], reconciled=row[4], reason=row[5]))
    save(pd.DataFrame(records), 'documented_revisions.csv.xz')
    save(view, 'expected_statistics_qualified.csv.xz')
    files = ['verified_final_objects.csv','same_old_snapshot_checks.csv','reconciled_reference_checks.csv',
        'documented_revisions.csv.xz','expected_statistics_qualified.csv.xz',
        'qualified_season_total_checks.csv.xz']
    summary = dict(status='qualified_same_fpl_expected_stat_version', statistic_values_qualified=True,
        rows=len(view), fixtures=view.fixture.nunique(), verified_final_git_objects=len(objects),
        exact_old_snapshot_rows=len(compared), direct_backfilled_rows=int(view.fixture_event.lt(16).sum()),
        revised_snapshot_rows=int(view.fixture_event.eq(16).sum()), mathematical_xgi_repair_rows=int(corrected.sum()),
        changed_field_values=len(records), retained_v1_qualified=False,
        qualified_season_total_checks=len(totals), qualified_season_total_failed_checks=0,
        source_snapshot_dates=dict(weekly=meta['gw16_commit_date'], final=meta['late_commit_date']),
        historical_feature_availability_qualified=False, scoring_qualified=False, training_dataset_ready=False,
        evidence_type=protocol['design'], protocol_sha256=digest(P / 'protocol.json'), code_sha256=digest(Path(__file__)),
        input_sha256={name:digest(R/name) for name in json.loads((P/'plan_lock.json').read_text())['input_sha256']},
        evidence_lock_sha256=digest(P / 'evidence_lock.json'),
        additional_evidence_sha256=evidence['input_sha256'],
        output_sha256={name:digest(P/name) for name in files})
    (P / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k:v for k,v in summary.items() if not k.endswith('sha256')}, indent=2))


if __name__ == '__main__':
    main()
