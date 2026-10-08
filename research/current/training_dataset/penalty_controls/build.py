"""Apply qualified positive penalty awards and recompute complete totals only."""
from pathlib import Path
import gzip
import hashlib
import json
import lzma
import sys
import pandas as pd
from plan import P, R, S
from validate import validate

K = ['season', 'fixture', 'code']
sys.path.insert(0, str(S / 'assist_intentional_pass'))
from baseline.build import aggregate

def save(df, name):
    payload = df.to_csv(index=False).encode()
    if name.endswith('.gz'):
        payload = gzip.compress(payload, mtime=0)
        payload = payload[:9] + bytes([255]) + payload[10:]
    elif name.endswith('.xz'):
        payload = lzma.compress(payload)
    (P / 'results' / name).write_bytes(payload)

def main():
    validation = validate()
    if validation['qualified_kinds'] != ['ordinary_foul_penalty']:
        raise ValueError('Positive penalty route did not pass its frozen gate')
    (P / 'results').mkdir(exist_ok=True)
    goals = pd.read_csv(S / 'assist_touch_bounds/results/goal_decisions.csv.gz')
    pred = pd.read_csv(S / 'penalty_foul_recovery/predictions.csv.gz')
    people = pd.read_csv(S / 'assist_intentional_pass/inputs/participants.csv.gz')
    baseline = pd.read_csv(S / 'assist_intentional_pass/baseline/fpl_baseline.csv.gz')
    people = people.merge(baseline[K + ['assists']], on=K, validate='one_to_one')
    cover = pd.read_csv(S / 'assist_intentional_pass/results/team_coverage.csv').set_index(
        ['match_id', 'team_id']).coverage_ok.to_dict()
    additions = []
    for r in pred[pred.season.ne('2025-26') & pred.kind.eq('ordinary_foul_penalty')].itertuples():
        mask = goals.match_id.eq(r.match_id) & goals.event_id.eq(r.event_id)
        if mask.sum() != 1:
            raise ValueError('Prediction lacks unique goal identity')
        if goals.loc[mask, 'status'].iloc[0] != 'unresolved':
            continue
        if not cover.get((r.match_id, r.scoring_team_id), False):
            continue
        recipient = people[people.match_id.eq(r.match_id) & people.team_id.eq(r.scoring_team_id)
                           & people.player_id.eq(r.recipient_player_id)]
        if len(recipient) != 1:
            continue
        goals.loc[mask, ['status', 'recipient_player_id', 'reason', 'route', 'missing', 'evidence_scope']] = [
            'awarded', r.recipient_player_id, 'paired_ordinary_foul_direct_penalty',
            'ordinary_foul_penalty_isolated_controls_v1', '',
            '30_recipient_isolated_temporal_controls_shared_opta_review']
        additions.append(dict(season=r.season, fixture=r.fixture, match_id=r.match_id,
                              event_id=r.event_id, recipient_player_id=r.recipient_player_id,
                              code=int(recipient.code.iloc[0]), foul_event_id=r.foul_event_id,
                              committed_event_id=r.committed_event_id))
    save(pd.DataFrame(additions, columns=['season', 'fixture', 'match_id', 'event_id',
                                        'recipient_player_id', 'code', 'foul_event_id',
                                        'committed_event_id']), 'new_goal_awards.csv')
    if not additions:
        # Do not duplicate an unchanged 775k-row ledger. This pilot strengthens
        # an existing route but supplies no new values to the remaining queue.
        current = json.loads((S.parent / 'CURRENT.json').read_text())
        summary = dict(new_goal_awards=0, new_assist_fields=0,
                       open_fields=current['open_fields'],
                       unique_affected_player_matches=current['unique_affected_player_matches'],
                       complete_player_matches=current['complete_player_matches'],
                       complete_matches=current['complete_matches'],
                       historical_ledger_unchanged=True, raw_fpl_preserved=True,
                       self_won_route_applied=False, scoring_qualified=False,
                       reason='Every eligible frozen historical positive penalty prediction is already a protected goal award.',
                       validation=validation)
        (P / 'results/summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary, indent=2))
        return
    old_goals = pd.read_csv(S / 'assist_touch_bounds/results/goal_decisions.csv.gz')
    protected = old_goals.status.ne('unresolved')
    pd.testing.assert_frame_equal(old_goals.loc[protected], goals.loc[protected])
    allowed_changes = {'status', 'recipient_player_id', 'reason', 'route', 'missing', 'evidence_scope'}
    pd.testing.assert_frame_equal(old_goals[[c for c in goals if c not in allowed_changes]],
                                  goals[[c for c in goals if c not in allowed_changes]])
    save(goals, 'goal_decisions.csv.gz')
    denied = pd.read_csv(S / 'assist_touch_bounds/results/candidate_exclusions.csv.gz')
    denials = {(int(r.event_id), r.player_id) for r in denied.itertuples()}
    denials.update((int(c['goal_event_id']), c['candidate_player_id']) for c in
                   json.loads((S / 'assist_intentional_pass/inputs/official_cases.json').read_text())
                   if not c['expected_award'])
    gm = {key: group.to_dict('records') for key, group in goals.groupby(['match_id', 'scoring_team_id'])}
    totals = []
    for r in people.to_dict('records'):
        key = (r['match_id'], r['team_id'])
        out = dict(value=r['assists'], reason='authoritative_fpl') if r['season'] == '2025-26' else aggregate(
            gm.get(key, []), r['player_id'], r['own_team_goals'], cover.get(key, False), denials)
        totals.append({**{k: r[k] for k in K + ['name', 'match_id', 'team_id', 'player_id']},
                       'historical_fpl_assists': r['assists'], **out})
    totals = pd.DataFrame(totals)
    old_totals = pd.read_csv(S / 'assist_touch_bounds/results/player_match_totals.csv.gz')
    known = old_totals.dropna(subset=['value'])[K + ['value']].merge(
        totals[K + ['value']], on=K, validate='one_to_one', suffixes=('_old', '_new'))
    if not known.value_old.eq(known.value_new).all():
        raise ValueError('Previously approved assist total changed')
    save(totals, 'player_match_totals.csv.gz')
    before = pd.read_csv(S / 'bulk_batch3/results/requirements.csv.xz', low_memory=False)
    layer = before[before.is_open & before.field.eq('assists_2026_27')][K + ['field']].merge(
        totals, on=K, validate='one_to_one').dropna(subset=['value'])
    save(layer, 'new_fields.csv.gz')
    out = before.copy(deep=True)
    mapping = out.reset_index(names='_row').merge(layer[K + ['field', 'value']],
        on=K + ['field'], validate='one_to_one', suffixes=('_old', ''))
    ix = mapping._row.to_numpy()
    if not mapping.is_open.all() or not mapping.value_old.isna().all():
        raise ValueError('Overlay attempts to overwrite a known value')
    out.loc[ix, 'value'] = mapping.value.to_numpy()
    out.loc[ix, 'is_zero'] = mapping.value.eq(0).to_numpy()
    out.loc[ix, 'is_open'] = False
    out.loc[ix, 'status'] = 'documented_source_reconciliation'
    out.loc[ix, 'needs_external_quality_review'] = True
    out.loc[ix, 'quality_status'] = 'qualified_ordinary_penalty_recipient_isolation_shared_opta_review'
    out.loc[ix, 'provenance'] = 'training_dataset/penalty_controls/results/player_match_totals.csv.gz + new_goal_awards.csv + validation_summary.json'
    mutable = {'value', 'is_zero', 'is_open', 'status', 'needs_external_quality_review', 'quality_status', 'provenance'}
    pd.testing.assert_frame_equal(before[[c for c in before if c not in mutable]],
                                  out[[c for c in out if c not in mutable]])
    pd.testing.assert_frame_equal(before.drop(index=ix), out.drop(index=ix))
    save(out, 'requirements.csv.xz')
    save(out[out.is_open], 'remaining_fields.csv.gz')
    players = out.groupby(K).agg(open_fields=('is_open', 'sum'),
                               external_quality_fields=('needs_external_quality_review', 'sum')).reset_index()
    matches = players.groupby(K[:2]).agg(open_fields=('open_fields', 'sum'),
                                        player_matches=('code', 'size'),
                                        affected_player_matches=('open_fields', lambda x: int(x.gt(0).sum()))).reset_index()
    save(players, 'player_match_readiness.csv.gz')
    save(matches, 'match_readiness.csv')
    save(out.groupby('field').agg(required=('field', 'size'), open_fields=('is_open', 'sum'),
                                 external_quality_fields=('needs_external_quality_review', 'sum')).reset_index(), 'field_summary.csv')
    old_players = before.groupby(K).is_open.sum()
    old_matches = old_players.groupby(level=[0, 1]).sum()
    summary = dict(new_goal_awards=len(additions), new_assist_fields=len(layer),
                   new_positive_totals=int(layer.value.gt(0).sum()), new_zero_totals=int(layer.value.eq(0).sum()),
                   open_fields=int(out.is_open.sum()), open_assist_fields=int((out.is_open & out.field.eq('assists_2026_27')).sum()),
                   unique_affected_player_matches=int(players.open_fields.gt(0).sum()),
                   complete_player_matches=int(players.open_fields.eq(0).sum()),
                   new_complete_player_matches=int(players.open_fields.eq(0).sum() - old_players.eq(0).sum()),
                   complete_matches=int(matches.open_fields.eq(0).sum()),
                   new_complete_matches=int(matches.open_fields.eq(0).sum() - old_matches.eq(0).sum()),
                   approved_assist_totals_preserved=len(known), raw_fpl_preserved=True,
                   self_won_route_applied=False, scoring_qualified=False, validation=validation)
    (P / 'results/summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
