from pathlib import Path
import json,gzip,hashlib
import pandas as pd
from certificates import classify
P=Path(__file__).resolve().parent;S=P.parent

def main():
 files=[P/n for n in ['certificates.py','predict.py','protocol.json','direct_control_plan.csv','bound_control_plan.csv']]+[S/'assist_intentional_pass/inputs'/n for n in ['goals.csv.gz','goal_episodes.csv.gz','participants.csv.gz']]+[S/'assist_team_identity/inputs/team_identity.csv']
 frozen={str(p.relative_to(S)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 g=pd.read_csv(S/'assist_intentional_pass/inputs/goals.csv.gz',low_memory=False);ep=pd.read_csv(S/'assist_intentional_pass/inputs/goal_episodes.csv.gz',low_memory=False).groupby(['match_id','goal_event_id'],sort=False)
 p=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz');teams=p.dropna(subset=['team_id']).groupby('match_id').team_id.unique().to_dict();identities=p.groupby(['match_id','team_id','player_id']).size().to_dict()
 mapping=pd.read_csv(S/'assist_team_identity/inputs/team_identity.csv').set_index(['season','opta_numeric_code']).team_id.to_dict()
 rows=[]
 for goal in g.to_dict('records'):
  for r in classify(goal,ep.get_group((goal['match_id'],goal['event_id'])),teams.get(goal['match_id'],[]),mapping,identities):rows.append({**{k:goal[k] for k in ['season','fixture','match_id','event_id']},**r})
 out=pd.DataFrame(rows);data=gzip.compress(out.to_csv(index=False).encode(),mtime=0)
 record=dict(inputs=frozen,prediction_sha256=hashlib.sha256(data).hexdigest())
 if (P/'prediction_freeze.json').exists():assert json.loads((P/'prediction_freeze.json').read_text())==record
 (P/'predictions.csv.gz').write_bytes(data);(P/'prediction_freeze.json').write_text(json.dumps(record,indent=2)+'\n');print(out.groupby(['kind','award']).size().to_string())
if __name__=='__main__':main()
