"""Compare only after checking the frozen, outcome-blind isolation plan."""
from pathlib import Path
import hashlib
import json
import pandas as pd
from plan import P, R, S

def validate():
    freeze = json.loads((P / 'freeze.json').read_text())
    for name, expected in freeze['inputs'].items():
        if hashlib.sha256((R / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Frozen input changed: {name}')
    baseline_path = S / 'assist_intentional_pass/baseline/fpl_baseline.csv.gz'
    lock = dict(validation_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                baseline_sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
                plan_freeze_sha256=hashlib.sha256((P / 'freeze.json').read_bytes()).hexdigest())
    path = P / 'validation_lock.json'
    if path.exists() and json.loads(path.read_text()) != lock:
        raise ValueError('Validation inputs changed after outcome comparison')
    path.write_text(json.dumps(lock, indent=2) + '\n')
    plan = pd.read_csv(P / 'plan.csv')
    baseline = pd.read_csv(baseline_path)
    result = plan.merge(baseline[['season', 'fixture', 'code', 'assists']],
                        on=['season', 'fixture', 'code'], validate='one_to_one')
    if len(result) != len(plan) or result.assists.isna().any():
        raise ValueError('FPL comparison coverage incomplete')
    result['isolated_fpl_contribution'] = result.assists - result.other_goal_contributions
    result['correct'] = result.isolated_fpl_contribution.eq(result.predicted_contribution)
    result.to_csv(P / 'comparisons.csv', index=False)
    pred = pd.read_csv(S / 'penalty_foul_recovery/predictions.csv.gz').fillna({'recipient_player_id': ''})
    pred = pred[pred.kind.eq('ordinary_foul_penalty')]
    goals = pd.read_csv(S / 'assist_touch_bounds/results/goal_decisions.csv.gz').fillna({'recipient_player_id': ''})
    merged = pred.merge(goals[['match_id', 'event_id', 'status', 'recipient_player_id']],
                        on=['match_id', 'event_id'], suffixes=('', '_old'), validate='one_to_one')
    conflicts = merged[merged.status_old.ne('unresolved') &
                       (~merged.status.eq(merged.status_old) |
                        ~merged.recipient_player_id.eq(merged.recipient_player_id_old))]
    conflicts.to_csv(P / 'protected_conflicts.csv', index=False)
    denied = pd.read_csv(S / 'assist_touch_bounds/results/candidate_exclusions.csv.gz')
    denials = {(int(r.event_id), r.player_id) for r in denied.itertuples()}
    denials.update((int(c['goal_event_id']), c['candidate_player_id']) for c in
                   json.loads((S / 'assist_intentional_pass/inputs/official_cases.json').read_text())
                   if not c['expected_award'])
    bad_denials = [dict(match_id=r.match_id, event_id=r.event_id, recipient_player_id=r.recipient_player_id)
                   for r in pred.itertuples() if (int(r.event_id), r.recipient_player_id) in denials]
    pd.DataFrame(bad_denials, columns=['match_id', 'event_id', 'recipient_player_id']).to_csv(
        P / 'denial_conflicts.csv', index=False)
    old_comparisons = pd.read_csv(S / 'penalty_foul_recovery/validation_comparisons.csv')
    old_validation = json.loads((S / 'penalty_foul_recovery/validation_summary.json').read_text())
    old_check = len(old_comparisons) == 6 and old_comparisons.correct.all() and old_validation['errors'] == 0
    # These previously inspected outcomes are explicit reused controls, not new holdout.
    qualified = (len(result) >= 20 and result.fixture.nunique() >= 20 and result.correct.all()
                 and conflicts.empty and not bad_denials and old_check)
    summary = dict(isolated_recipient_comparisons=len(result), distinct_fixtures=int(result.fixture.nunique()),
                   one_goal_comparisons=int(result.other_goals.eq(0).sum()),
                   multi_goal_isolated_comparisons=int(result.other_goals.gt(0).sum()),
                   residual_errors=int((~result.correct).sum()), protected_conflicts=len(conflicts),
                   denial_conflicts=len(bad_denials), old_six_vector_controls_still_pass=bool(old_check),
                   qualified_kinds=['ordinary_foul_penalty'] if qualified else [],
                   self_won_penalty_qualified=False,
                   limits='Reused temporal shared-Opta evidence, component-isolated comparisons; '
                          'not independent holdout or whole-team vector comparisons.')
    (P / 'validation_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary

if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
