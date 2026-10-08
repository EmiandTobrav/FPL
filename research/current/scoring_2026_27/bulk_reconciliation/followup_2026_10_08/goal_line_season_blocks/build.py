"""Validate exact zero-team proofs and reuse the published ledger-preserving overlay."""
from pathlib import Path
import gzip
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
    assert digest(B / parent['requirements']) == parent['requirements_sha256']
    before = pd.read_csv(B / parent['requirements'], low_memory=False)
    pred = pd.read_csv(P / 'predictions.csv.gz')
    closed = before[before.field.eq('goal_line_clearances') & ~before.is_open]
    controls = closed[K + ['value']].merge(pred, on=K, suffixes=('_approved', '_event'), validate='one_to_one')
    controls['agrees'] = controls.value_approved.eq(controls.value_event)
    save(controls, 'closed_controls.csv.gz')
    source = pd.read_csv(R / 'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz', low_memory=False)
    positive = source[source.clearanceOffLine.gt(0)][K + ['clearanceOffLine']]
    conflicts = positive.merge(pred, on=K, validate='one_to_one')
    save(conflicts, 'explicit_positive_conflicts.csv')
    by_season = controls.groupby('season').agg(controls=('agrees', 'size'), errors=('agrees', lambda x: int((~x).sum()))).reset_index()
    save(by_season, 'controls_by_season.csv')
    qualified = len(controls) >= 1000 and controls.agrees.all() and conflicts.empty
    validation = dict(qualified=bool(qualified), closed_controls=len(controls),
        closed_control_errors=int((~controls.agrees).sum()), explicit_positive_conflicts=len(conflicts),
        closed_controls_by_season=controls.groupby('season').size().to_dict(),
        exact_season_team_groups=int(pd.read_csv(P / 'season_conservation.csv').qualified.sum()),
        zero_team_matches=len(pd.read_csv(P / 'team_gates.csv').query('block_total == 0')),
        limits='Exact primary season/match conservation and reused closed-source regression; '
               'not independent holdout, native FPL goal-line observations, or scoring qualification.')
    (OUT / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
    if not qualified:
        (OUT / 'findings.json').write_text(json.dumps(dict(new_fields=0, validation=validation), indent=2) + '\n')
        print(json.dumps(validation, indent=2))
        return
    pending = before[before.is_open & before.status.eq('missing_data') & before.field.eq('goal_line_clearances')]
    overlay = pending[K + ['field']].merge(pred, on=K, validate='one_to_one')
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
    req.loc[mask, 'provenance'] = 'followup_2026_10_08/goal_line_season_blocks/results/overlay.csv.gz + season_conservation.csv + team_gates.csv'
    req.loc[mask, 'quality_status'] = 'explicit_primary_whole_team_zero_blocks;independent_of_player_minute_bookkeeping;collective_quality_pending'
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
        unchanged_ledger_rows=len(before) - len(overlay), raw_fpl_preserved=True,
        old_scoring_labels_preserved=True, scoring_qualified=False, validation=validation)
    assert summary['old_open_fields'] - summary['open_fields'] == summary['new_fields']
    (OUT / 'findings.json').write_text(json.dumps(summary, indent=2) + '\n')
    outputs = sorted(x for x in OUT.iterdir() if x.name != 'manifest.json')
    (OUT / 'manifest.json').write_text(json.dumps({x.name: digest(x) for x in outputs}, indent=2) + '\n')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
