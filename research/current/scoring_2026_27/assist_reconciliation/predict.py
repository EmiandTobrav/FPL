"""Freeze code, then predict without loading validation outcomes."""
from pathlib import Path
import hashlib,json
import pandas as pd
from engine import classify
P=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(df,name):df.to_csv(P/name,index=False,compression={'method':'gzip','mtime':0})
def main():
 names=['engine.py','rules.py','predict.py','validation_protocol.json','validation_plan.csv','inputs/goals.csv.gz','inputs/goal_episodes.csv.gz','inputs/participants.csv.gz']
 frozen={n:sha(P/n) for n in names}
 freeze=P/'prediction_freeze.json'
 if freeze.exists() and json.loads(freeze.read_text())['inputs']!=frozen:raise ValueError('Frozen predictor/input changed; do not retune on the control labels')
 goals=pd.read_csv(P/'inputs/goals.csv.gz',low_memory=False)
 episodes=pd.read_csv(P/'inputs/goal_episodes.csv.gz',low_memory=False).groupby(['match_id','goal_event_id'],sort=False)
 participants=pd.read_csv(P/'inputs/participants.csv.gz',low_memory=False)
 teams=participants.dropna(subset=['team_id']).groupby('match_id').team_id.unique().to_dict()
 identities=participants.dropna(subset=['player_id','team_id']).groupby(['match_id','team_id','player_id']).size().to_dict()
 outputs=[];candidates=[]
 for g in goals.sort_values(['season','fixture','period_id','clock','event_id']).to_dict('records'):
  out,cs=classify(g,episodes.get_group((g['match_id'],g['event_id'])),teams.get(g['match_id'],[]))
  key={k:g[k] for k in ['season','fixture','match_id','event_id','period_id','clock']}
  if out['status']=='awarded' and identities.get((g['match_id'],out['scoring_team_id'],out['recipient_player_id']),0)!=1:
   out.update(status='unresolved',reason='recipient_identity_gap',missing='unique_fpl_player_link')
  outputs.append({**key,**out});candidates.extend({**key,**c} for c in cs)
 save(pd.DataFrame(outputs),'raw_goal_decisions.csv.gz');save(pd.DataFrame(candidates),'candidate_decisions.csv.gz')
 record=dict(inputs=frozen,prediction_sha256=sha(P/'raw_goal_decisions.csv.gz'),candidate_sha256=sha(P/'candidate_decisions.csv.gz'),protocol='Predictions saved before loading any control assist outcome.')
 if freeze.exists() and json.loads(freeze.read_text())!=record:raise ValueError('Non-reproducible prediction')
 freeze.write_text(json.dumps(record,indent=2)+'\n')
 print(pd.DataFrame(outputs).groupby(['route','status']).size().to_string())
if __name__=='__main__':main()
