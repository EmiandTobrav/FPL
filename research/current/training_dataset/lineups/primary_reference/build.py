"""Audit official full lineups and evaluate frozen starts against compatible truth."""
from pathlib import Path
import sys
import json
import hashlib
import tarfile
import re

import pandas as pd

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P.parent))
from predict import K, digest, save
from validate import check_freeze
from collect import check_plan


def extract_lineup(data, row, source_sha):
    if data['id'] != row.pulse_id or data['status'] != 'C' or int(data['altIds']['opta'].lstrip('g')) != row.fixture_code:
        raise ValueError('Primary reference fixture mismatch')
    if [x['team']['id'] for x in data['teams']] != [row.home_primary_id, row.away_primary_id]:
        raise ValueError('Primary reference sides mismatch')
    if [x['score'] for x in data['teams']] != [row.home_score, row.away_score]:
        raise ValueError('Primary reference score mismatch')
    if pd.to_datetime(data['kickoff']['millis'], unit='ms', utc=True).strftime('%Y-%m-%d') != row.date:
        raise ValueError('Primary reference date mismatch')
    sides = data['teamLists']
    if len(sides) != 2 or {x['teamId'] for x in sides} != {row.home_primary_id, row.away_primary_id}:
        raise ValueError('Incomplete unique primary sides')
    rows = []
    all_people = []
    for side in sides:
        if len(side['lineup']) != 11:
            raise ValueError('Primary side must have eleven starters')
        for started, people in [(1, side['lineup']), (0, side['substitutes'])]:
            for person in people:
                code = person['altIds']['opta']
                if not re.fullmatch(r'p\d+', code):
                    raise ValueError('Invalid stable primary code')
                all_people.append(person['id'])
                rows.append(dict(season=row.season, fixture=row.fixture, code=int(code[1:]),
                    reference_starts=started, primary_person_id=person['id'],
                    primary_side='home' if side['teamId'] == row.home_primary_id else 'away',
                    source_sha256=source_sha, source_file=f'raw/fixture_{row.pulse_id}.json', scope=row.scope))
    if len(set(all_people)) != len(all_people) or len({x['code'] for x in rows}) != len(rows):
        raise ValueError('Duplicate primary player in full squad')
    return rows


def main():
    check_plan()
    frozen = check_freeze()
    manifest = json.loads((P / 'raw_manifest.json').read_text())
    if digest(P / 'raw_inputs.tar.gz') != manifest['archive_sha256'] or digest(P / 'sources.json') != manifest['sources_sha256'] or digest(P / 'plan_lock.json') != manifest['plan_lock_sha256']:
        raise ValueError('Reference raw source/plan changed')
    sources = {x['file']: x for x in manifest['entries']}
    rows = []
    with tarfile.open(P / 'raw_inputs.tar.gz') as archive:
        for row in pd.read_csv(P / 'fixture_plan.csv').itertuples():
            name = f'raw/fixture_{row.pulse_id}.json'
            raw = archive.extractfile(name).read()
            sha = hashlib.sha256(raw).hexdigest()
            if sha != sources[name]['sha256']:
                raise ValueError('Reference raw member changed')
            rows.extend(extract_lineup(json.loads(raw), row, sha))
    reference = pd.DataFrame(rows).sort_values(K).reset_index(drop=True)
    if reference.duplicated(K).any():
        raise ValueError('Duplicate reference observation')
    save(reference, P / 'explicit_lineups.csv.xz')
    old = pd.read_csv(P.parent.parent / 'scoring/results/historical_inventory.csv.xz',
        usecols=K + ['starts', 'was_home', 'fixture_event'], low_memory=False)
    predictions = pd.read_csv(P.parent / 'predictions.csv.xz', low_memory=False)
    joined = reference.merge(old, on=K, validate='one_to_one')
    if not joined.primary_side.eq(joined.was_home.map({True: 'home', False: 'away'})).all():
        raise ValueError('Primary/reference original club-side mismatch')
    early_raw = old[old.season.eq('2022-23') & old.fixture_event.lt(16)]
    early = joined[joined.scope.eq('structural_start_reference')]
    fixtures = early.groupby('fixture').reference_starts.sum()
    if len(fixtures) != 136 or not fixtures.eq(22).all() or early_raw.fixture.nunique() != 136 or not early_raw.starts.eq(0).all():
        raise ValueError('Early FPL starts incompatibility not established')
    later = joined[joined.scope.eq('later_native_control')].merge(predictions[K + ['predicted_starts']], on=K, validate='one_to_one')
    later['native_agrees'] = later.reference_starts.eq(later.starts)
    later['prediction_agrees'] = later.reference_starts.eq(later.predicted_starts)
    save(later, P / 'later_primary_controls.csv.xz')
    later_ok = len(later[['season', 'fixture']].drop_duplicates()) == 6 and later.native_agrees.all() and later.prediction_agrees.all()
    comparison = predictions[K + ['predicted_starts']].merge(old, on=K, validate='one_to_one').merge(reference, on=K, how='left', validate='one_to_one')
    controls = comparison[comparison.season.ge('2022-23') & comparison.starts.notna() & comparison.predicted_starts.notna()].copy()
    structural = controls.season.eq('2022-23') & controls.fixture_event.lt(16)
    if controls.loc[structural, 'reference_starts'].isna().any():
        raise ValueError('Primary early reference missing a frozen control identity')
    if not controls.loc[structural, 'primary_side'].eq(controls.loc[structural, 'was_home'].map({True: 'home', False: 'away'})).all():
        raise ValueError('Primary early reference side mismatch')
    controls['compatible_starts'] = controls.starts
    controls.loc[structural, 'compatible_starts'] = controls.loc[structural, 'reference_starts']
    controls['reference_type'] = structural.map({True: 'explicit_primary_lineup_structural_repair', False: 'native_compatible_fpl'})
    controls['agrees'] = controls.predicted_starts.eq(controls.compatible_starts)
    protocol = json.loads((P / 'protocol.json').read_text())
    gates = protocol['gates']
    groups = []
    for season, group in controls.groupby('season', sort=True):
        count = group.fixture.nunique()
        positive = int(group.compatible_starts.eq(1).sum())
        negative = int(group.compatible_starts.eq(0).sum())
        errors = int((~group.agrees).sum())
        groups.append(dict(season=season, rows=len(group), fixtures=count,
            positives=positive, negatives=negative, disagreements=errors,
            passed=count >= gates['minimum_control_fixtures_per_season'] and positive >= gates['minimum_positive_per_season'] and negative >= gates['minimum_negative_per_season'] and errors <= gates['maximum_disagreements']))
    passed = later_ok and len(groups) == 4 and all(x['passed'] for x in groups)
    save(controls[K + ['starts', 'predicted_starts', 'compatible_starts', 'reference_type', 'agrees', 'source_sha256']], P / 'compatible_control_comparisons.csv.xz')
    save(pd.DataFrame(groups), P / 'compatible_control_summary.csv')
    summary = dict(version=protocol['version'], qualified=bool(passed),
        evidence_type=protocol['design'] + ' Shared Opta ancestry; not independent holdout.',
        unchanged_prediction_sha256=frozen['prediction_sha256'], groups=groups,
        primary_early_fixtures=136, raw_early_rows=len(early_raw),
        primary_early_starters=int(early.reference_starts.sum()),
        raw_early_start_sum=int(early_raw.starts.sum()),
        later_primary_rows=len(later), later_primary_passed=bool(later_ok),
        later_native_disagreements=int((~later.native_agrees).sum()),
        later_missing_prediction_rows=int(later.predicted_starts.isna().sum()),
        later_observed_prediction_disagreements=int((later.predicted_starts.notna() & ~later.prediction_agrees).sum()),
        changed_reference_rows=int(structural.sum()),
        original_v2_disagreements=int((~controls.predicted_starts.eq(controls.starts)).sum()),
        compatible_disagreements=int((~controls.agrees).sum()),
        primary_reference_sha256=digest(P / 'explicit_lineups.csv.xz'),
        protocol_sha256=digest(P / 'protocol.json'), plan_lock_sha256=digest(P / 'plan_lock.json'),
        raw_manifest_sha256=digest(P / 'raw_manifest.json'), build_code_sha256=digest(Path(__file__)))
    (P / 'validation_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
