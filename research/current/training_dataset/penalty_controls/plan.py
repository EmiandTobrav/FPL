"""Freeze recipient-isolated controls before loading FPL assist outcomes."""
from pathlib import Path
import hashlib
import json
import pandas as pd

P = Path(__file__).resolve().parent
R = P.parents[1]
S = R / 'scoring_2026_27/bulk_reconciliation/followup_2026_10_08'
KEY = ['match_id', 'event_id']

def main():
    pred_path = S / 'penalty_foul_recovery/predictions.csv.gz'
    joint_path = S / 'bulk_batch3/joint_predictions.csv.gz'
    people_path = S / 'assist_intentional_pass/inputs/participants.csv.gz'
    cover_path = S / 'assist_intentional_pass/results/team_coverage.csv'
    pred = pd.read_csv(pred_path)
    joint = pd.read_csv(joint_path).fillna({'recipient_player_id': ''})
    people = pd.read_csv(people_path)
    cover = pd.read_csv(cover_path).set_index(['match_id', 'team_id']).coverage_ok.to_dict()
    rows, contributions = [], []
    for r in pred[pred.season.eq('2025-26') & pred.kind.eq('ordinary_foul_penalty')].itertuples():
        if not cover.get((r.match_id, r.scoring_team_id), False):
            continue
        person = people[people.match_id.eq(r.match_id) & people.team_id.eq(r.scoring_team_id)
                        & people.player_id.eq(r.recipient_player_id)]
        if len(person) != 1:
            continue
        others = joint[joint.match_id.eq(r.match_id) & joint.team_id.eq(r.scoring_team_id)
                       & joint.event_id.ne(r.event_id)]
        known, facts, ambiguous = 0, [], False
        for goal in others.itertuples():
            if goal.status == 'awarded':
                value, method = int(goal.recipient_player_id == r.recipient_player_id), 'protected_goal_award'
            elif goal.status == 'no_assist':
                value, method = 0, 'protected_goal_no_assist'
            elif r.recipient_player_id not in json.loads(goal.allowed):
                value, method = 0, 'qualified_joint_candidate_exclusion'
            else:
                ambiguous = True
                break
            known += value
            facts.append(dict(match_id=r.match_id, penalty_event_id=r.event_id,
                              other_event_id=goal.event_id, recipient_player_id=r.recipient_player_id,
                              contribution=value, method=method))
        if ambiguous:
            continue
        rows.append(dict(season=r.season, fixture=r.fixture, match_id=r.match_id,
                         event_id=r.event_id, team_id=r.scoring_team_id,
                         recipient_player_id=r.recipient_player_id,
                         code=int(person.code.iloc[0]), other_goal_contributions=known,
                         other_goals=len(others), predicted_contribution=1))
        contributions.extend(facts)
    plan = pd.DataFrame(rows).sort_values(['fixture', 'event_id'])
    payload = plan.to_csv(index=False).encode()
    path = P / 'plan.csv'
    if path.exists() and path.read_bytes() != payload:
        raise ValueError('Frozen plan changed')
    path.write_bytes(payload)
    facts = pd.DataFrame(contributions).sort_values(['match_id', 'penalty_event_id', 'other_event_id'])
    evidence = facts.to_csv(index=False).encode()
    path = P / 'isolation_evidence.csv'
    if path.exists() and path.read_bytes() != evidence:
        raise ValueError('Frozen isolation evidence changed')
    path.write_bytes(evidence)
    inputs = [pred_path, joint_path, people_path, cover_path, P / 'plan.py', P / 'protocol.json',
              S / 'penalty_foul_recovery/rule.py', S / 'penalty_foul_recovery/freeze.json',
              S / 'bulk_batch3/joint_freeze.json', P / 'plan.csv', P / 'isolation_evidence.csv']
    freeze = {'inputs': {str(p.relative_to(R)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
              'comparisons': len(plan), 'distinct_fixtures': int(plan.fixture.nunique()),
              'outcomes_read_by_selection': False}
    path = P / 'freeze.json'
    if path.exists() and json.loads(path.read_text()) != freeze:
        raise ValueError('Frozen inputs changed')
    path.write_text(json.dumps(freeze, indent=2) + '\n')
    print({k: v for k, v in freeze.items() if k != 'inputs'})

if __name__ == '__main__':
    main()
