"""Validate complete-start inference and extend the separate starts-only view."""
from pathlib import Path
import json
import importlib.util

import pandas as pd

spec = importlib.util.spec_from_file_location('start_conservation_predict', Path(__file__).with_name('predict.py'))
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
P, R, K, digest, save, conserve = candidate.P, candidate.R, candidate.K, candidate.digest, candidate.save, candidate.conserve


def main():
    lock = json.loads((P / 'freeze.json').read_text())
    for name, sha in lock['input_sha256'].items():
        if digest(R / name) != sha:
            raise ValueError('Frozen conservation input changed: ' + name)
    if lock['outcomes_read'] or digest(P / 'predict.py') != lock['prediction_code_sha256'] or digest(P / 'predictions.csv.xz') != lock['prediction_sha256'] or digest(P / 'complete_start_inventories.csv') != lock['proof_sha256']:
        raise ValueError('Invalid conservation freeze')
    protocol = json.loads((P / 'protocol.json').read_text())
    original = pd.read_csv(P.parent.parent / 'scoring/results/historical_inventory.csv.xz', usecols=K + ['starts', 'fixture_event', 'was_home'])
    predictions = pd.read_csv(P / 'predictions.csv.xz')
    controls = predictions.merge(original.drop(columns='was_home'), on=K, validate='one_to_one')
    controls = controls[controls.season.ge('2022-23') & controls.starts.notna()].copy()
    primary = pd.read_csv(P.parent / 'primary_reference/explicit_lineups.csv.xz')
    # Separate truth comes from complete primary starting sets, never candidate starts.
    primary_early = primary[primary.scope.eq('structural_start_reference')]
    truth_population = original[original.season.eq('2022-23') & original.fixture_event.lt(16)][K + ['was_home']]
    direct = truth_population.merge(primary_early[K + ['reference_starts']], on=K, how='left', validate='one_to_one')
    direct = direct.rename(columns={'reference_starts': 'predicted_starts'})
    reference, primary_proofs = conserve(direct)
    if len(primary_proofs) != 136 or not primary_proofs.complete.all():
        raise ValueError('Incomplete primary early starting inventory')
    controls = controls.merge(reference[K + ['completed_starts']].rename(columns={'completed_starts':'primary_truth'}), on=K, how='left', validate='one_to_one')
    controls['compatible_starts'] = controls.starts
    early = controls.season.eq('2022-23') & controls.fixture_event.lt(16)
    controls.loc[early, 'compatible_starts'] = controls.loc[early, 'primary_truth']
    controls['agrees'] = controls.completed_starts.eq(controls.compatible_starts)
    direct_checks = predictions.merge(primary[K + ['reference_starts']], on=K, validate='one_to_one')
    primary_errors = int((~direct_checks.completed_starts.eq(direct_checks.reference_starts)).sum())
    gates, groups = protocol['gates'], []
    for season, group in controls.groupby('season', sort=True):
        fixtures = group.fixture.nunique()
        positives, negatives = int(group.compatible_starts.eq(1).sum()), int(group.compatible_starts.eq(0).sum())
        errors = int((~group.agrees).sum())
        groups.append(dict(season=season, rows=len(group), fixtures=fixtures, positives=positives,
            negatives=negatives, disagreements=errors, passed=fixtures >= gates['minimum_control_fixtures_per_season'] and positives >= gates['minimum_positive_per_season'] and negatives >= gates['minimum_negative_per_season'] and errors <= gates['maximum_disagreements']))
    old = pd.read_csv(P.parent / 'starts_qualified.csv.xz', low_memory=False)
    final = old.merge(predictions[K + ['completed_starts', 'conservation_zero', 'complete_start_inventory']], on=K, validate='one_to_one')
    known = final.starts_qualified.notna()
    existing_errors = int((~final.loc[known, 'starts_qualified'].eq(final.loc[known, 'completed_starts'])).sum())
    proofs = pd.read_csv(P / 'complete_start_inventories.csv')
    passed = len(groups) == 4 and all(x['passed'] for x in groups) and len(proofs) == 2660 and proofs.complete.all() and primary_errors == 0 and existing_errors == 0
    save(controls, P / 'control_comparisons.csv.xz')
    save(pd.DataFrame(groups), P / 'control_summary.csv')
    summary = dict(qualified=bool(passed), groups=groups, controls=len(controls),
        complete_fixtures=int(proofs.complete.sum()), primary_controls=len(direct_checks),
        primary_disagreements=primary_errors, existing_value_changes=existing_errors,
        prediction_sha256=lock['prediction_sha256'], freeze_sha256=digest(P / 'freeze.json'),
        code_sha256=digest(Path(__file__)), scoring_qualified=False, evidence_type=protocol['design'])
    (P / 'validation_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    if not passed:
        raise ValueError('Full start-inventory qualification failed')
    missing = ~known
    if not final.loc[missing, 'conservation_zero'].all():
        raise ValueError('A new start value lacks conservation proof')
    final.loc[missing, 'starts_qualified'] = 0
    final.loc[missing, 'starts_quality'] = 'qualified_complete_start_inventory_zero'
    final.loc[missing, 'starts_value_qualified'] = True
    save(final, P / 'starts_qualified.csv.xz')
    coverage = final.groupby('season', sort=True).agg(rows=('code','size'),
        qualified=('starts_value_qualified','sum'), conserved_zero=('conservation_zero','sum')).reset_index()
    save(coverage, P / 'coverage.csv')
    manifest = dict(status='qualified_starts_full_canonical_coverage', rows=len(final),
        qualified_rows=int(final.starts_value_qualified.sum()), new_qualified_zeros=int(missing.sum()),
        complete_fixtures=2660, original_values_preserved=True, scoring_qualified=False,
        training_dataset_ready=False, validation_sha256=digest(P / 'validation_summary.json'),
        output_sha256={name:digest(P / name) for name in ['starts_qualified.csv.xz','coverage.csv']},
        limitations='Only start role completed. No inference for minutes or other event counters; historical publication time remains unqualified. Prior partial starts view and raw FPL preserved.')
    (P / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
