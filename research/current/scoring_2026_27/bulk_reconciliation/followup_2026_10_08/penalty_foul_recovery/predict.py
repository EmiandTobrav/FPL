from pathlib import Path
import json,pandas as pd,hashlib,gzip
from rule import classify
P=Path(__file__).resolve().parent;S=P.parent
people=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz');ids=people.groupby(['match_id','team_id','player_id']).size().to_dict();g=pd.read_csv(S/'assist_intentional_pass/inputs/goals.csv.gz');ep=pd.read_csv(S/'assist_intentional_pass/inputs/goal_episodes.csv.gz',low_memory=False).groupby(['match_id','goal_event_id'],sort=False);rows=[]
for goal in g.to_dict('records'):
 r=classify(goal,ep.get_group((goal['match_id'],goal['event_id'])),ids)
 if r:rows.append({**{k:goal[k] for k in ['season','fixture','match_id','event_id']},**r})
pred=pd.DataFrame(rows);raw=gzip.compress(pred.to_csv(index=False).encode(),mtime=0);(P/'predictions.csv.gz').write_bytes(raw)
plan=people[people.season.eq('2025-26')&people.own_team_goals.eq(1)][['season','fixture','match_id','team_id']].drop_duplicates();plan.to_csv(P/'validation_plan.csv',index=False)
files=[P/n for n in ['rule.py','predict.py','protocol.json','validation_plan.csv']]+[S/'assist_intentional_pass/inputs'/n for n in ['goals.csv.gz','goal_episodes.csv.gz','participants.csv.gz']]
f={'inputs':{str(p.relative_to(S)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'predictions_sha256':hashlib.sha256(raw).hexdigest()}
if (P/'freeze.json').exists():assert json.loads((P/'freeze.json').read_text())==f
(P/'freeze.json').write_text(json.dumps(f,indent=2)+'\n');print(pred.groupby(['season','kind']).size().to_string())
