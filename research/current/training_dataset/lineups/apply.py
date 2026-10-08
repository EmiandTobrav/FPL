"""Build a separate qualified starts view after compatible reference gates pass."""
from pathlib import Path
import json

import pandas as pd

from predict import P, K, digest, save
from validate import check_freeze
from validate_v4 import check_freeze_v4


def require_qualified(summary, prediction_sha):
    if not summary['qualified'] or summary['prediction_sha256'] != prediction_sha:
        raise ValueError('Starts qualification not passed for frozen predictions')


def qualified_view(original, predictions, reference):
    frame = original.merge(predictions[K + ['predicted_starts', 'status', 'match_id', 'player_id',
        'primary_source_file', 'primary_source_sha256']], on=K, validate='one_to_one')
    frame = frame.merge(reference[K + ['reference_starts', 'source_file', 'source_sha256']], on=K,
        how='left', validate='one_to_one')
    structural = frame.season.eq('2022-23') & frame.fixture_event.lt(16)
    frame['starts_original'] = frame.starts
    frame['starts_qualified'] = frame.starts
    frame['starts_quality'] = frame.starts.notna().map({True: 'native_compatible_fpl', False: 'missing'})
    # All early structural defaults are incompatible. Absence in a lineup is NOT zero.
    frame.loc[structural, 'starts_qualified'] = float('nan')
    frame.loc[structural, 'starts_quality'] = 'structural_default_unresolved'
    primary = structural & frame.reference_starts.notna()
    frame.loc[primary, 'starts_qualified'] = frame.loc[primary, 'reference_starts']
    frame.loc[primary, 'starts_quality'] = 'explicit_primary_structural_repair'
    older = frame.season.lt('2022-23') & frame.starts.isna() & frame.predicted_starts.notna()
    frame.loc[older, 'starts_qualified'] = frame.loc[older, 'predicted_starts']
    frame.loc[older, 'starts_quality'] = 'qualified_explicit_lineup'
    # Native compatible values remain byte-for-value unchanged.
    compatible = frame.starts.notna() & ~structural
    if not frame.loc[compatible, 'starts_qualified'].eq(frame.loc[compatible, 'starts']).all():
        raise ValueError('Compatible original FPL starts changed')
    if not frame.starts_qualified.dropna().isin([0, 1]).all():
        raise ValueError('Invalid per-match start count')
    frame['starts_value_qualified'] = frame.starts_qualified.notna()
    frame['source_start_prediction'] = frame.predicted_starts
    return frame


def main():
    check_freeze()
    frozen = check_freeze_v4()
    refdir = P / 'primary_reference'
    qualification = json.loads((P / 'validation_summary_v4.json').read_text())
    require_qualified(qualification, frozen['prediction_sha256'])
    if digest(refdir / 'explicit_lineups.csv.xz') != qualification['primary_reference_sha256'] or digest(refdir / 'validation_summary.json') != qualification['reference_validation_sha256'] or digest(P / 'validate_v4.py') != qualification['validation_code_sha256'] or digest(P / 'freeze_v4.json') != qualification['freeze_sha256']:
        raise ValueError('Qualified starts reference/validation changed')
    # Explicitly prove every archive match has two complete elevens. This covers
    # the absent-slot-group edge case separately from frozen v2 classification.
    lineup = pd.read_csv(P / 'opta_lineups.csv.xz', keep_default_na=False)
    lineup['slot'] = pd.to_numeric(lineup.formation_place, errors='coerce')
    valid = lineup.slot.between(1, 11) & lineup.slot.eq(lineup.slot.round())
    starts = lineup[valid]
    pairs = starts.groupby(['match_id', 'team_position']).slot.agg(lambda x: len(x) == 11 and set(x) == set(range(1, 12)))
    sides = starts.groupby('match_id').team_position.agg(lambda x: set(x) == {'home', 'away'})
    if not pairs.all() or not sides.all() or len(sides) != lineup.match_id.nunique():
        raise ValueError('Archive contains incomplete exact starting slot inventory')
    inventory = P.parent / 'scoring/results/historical_inventory.csv.xz'
    original = pd.read_csv(inventory, usecols=K + ['fixture_event', 'minutes', 'starts'], low_memory=False)
    predictions = pd.read_csv(P / 'predictions_v4.csv.xz', low_memory=False)
    reference = pd.read_csv(refdir / 'explicit_lineups.csv.xz', low_memory=False)
    frame = qualified_view(original, predictions, reference)
    starter_counts = frame.groupby(['season', 'fixture']).starts_qualified.sum(min_count=1)
    if len(starter_counts) != 2660 or not starter_counts.eq(22).all():
        raise ValueError('Canonical fixture does not have exactly twenty-two qualified starters')
    save(frame, P / 'starts_qualified.csv.xz')
    coverage = []
    for season, group in frame.groupby('season', sort=True):
        active = group[group.minutes.gt(0)]
        fixture_status = active.groupby('fixture').starts_value_qualified.all()
        coverage.append(dict(season=season, rows=len(group), active_rows=len(active),
            qualified_rows=int(group.starts_value_qualified.sum()),
            qualified_active_rows=int(active.starts_value_qualified.sum()),
            missing_active_rows=int((~active.starts_value_qualified).sum()),
            source_filled_rows=int(group.starts_quality.eq('qualified_explicit_lineup').sum()),
            primary_repaired_rows=int(group.starts_quality.eq('explicit_primary_structural_repair').sum()),
            unqualified_structural_rows=int(group.starts_quality.eq('structural_default_unresolved').sum()),
            complete_active_fixtures=int(fixture_status.sum()), fixtures=len(fixture_status)))
    save(pd.DataFrame(coverage), P / 'starts_coverage.csv')
    save(frame[frame.minutes.gt(0) & ~frame.starts_value_qualified], P / 'starts_active_gaps.csv')
    manifest = dict(status='qualified_starts_partial_coverage', historical_scoring_qualified=False,
        training_dataset_ready=False, rows=len(frame), qualified_rows=int(frame.starts_value_qualified.sum()),
        compatible_values_preserved=True, full_archive_inventory_verified=True,
        verified_twenty_two_starters_per_fixture=2660,
        output_sha256={name: digest(P / name) for name in ['starts_qualified.csv.xz', 'starts_coverage.csv', 'starts_active_gaps.csv']},
        input_sha256=dict(inventory=digest(inventory), prediction=frozen['prediction_sha256'],
            qualification=digest(P / 'validation_summary_v4.json'), reference=qualification['primary_reference_sha256']),
        application_code_sha256=digest(Path(__file__)),
        limitations='Starts alone, with unresolved absent identities remaining nullable. Shared Opta ancestry, post-diagnostic reference repair. No points/BPS/bonus/defcon or xG labels qualified here.')
    (P / 'application_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(coverage, indent=2))


if __name__ == '__main__':
    main()
