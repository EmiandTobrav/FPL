"""Read native BPS only after the source-verified bounds have been frozen."""
from pathlib import Path
import json

import pandas as pd

from collect import check_freeze
from prepare import P, R, K, digest


def verify_fingerprints(root, fingerprints):
    for name, expected in fingerprints.items():
        if digest(root / name) != expected:
            raise ValueError('Frozen input/output changed: ' + name)


def acceptance(protocol, discriminating, clipped_violations, source_disagreements):
    gates = protocol['acceptance']
    by_season = discriminating.groupby('season').size().to_dict()
    checks = {
        'minimum_discriminating_rows': len(discriminating) >= gates['minimum_discriminating_rows'],
        'minimum_discriminating_rows_per_season': all(
            by_season.get(s,0) >= gates['minimum_discriminating_rows_per_season']
            for s in gates['required_seasons']),
        'maximum_clipped_bound_violations': clipped_violations <= gates['maximum_clipped_bound_violations'],
        'maximum_primary_explicit_disagreements': source_disagreements <= gates['maximum_primary_explicit_disagreements'],
    }
    return all(checks.values()), checks


def main():
    check_freeze()
    lock = json.loads((P / 'primary_prediction_freeze.json').read_text())
    verify_fingerprints(R, lock['input_sha256'])
    verify_fingerprints(P, lock['output_sha256'])
    for name, key in [('source_manifest.json','primary_source_manifest_sha256'),
                      ('raw_inputs.tar.gz','primary_archive_sha256'),
                      ('primary_predict.py','predictor_code_sha256'),
                      ('freeze.json','plan_freeze_sha256')]:
        if digest(P / name) != lock[key]:
            raise ValueError('Primary prediction evidence changed: ' + name)
    if lock['outcomes_read']:
        raise ValueError('Prediction freeze must precede native BPS outcomes')
    predictions = pd.read_csv(P / 'primary_predictions.csv')
    plan = pd.read_csv(P / 'plan.csv')
    comparisons = pd.read_csv(P / 'primary_comparisons.csv')
    if predictions.duplicated(K).any() or plan.duplicated(K).any():
        raise ValueError('Duplicate frozen population/prediction')
    if not set(map(tuple,predictions[K].to_numpy())).issubset(set(map(tuple,plan[K].to_numpy()))):
        raise ValueError('Predictions outside fixed population')
    # This is the first numeric read of the published BPS outcome in this study.
    native = pd.read_csv(P.parent / 'results/historical_inventory.csv.xz', usecols=K+['bps'])
    checks = predictions.merge(native, on=K, how='left', validate='one_to_one')
    if (checks.bps.isna().any() or not checks.source_verified.all()
            or (checks.bps % 1).ne(0).any()):
        raise ValueError('Invalid native BPS or unverified positive bound')
    checks['signed_bound_violated'] = checks.bps.gt(checks.primary_upper_signed)
    checks['clipped_bound_violated'] = checks.bps.gt(checks.primary_upper_clipped)
    checks['discriminating'] = checks.signed_bound_violated & ~checks.clipped_bound_violated
    disagreements = comparisons[comparisons.status.eq('disagreed')].copy()
    protocol = json.loads((P / 'protocol.json').read_text())
    qualified, gates = acceptance(protocol, checks[checks.discriminating],
                                  int(checks.clipped_bound_violated.sum()), len(disagreements))
    checks.to_csv(P / 'bps_bound_checks.csv', index=False)
    disagreements.to_csv(P / 'primary_disagreements.csv', index=False)
    eligibility = comparisons.groupby(K).status.agg(lambda s:'disagreed' if s.eq('disagreed').any()
                                                    else 'missing' if s.eq('missing').any() else 'agreed').rename('source_status').reset_index()
    eligibility = plan[K].merge(eligibility,on=K,how='left',validate='one_to_one')
    eligibility['bound_eligible'] = list(map(tuple,eligibility[K].to_numpy()))
    keys = set(map(tuple,predictions[K].to_numpy()))
    eligibility['bound_eligible'] = eligibility.bound_eligible.map(lambda k:k in keys)
    eligibility.to_csv(P / 'source_eligibility.csv',index=False)
    by_season = checks.groupby('season').agg(verified_rows=('bps','size'),
        signed_bound_violations=('signed_bound_violated','sum'),
        clipped_bound_violations=('clipped_bound_violated','sum'),discriminating_rows=('discriminating','sum'))
    by_season.to_csv(P / 'season_summary.csv')
    summary = dict(version=protocol['version'], status='qualified_component_rule' if qualified else 'not_qualified',
        fixed_controls=len(plan), primary_responses=len(plan), source_verified_bounds=len(checks),
        source_missing_controls=int(eligibility.source_status.eq('missing').sum()),
        source_disagreed_controls=int(eligibility.source_status.eq('disagreed').sum()),
        primary_explicit_disagreements=len(disagreements),
        signed_bound_violations=int(checks.signed_bound_violated.sum()),
        clipped_bound_violations=int(checks.clipped_bound_violated.sum()),
        discriminating_rows=int(checks.discriminating.sum()),
        discriminating_rows_by_season=checks[checks.discriminating].groupby('season').size().to_dict(),
        acceptance_gates=gates, legacy_clipping_qualified=qualified,
        raw_signed_counts_preserved=True, unknown_negative_counts_kept_missing=True,
        source_agreement_and_rule_qualification_are_separate=True,
        final_bps_bonus_or_points_qualified=False, qualified_historical_fixtures=0,
        new_ledger_inputs=0, training_labels_enabled=False,
        primary_evidence_warning='Current primary/archived source share Opta ancestry and may have version differences. Dated copied rule text is corroboration only. Bound diagnostics do not reconstruct complete BPS.',
        failed_control_policy='No gate relaxed and no post-outcome exclusions. Missing controls remain recorded. Explicit disagreements keep the global source gate failed.',
        evidence_sha256={'protocol.json':digest(P/'protocol.json'),
            'freeze.json':digest(P/'freeze.json'),
            'primary_prediction_freeze.json':digest(P/'primary_prediction_freeze.json')},
        validator_code_sha256=digest(Path(__file__)),
        output_sha256={name:digest(P/name) for name in ['bps_bound_checks.csv','primary_disagreements.csv','source_eligibility.csv','season_summary.csv']})
    (P / 'validation_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print({k:summary[k] for k in ['status','source_verified_bounds','primary_explicit_disagreements',
        'signed_bound_violations','clipped_bound_violations','discriminating_rows',
        'discriminating_rows_by_season','acceptance_gates']})


if __name__ == '__main__':
    main()
