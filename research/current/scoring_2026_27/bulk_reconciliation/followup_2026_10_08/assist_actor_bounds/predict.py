from pathlib import Path
import pandas as pd,json,hashlib,gzip
from certificates import classify
P=Path(__file__).resolve().parent;S=P.parent
p=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz');teams=p.dropna(subset=['team_id']).groupby('match_id').team_id.unique().to_dict();identities=p.groupby(['match_id','team_id','player_id']).size().to_dict();mapping=pd.read_csv(S/'assist_team_identity/inputs/team_identity.csv').set_index(['season','opta_numeric_code']).team_id.to_dict();g=pd.read_csv(S/'assist_intentional_pass/inputs/goals.csv.gz');ep=pd.read_csv(S/'assist_intentional_pass/inputs/goal_episodes.csv.gz',low_memory=False).groupby(['match_id','goal_event_id'],sort=False);rows=[]
for goal in g.to_dict('records'):
 for r in classify(goal,ep.get_group((goal['match_id'],goal['event_id'])),teams.get(goal['match_id'],[]),mapping,identities):
  rows.append({**{k:goal[k] for k in ['season','fixture','match_id','event_id']},**r,'candidates':json.dumps(r['candidates']),'anchor_event_ids':json.dumps(r['anchor_event_ids'])})
out=pd.DataFrame(rows);raw=gzip.compress(out.to_csv(index=False).encode(),mtime=0);(P/'predictions.csv.gz').write_bytes(raw)
# Keep the existing all2025 scoring-team plan unchanged; only the new predictor is new.
plan=(S/'assist_certificate_expansion/bound_control_plan.csv').read_bytes();(P/'validation_plan.csv').write_bytes(plan)
files=[P/n for n in ['certificates.py','predict.py','protocol.json','validation_plan.csv']]+[S/'assist_intentional_pass/inputs'/n for n in ['participants.csv.gz','goals.csv.gz','goal_episodes.csv.gz']]+[S/'assist_team_identity/inputs/team_identity.csv']
f={'inputs':{str(x.relative_to(S)):hashlib.sha256(x.read_bytes()).hexdigest() for x in files},'prediction_sha256':hashlib.sha256(raw).hexdigest()}
if (P/'freeze.json').exists():assert json.loads((P/'freeze.json').read_text())==f
(P/'freeze.json').write_text(json.dumps(f,indent=2)+'\n');print(out.groupby(['season','kind']).size().to_string())
