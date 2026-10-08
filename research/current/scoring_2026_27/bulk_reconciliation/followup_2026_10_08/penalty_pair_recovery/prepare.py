"""Freeze physical predictions and outcome-blind native control selection."""
from pathlib import Path
import gzip
import hashlib
import json
import pandas as pd
from rule import classify

P = Path(__file__).resolve().parent
S = P.parent
K = ['season', 'fixture', 'code']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def frozen_write(path, payload):
    if path.exists() and path.read_bytes() != payload:
        raise ValueError(f'Frozen selection changed: {path.name}')
    path.write_bytes(payload)

def main():
    people_path = S / 'assist_intentional_pass/inputs/participants.csv.gz'
    goals_path = S / 'assist_intentional_pass/inputs/goals.csv.gz'
    episodes_path = S / 'assist_intentional_pass/inputs/goal_episodes.csv.gz'
    cover_path = S / 'assist_intentional_pass/results/team_coverage.csv'
    joint_path = S / 'bulk_batch3/joint_predictions.csv.gz'
    people = pd.read_csv(people_path)
    goals = pd.read_csv(goals_path)
    episodes = pd.read_csv(episodes_path, low_memory=False).groupby(
        ['match_id', 'goal_event_id'], sort=False)
    identities = people.groupby(['match_id', 'team_id', 'player_id']).size().to_dict()
    rows = []
    for goal in goals.to_dict('records'):
        result = classify(goal, episodes.get_group((goal['match_id'], goal['event_id'])), identities)
        if result:
            rows.append({**{k: goal[k] for k in ['season', 'fixture', 'match_id', 'event_id']},
                         'taker_reference_present': '348' in json.loads(episodes.get_group(
                             (goal['match_id'], goal['event_id'])).set_index('event_id').loc[
                                 result['foul_event_id'], 'qualifier_json']), **result})
    pred = pd.DataFrame(rows).sort_values(['season', 'fixture', 'event_id'])
    frozen_write(P / 'predictions.csv.gz', gzip.compress(pred.to_csv(index=False).encode(), mtime=0))
    joint = pd.read_csv(joint_path).fillna({'recipient_player_id': ''})
    cover = pd.read_csv(cover_path).set_index(['match_id', 'team_id']).coverage_ok.to_dict()
    teams = {k: g for k, g in people.groupby(['match_id', 'team_id'])}
    plan, evidence = [], []
    for r in pred[pred.season.eq('2025-26')].itertuples():
        team_key = (r.match_id, r.scoring_team_id)
        if not cover.get(team_key, False):
            continue
        p = teams[team_key]
        if p.player_id.isna().any() or p.player_id.duplicated().any():
            continue
        others = joint[joint.match_id.eq(r.match_id) & joint.team_id.eq(r.scoring_team_id)
                       & joint.event_id.ne(r.event_id)]
        expected_goals = p.own_team_goals.unique()
        if len(expected_goals) != 1 or len(others) != expected_goals[0] - 1:
            continue
        whole = others.status.isin(['awarded', 'no_assist']).all()
        if r.kind == 'self_won_penalty' and not whole:
            continue
        persons = p if whole else p[p.player_id.eq(r.recipient_player_id)]
        eligible, pending = True, []
        for person in persons.itertuples():
            known = 0
            for other in others.itertuples():
                if other.status == 'awarded':
                    value, basis = int(person.player_id == other.recipient_player_id), 'fixed_source_award'
                elif other.status == 'no_assist':
                    value, basis = 0, 'fixed_source_no_assist'
                elif person.player_id not in json.loads(other.allowed):
                    value, basis = 0, 'qualified_joint_exclusion'
                else:
                    eligible = False
                    break
                known += value
                pending.append(dict(match_id=r.match_id, event_id=r.event_id,
                                    code=int(person.code), other_event_id=other.event_id,
                                    contribution=value, basis=basis))
            if not eligible:
                break
            plan.append(dict(season=r.season, fixture=int(r.fixture), match_id=r.match_id,
                             event_id=r.event_id, kind=r.kind, code=int(person.code),
                             player_id=person.player_id, team_id=r.scoring_team_id,
                             comparison='whole_team_vector' if whole else 'recipient_isolation',
                             other_goal_contributions=known,
                             predicted_contribution=int(r.kind == 'ordinary_foul_penalty'
                                                        and person.player_id == r.recipient_player_id),
                             taker_reference_present=r.taker_reference_present))
        if not eligible:
            plan = [x for x in plan if (x['match_id'], x['event_id']) != (r.match_id, r.event_id)]
        else:
            evidence.extend(pending)
    plan = pd.DataFrame(plan)
    facts = pd.DataFrame(evidence, columns=['match_id', 'event_id', 'code', 'other_event_id',
                                         'contribution', 'basis'])
    frozen_write(P / 'plan.csv', plan.to_csv(index=False).encode())
    frozen_write(P / 'isolation_evidence.csv', facts.to_csv(index=False).encode())
    inputs = [people_path, goals_path, episodes_path, cover_path, joint_path,
              S / 'bulk_batch3/joint_freeze.json', P / 'protocol.json', P / 'rule.py',
              Path(__file__), P / 'predictions.csv.gz', P / 'plan.csv', P / 'isolation_evidence.csv']
    freeze = {'inputs': {str(x.relative_to(S)): sha(x) for x in inputs},
              'outcomes_read_by_selection': False}
    frozen_write(P / 'freeze.json', (json.dumps(freeze, indent=2) + '\n').encode())
    print('Predictions:', pred.groupby(['season', 'kind']).size().to_dict())
    print('Control goals:', plan.drop_duplicates(['match_id', 'event_id']).groupby(
        ['kind', 'comparison']).size().to_dict())

if __name__ == '__main__':
    main()
