"""Check frozen source compatibility and fill only missing goal-line inputs."""
from pathlib import Path
import gzip
import hashlib
import json
import lzma
import pandas as pd
from predict import P, B, R, K, digest

OUT = P / 'results'

def save(frame, name):
    raw = frame.to_csv(index=False).encode()
    if name.endswith('.xz'):
        raw = lzma.compress(raw, preset=6)
    elif name.endswith('.gz'):
        raw = gzip.compress(raw, mtime=0)
    (OUT / name).write_bytes(raw)

def main():
    OUT.mkdir(exist_ok=True)
    for name, expected in json.loads((P / 'prediction_freeze.json').read_text())['files'].items():
        assert digest(R / name) == expected, name
    parent = json.loads((P / 'inputs/parent_CURRENT.json').read_text())
    parent_path = B / parent['requirements']
    assert digest(parent_path) == parent['requirements_sha256']
    before = pd.read_csv(parent_path, low_memory=False)
    pred = pd.read_csv(P / 'predictions.csv.gz')
    closed = before[before.field.eq('goal_line_clearances') & ~before.is_open]
    controls = closed[K + ['value']].merge(pred, on=K, suffixes=('_approved', '_event'), validate='one_to_one')
    controls['agrees'] = controls.value_approved.eq(controls.value_event)
    save(controls, 'closed_controls.csv.gz')
    explicit = pred[pred.explicit_archive_goal_line.notna()].copy()
    explicit['agrees'] = explicit.value.eq(explicit.explicit_archive_goal_line)
    save(explicit, 'explicit_source_controls.csv')
    positive = explicit[explicit.explicit_archive_goal_line.gt(0)].groupby('season').size().to_dict()
    required = [f'{y}-{str(y+1)[2:]}' for y in range(2019, 2025)]
    gates = json.loads((P / 'protocol.json').read_text())['gate']
    mismatch_controls = controls[controls.minute_difference.abs().eq(1)]
    mismatch_explicit = explicit[explicit.minute_difference.abs().eq(1)]
    mismatch_positive = mismatch_explicit[mismatch_explicit.explicit_archive_goal_line.gt(0)]
    mismatch_by_season = mismatch_controls.groupby('season').size().to_dict()
    qualified = (len(controls) >= gates['minimum_closed_controls'] and controls.agrees.all() and explicit.agrees.all()
                 and all(positive.get(year, 0) >= gates['minimum_explicit_positive_each_2019_to_2024'] for year in required)
                 and positive.get('2025-26', 0) >= gates['minimum_explicit_positive_2025']
                 and len(mismatch_controls) >= gates['minimum_closed_one_minute_controls']
                 and len(mismatch_positive) >= gates['minimum_positive_one_minute_controls'])
    applied_seasons = sorted(year for year in mismatch_by_season
        if mismatch_by_season[year] >= gates['minimum_closed_one_minute_controls_each_applied_season'])
    validation = dict(qualified=bool(qualified), closed_controls=len(controls),
        closed_zero_controls=int(controls.value_approved.eq(0).sum()),
        closed_control_errors=int((~controls.agrees).sum()), explicit_source_controls=len(explicit),
        explicit_source_errors=int((~explicit.agrees).sum()), positive_source_controls_by_season=positive,
        closed_controls_by_season=controls.groupby('season').size().to_dict(),
        overlapping_source_and_closed_control_keys=len(explicit[K].merge(controls[K], on=K, validate='one_to_one')),
        one_minute_closed_controls=len(mismatch_controls),
        one_minute_closed_control_errors=int((~mismatch_controls.agrees).sum()),
        one_minute_explicit_positive_controls=len(mismatch_positive),
        one_minute_explicit_control_errors=int((~mismatch_explicit.agrees).sum()),
        one_minute_closed_controls_by_season=mismatch_by_season,
        qualified_application_seasons=applied_seasons,
        limits='Shared Opta lineage; previously observed development/source controls and closed-ledger regression. '
               'Not independent holdout, not native FPL goal-line observations, not scoring qualification.')
    (OUT / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
    if not qualified:
        (OUT / 'findings.json').write_text(json.dumps(dict(new_fields=0, validation=validation), indent=2) + '\n')
        print(json.dumps(validation, indent=2))
        return
    pending = before[before.is_open & before.status.eq('missing_data') & before.field.eq('goal_line_clearances')]
    eligible = pred[pred.minute_difference.abs().eq(1) & pred.season.isin(applied_seasons)]
    overlay = pending[K + ['field']].merge(eligible, on=K, validate='one_to_one')
    save(overlay, 'overlay.csv.gz')
    req = before.copy()
    values = overlay.set_index(K)
    keys = pd.MultiIndex.from_frame(req[K])
    mask = (req.field.eq('goal_line_clearances') & req.is_open & req.status.eq('missing_data')
            & keys.isin(values.index))
    assert int(mask.sum()) == len(overlay)
    subkeys = pd.MultiIndex.from_frame(req.loc[mask, K])
    req.loc[mask, 'value'] = values.value.reindex(subkeys).to_numpy()
    req.loc[mask, 'status'] = 'documented_source_reconciliation'
    req.loc[mask, 'provenance'] = 'followup_2026_10_08/goal_line_identity_v2/results/overlay.csv.gz + predictions.csv.gz + team_gates.csv + identity_scope.csv.gz'
    req.loc[mask, 'quality_status'] = 'complete_last_line_block_inventory_with_cross_match_identity_and_one_minute_duration_difference;collective_quality_pending'
    req.loc[mask, 'needs_external_quality_review'] = True
    req.loc[mask, 'is_open'] = False
    req.loc[mask, 'is_zero'] = req.loc[mask, 'value'].eq(0)
    pd.testing.assert_frame_equal(req.loc[~mask], before.loc[~mask])
    unchanged = [c for c in before if c not in ['value', 'status', 'provenance', 'quality_status',
                 'needs_external_quality_review', 'is_open', 'is_zero']]
    pd.testing.assert_frame_equal(req[unchanged], before[unchanged])
    save(req, 'requirements.csv.xz')
    pending = req[req.is_open]
    save(pending, 'remaining_fields.csv.xz')
    fields = req.groupby('field').agg(required=('field', 'size'), open_cells=('is_open', 'sum'),
                                     external_quality_cells=('needs_external_quality_review', 'sum')).reset_index()
    save(fields, 'field_summary.csv')
    pm = req.groupby(K).agg(open_fields=('is_open', 'sum'), quality_fields=('needs_external_quality_review', 'sum')).reset_index()
    pm['inputs_available'] = pm.open_fields.eq(0)
    pm['scoring_qualified'] = False
    save(pm, 'player_match_readiness.csv.xz')
    matches = pm.groupby(K[:2]).agg(player_matches=('code', 'size'), open_fields=('open_fields', 'sum'),
                                   quality_fields=('quality_fields', 'sum')).reset_index()
    matches['inputs_available'] = matches.open_fields.eq(0)
    matches['bonus_ready'] = False
    save(matches, 'match_readiness.csv')
    old_pm = pd.read_csv(B / parent['player_match_readiness'])
    old_matches = pd.read_csv(B / parent['match_readiness'])
    new_pm = pm[pm.inputs_available].merge(old_pm[K + ['inputs_available']], on=K,
                                          validate='one_to_one', suffixes=('', '_old'))
    new_matches = matches[matches.inputs_available].merge(old_matches[K[:2] + ['inputs_available']],
                         on=K[:2], validate='one_to_one', suffixes=('', '_old'))
    summary = dict(old_open_fields=int(before.is_open.sum()), new_fields=len(overlay),
        zero_values=int(overlay.value.eq(0).sum()), positive_values=int(overlay.value.gt(0).sum()),
        open_fields=int(req.is_open.sum()), unique_affected_player_matches=len(pending[K].drop_duplicates()),
        complete_player_matches=int(pm.inputs_available.sum()), complete_matches=int(matches.inputs_available.sum()),
        new_complete_player_matches=int((~new_pm.inputs_available_old).sum()),
        new_complete_matches=int((~new_matches.inputs_available_old).sum()),
        remaining_goal_line_clearances=int((pending.field == 'goal_line_clearances').sum()),
        new_fields_by_season=overlay.groupby('season').size().to_dict(),
        new_fields_by_minute_difference={str(int(k)):int(v) for k,v in overlay.groupby('minute_difference').size().items()},
        unchanged_ledger_rows=len(before) - len(overlay), raw_fpl_preserved=True,
        old_scoring_labels_preserved=True, scoring_qualified=False, validation=validation)
    assert summary['old_open_fields'] - summary['open_fields'] == summary['new_fields']
    (OUT / 'findings.json').write_text(json.dumps(summary, indent=2) + '\n')
    outputs = sorted(x for x in OUT.iterdir() if x.name != 'manifest.json')
    (OUT / 'manifest.json').write_text(json.dumps({x.name: digest(x) for x in outputs}, indent=2) + '\n')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
