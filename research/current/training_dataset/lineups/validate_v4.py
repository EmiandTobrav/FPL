"""Evaluate the separately frozen primary identity extension without lowering gates."""
import json

import pandas as pd

from predict import P, R, K, digest, save


def check_freeze_v4():
    lock = json.loads((P / 'freeze_v4.json').read_text())
    for name, sha in lock['input_sha256'].items():
        if digest(R / name) != sha:
            raise ValueError('V4 frozen input changed: ' + name)
    if lock['outcomes_read'] or digest(P / 'predict_v4.py') != lock['prediction_code_sha256'] or digest(P / 'predictions_v4.csv.xz') != lock['prediction_sha256']:
        raise ValueError('V4 freeze invalid')
    return lock


def main():
    lock = check_freeze_v4()
    protocol = json.loads((P / 'protocol_v4.json').read_text())
    original = pd.read_csv(P.parent / 'scoring/results/historical_inventory.csv.xz', usecols=K + ['starts', 'fixture_event'])
    predictions = pd.read_csv(P / 'predictions_v4.csv.xz', usecols=K + ['predicted_starts'])
    refdir = P / 'primary_reference'
    reference = pd.read_csv(refdir / 'explicit_lineups.csv.xz')
    previous = json.loads((refdir / 'validation_summary.json').read_text())
    if digest(refdir / 'explicit_lineups.csv.xz') != previous['primary_reference_sha256'] or previous['primary_early_starters'] != 2992 or previous['raw_early_start_sum'] != 0 or previous['later_native_disagreements'] != 0:
        raise ValueError('Structural reference/native qualification not established')
    comparisons = predictions.merge(original, on=K, validate='one_to_one').merge(reference[K + ['reference_starts', 'scope']], on=K, how='left', validate='one_to_one')
    controls = comparisons[comparisons.season.ge('2022-23') & comparisons.starts.notna() & comparisons.predicted_starts.notna()].copy()
    early = controls.season.eq('2022-23') & controls.fixture_event.lt(16)
    if controls.loc[early, 'reference_starts'].isna().any():
        raise ValueError('Missing early control reference')
    controls['compatible_starts'] = controls.starts
    controls.loc[early, 'compatible_starts'] = controls.loc[early, 'reference_starts']
    controls['agrees'] = controls.compatible_starts.eq(controls.predicted_starts)
    later = comparisons[comparisons.scope.eq('later_native_control')].copy()
    later['agrees'] = later.reference_starts.eq(later.starts) & later.reference_starts.eq(later.predicted_starts)
    later_ok = len(later) == previous['later_primary_rows'] == 240 and len(later[['season', 'fixture']].drop_duplicates()) == 6 and later.agrees.all()
    groups = []
    gates = protocol['gates']
    if gates != json.loads((P / 'protocol.json').read_text())['gates']:
        raise ValueError('Original qualification gates changed')
    for season, group in controls.groupby('season', sort=True):
        count = group.fixture.nunique()
        positives, negatives = int(group.compatible_starts.eq(1).sum()), int(group.compatible_starts.eq(0).sum())
        errors = int((~group.agrees).sum())
        groups.append(dict(season=season, rows=len(group), fixtures=count, positives=positives, negatives=negatives,
            disagreements=errors, passed=count >= gates['minimum_control_fixtures_per_season'] and positives >= gates['minimum_positive_per_season'] and negatives >= gates['minimum_negative_per_season'] and errors <= gates['maximum_disagreements']))
    passed = later_ok and len(groups) == 4 and all(x['passed'] for x in groups)
    save(controls, P / 'control_comparisons_v4.csv.xz')
    save(pd.DataFrame(groups), P / 'control_summary_v4.csv')
    summary = dict(version=protocol['version'], qualified=bool(passed), groups=groups,
        evidence_type=protocol['design'], unchanged_gates=True, rows=len(controls),
        later_primary_rows=len(later), later_primary_missing=int(later.predicted_starts.isna().sum()),
        later_primary_disagreements=int((~later.agrees).sum()),
        freeze_sha256=digest(P / 'freeze_v4.json'), prediction_sha256=lock['prediction_sha256'],
        primary_reference_sha256=digest(refdir / 'explicit_lineups.csv.xz'),
        reference_validation_sha256=digest(refdir / 'validation_summary.json'),
        validation_code_sha256=digest(P / 'validate_v4.py'), historical_scoring_qualified=False)
    (P / 'validation_summary_v4.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
