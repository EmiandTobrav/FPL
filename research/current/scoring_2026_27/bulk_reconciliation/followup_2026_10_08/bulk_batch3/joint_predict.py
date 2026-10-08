from pathlib import Path
import pandas as pd,json,hashlib,gzip
P=Path(__file__).resolve().parent;S=P.parent
configs=[('assist_candidate_bounds','bounds.csv.gz',None,None),('assist_certificate_expansion','predictions.csv.gz','validation_summary.json','qualified_bound_kinds'),('assist_actor_bounds','predictions.csv.gz','validation_summary.json','qualified_kinds')]+[(x,'predictions.csv.gz','validation_summary.json','qualified_kinds') for x in ['assist_possession_bounds','assist_pass_boundary','assist_attacking_touch_bounds','assist_failed_pass_bounds','assist_touch_bounds']]
files=[S/'assist_possession_bounds/results/goal_decisions.csv.gz',S/'assist_intentional_pass/inputs/participants.csv.gz',S/'assist_pass_boundary/validation_plan.csv',P/'joint_predict.py',P/'joint_protocol.json'];bounds={}
for stage,filename,vfile,key in configs:
 path=S/stage/filename;files.append(path);d=pd.read_csv(path)
 if vfile:
  vf=S/stage/vfile;files.append(vf);kinds=json.loads(vf.read_text())[key];d=d[d.kind.isin(kinds)]
 for r in d[d.season.eq('2025-26')].itertuples():
  actors=set(json.loads(r.candidates)) if hasattr(r,'candidates') else {r.candidate_player_id};k=(r.match_id,r.event_id);bounds[k]=bounds.get(k,actors)&actors
people=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz');teams={k:set(d.player_id.dropna()) for k,d in people.groupby(['match_id','team_id'])};goals=pd.read_csv(S/'assist_possession_bounds/results/goal_decisions.csv.gz');rows=[]
for r in goals[goals.season.eq('2025-26')].itertuples():
 actors=teams[(r.match_id,r.scoring_team_id)]-(set() if r.own_goal else {r.scorer_player_id});k=(r.match_id,r.event_id)
 if k in bounds:actors &= bounds[k]
 rows.append(dict(match_id=r.match_id,team_id=r.scoring_team_id,event_id=r.event_id,status=r.status,recipient_player_id=r.recipient_player_id,allowed=json.dumps(sorted(actors)),bounded=k in bounds))
b=gzip.compress(pd.DataFrame(rows).to_csv(index=False).encode(),mtime=0);(P/'joint_predictions.csv.gz').write_bytes(b);f=dict(inputs={str(x.relative_to(S)):hashlib.sha256(x.read_bytes()).hexdigest() for x in files},prediction_sha256=hashlib.sha256(b).hexdigest())
if (P/'joint_freeze.json').exists():assert json.loads((P/'joint_freeze.json').read_text())==f
(P/'joint_freeze.json').write_text(json.dumps(f,indent=2)+'\n');print('Joint prediction goals',len(rows))
