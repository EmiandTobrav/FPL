"""Compare only the already-frozen lineup predictions with FPL starts."""
from pathlib import Path
import json

import pandas as pd

from predict import P, R, K, digest, save


def check_freeze():
    lock = json.loads((P / 'freeze_v2.json').read_text())
    for name, sha in lock['input_sha256'].items():
        if digest(R / name) != sha:
            raise ValueError(f'Frozen lineup input changed: {name}')
    for path, sha in [(P / 'predict.py', lock['prediction_code_sha256']),
                      (P / 'predictions.csv.xz', lock['prediction_sha256']),
                      (P / 'fixture_identity.csv', lock['fixture_identity_sha256'])]:
        if digest(path) != sha:
            raise ValueError('Frozen lineup code/prediction changed')
    if lock['outcomes_read']:
        raise ValueError('Control outcomes were used during prediction')
    return lock


def main():
    check_freeze()
    protocol = json.loads((P / 'protocol.json').read_text())
    predictions = pd.read_csv(P / 'predictions.csv.xz', low_memory=False)
    original = pd.read_csv(P.parent / 'scoring/results/historical_inventory.csv.xz',
                          usecols=K + ['starts'], low_memory=False)
    comparisons = predictions.merge(original, on=K, validate='one_to_one')
    controls = comparisons[comparisons.season.ge('2022-23') & comparisons.starts.notna() & comparisons.predicted_starts.notna()].copy()
    controls['agrees'] = controls.predicted_starts.eq(controls.starts)
    gates = protocol['gates']
    groups = []
    for season, rows in controls.groupby('season', sort=True):
        fixture_count = rows.fixture.nunique()
        positives, negatives = int(rows.starts.eq(1).sum()), int(rows.starts.eq(0).sum())
        errors = int((~rows.agrees).sum())
        groups.append(dict(season=season, rows=len(rows), fixtures=fixture_count,
            positives=positives, negatives=negatives, disagreements=errors,
            passed=fixture_count >= gates['minimum_control_fixtures_per_season'] and
                positives >= gates['minimum_positive_per_season'] and
                negatives >= gates['minimum_negative_per_season'] and
                errors <= gates['maximum_disagreements']))
    passed = len(groups) == 4 and all(group['passed'] for group in groups)
    save(controls[K + ['status', 'match_id', 'player_id', 'predicted_starts', 'starts', 'agrees']], P / 'control_comparisons.csv.xz')
    save(controls[~controls.agrees], P / 'control_disagreements.csv')
    save(pd.DataFrame(groups), P / 'control_summary.csv')
    summary = dict(protocol_version=protocol['version'], qualified=passed,
        rows=len(controls), fixture_count=controls[['season', 'fixture']].drop_duplicates().shape[0],
        disagreements=int((~controls.agrees).sum()), groups=groups,
        evidence_type='Full-population mapping regression against already observed FPL with shared Opta ancestry, not independent holdout',
        frozen_prediction_sha256=digest(P / 'predictions.csv.xz'),
        validation_code_sha256=digest(Path(__file__)))
    (P / 'validation_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
