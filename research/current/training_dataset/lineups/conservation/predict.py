"""Infer non-starts only from a fully identified set of eleven starters per side."""
from pathlib import Path
import sys
import json

import pandas as pd

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P.parent))
from predict import R, K, digest, save
from validate_v4 import check_freeze_v4


def conserve(frame):
    if frame.duplicated(K).any() or frame.code.isna().any() or not frame.was_home.isin([True, False]).all():
        raise ValueError('Incomplete unique canonical code/side identity')
    if not frame.predicted_starts.dropna().isin([0, 1]).all():
        raise ValueError('Invalid explicit start value')
    out, proofs = [], []
    for (season, fixture), group in frame.groupby(['season', 'fixture'], sort=True):
        group = group.copy()
        starters = group[group.predicted_starts.eq(1)]
        counts = starters.groupby('was_home').code.nunique()
        complete = set(counts.index) == {True, False} and counts.eq(11).all()
        if (counts > 11).any():
            raise ValueError('Too many explicit starters on a club side')
        proofs.append(dict(season=season, fixture=fixture, complete=bool(complete),
            home_starter_codes=';'.join(map(str, sorted(starters.loc[starters.was_home, 'code']))),
            away_starter_codes=';'.join(map(str, sorted(starters.loc[~starters.was_home, 'code']))),
            rows=len(group), inferred_zero_rows=int(group.predicted_starts.isna().sum()) if complete else 0))
        group['complete_start_inventory'] = bool(complete)
        group['conservation_zero'] = complete & group.predicted_starts.isna()
        group['completed_starts'] = group.predicted_starts
        group.loc[group.conservation_zero, 'completed_starts'] = 0
        out.append(group)
    return pd.concat(out).sort_values(K).reset_index(drop=True), pd.DataFrame(proofs)


def main():
    frozen = check_freeze_v4()
    qualification = json.loads((P.parent / 'validation_summary_v4.json').read_text())
    if not qualification['qualified'] or qualification['prediction_sha256'] != frozen['prediction_sha256']:
        raise ValueError('Explicit source start qualification not passed')
    protocol = dict(version='full_identified_start_inventory_conservation_v5',
        design='Logical exhaustive-lineup inference, followed by whole-population regression. Earlier controls have been seen and share Opta ancestry; no independent holdout claimed.',
        rule='Only if eleven distinct stable canonical player codes are explicit qualified starters on EACH fixture club side, every other distinct canonical identity cannot be a starter. Infer starts=0 only for previously missing source roles. Missing/incomplete elevens preserve missing values; never infer from minutes, provider timing, an empty roster or a positive residual.',
        gates=json.loads((P.parent / 'protocol_v4.json').read_text())['gates'],
        extra_gates=dict(all_historical_fixtures_with_two_complete_elevens=2660,
            maximum_compatible_native_start_disagreements=0, maximum_existing_qualified_value_changes=0,
            maximum_direct_primary_disagreements=0),
        comparison='All four seasons 2022/23..2025/26. For the documented early-2022 incompatible block, use the separate official primary full starting sets as truth; missing original primary squad membership is a zero ONLY because primary has two fully identified complete elevens.',
        scope='Starts only. No other event count, point/BPS/bonus/defcon label, or historical feature publication time is qualified.')
    encoded = json.dumps(protocol, indent=2) + '\n'
    path = P / 'protocol.json'
    if path.exists() and path.read_text() != encoded:
        raise ValueError('Conservation protocol changed')
    path.write_text(encoded)
    inputs = [P.parent / 'predictions_v4.csv.xz', P.parent / 'freeze_v4.json',
        P.parent / 'validation_summary_v4.json', path,
        P.parent.parent / 'scoring/results/historical_inventory.csv.xz',
        P.parent / 'starts_qualified.csv.xz', P.parent / 'application_manifest.json',
        P.parent / 'primary_reference/explicit_lineups.csv.xz']
    population = pd.read_csv(inputs[4], usecols=K + ['was_home'])
    predictions = pd.read_csv(inputs[0], usecols=K + ['predicted_starts'])
    completed, proofs = conserve(predictions.merge(population, on=K, validate='one_to_one'))
    save(completed, P / 'predictions.csv.xz')
    save(proofs, P / 'complete_start_inventories.csv')
    lock = dict(outcomes_read=False, design=protocol['design'],
        input_sha256={str(x.relative_to(R)): digest(x) for x in inputs},
        prediction_code_sha256=digest(Path(__file__)), prediction_sha256=digest(P / 'predictions.csv.xz'),
        proof_sha256=digest(P / 'complete_start_inventories.csv'))
    path = P / 'freeze.json'
    encoded = json.dumps(lock, indent=2) + '\n'
    if path.exists() and path.read_text() != encoded:
        raise ValueError('Conservation freeze changed')
    path.write_text(encoded)
    print(dict(predictions=len(completed), inferred_zeros=int(completed.conservation_zero.sum()),
        complete_fixtures=int(proofs.complete.sum())))


if __name__ == '__main__':
    main()
