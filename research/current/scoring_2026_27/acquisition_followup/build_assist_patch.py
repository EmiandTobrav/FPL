"""Six official per-goal decisions; four additions, not a full-season relabel.

The decisions are adjudications published by Premier League, not predictions.
Output is supplemental and never overwrites the locked dataset.
"""
from pathlib import Path
import ast
import json
import pandas as pd

P = Path(__file__).resolve().parent
SOURCE = 'https://www.premierleague.com/en/news/4362187/whats-new-in-202526-fantasy-changes-to-assists-rules'
# fixture, creator FPL id, scorer FPL id, awarded under the new rule, reason
DECISIONS = [
    (336, 755, 342, True, 'one defensive touch; reception inside box'),
    (201, 495, 503, True, 'one defensive clearance; reception inside box'),
    (312, 77, 78, True, 'defensive error is not a pass; intended receiver'),
    (223, 235, 232, True, 'last attacking touch before handball'),
    (254, 366, 652, False, 'unintended receiver outside box'),
    (213, 541, 543, False, 'two defensive touches'),
]


def build(fixtures, players):
    if fixtures.id.duplicated().any() or players.id.duplicated().any():
        raise ValueError('ambiguous identities')
    fixtures, players = fixtures.set_index('id'), players.set_index('id')
    records = []
    for fixture, creator, scorer, awarded, reason in DECISIONS:
        f, p = fixtures.loc[fixture], players.loc[creator]
        stats = {s['identifier']:s for s in ast.literal_eval(f['stats'])}
        goal_players = {v['element'] for side in ['h','a'] for v in stats['goals_scored'][side]}
        if scorer not in goal_players:
            raise ValueError('published example does not match fixture goalscorer')
        historical = sum(v['value'] for side in ['h','a'] for v in stats['assists'][side]
                         if v['element'] == creator)
        if historical != 0:
            raise ValueError('baseline changed: do not double-add a correction')
        records.append(dict(season='2024-25', fixture=fixture, fixture_code=int(f.code),
                            pulse_id=int(f.pulse_id), round=int(f.event), kickoff_time=f.kickoff_time,
                            element=creator, code=int(p.code), name=p.web_name, goalscorer_element=scorer,
                            historical_assists=historical, awarded_for_this_goal=awarded,
                            assist_delta=int(awarded), direct_points_delta=3*int(awarded),
                            assist_component_bps_delta=9*int(awarded), reason=reason,
                            evidence_scope='official example; not complete match/season adjudication',
                            source_url=SOURCE, evidence_published='2025-07-18', target_rules='2026-27'))
    return pd.DataFrame(records)


if __name__ == '__main__':
    root = P.parent.parent / 'project/data'
    result = build(pd.read_csv(root/'2024-25_fixtures.csv.gz'), pd.read_csv(root/'2024-25_players.csv.gz'))
    result.to_csv(P/'assist_decisions.csv', index=False)
    result[result.assist_delta.gt(0)].to_csv(P/'verified_assist_additions.csv', index=False)
    print(dict(decisions=len(result), additions=int(result.assist_delta.sum()),
               direct_points=int(result.direct_points_delta.sum()), complete_harmonization=False))
