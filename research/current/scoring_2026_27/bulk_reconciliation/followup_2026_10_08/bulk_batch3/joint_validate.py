from pathlib import Path
import pandas as pd,json,hashlib,sys
P=Path(__file__).resolve().parent;S=P.parent;sys.path.insert(0,str(S/'assist_candidate_bounds'));from validate import feasible
f=json.loads((P/'joint_freeze.json').read_text())
for n,h in f['inputs'].items():assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h
assert hashlib.sha256((P/'joint_predictions.csv.gz').read_bytes()).hexdigest()==f['prediction_sha256']
g=pd.read_csv(P/'joint_predictions.csv.gz');gg={k:d for k,d in g.groupby(['match_id','team_id'])};p=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz').merge(pd.read_csv(S/'assist_intentional_pass/baseline/fpl_baseline.csv.gz')[['season','fixture','code','assists']],on=['season','fixture','code'],validate='one_to_one');pp={k:d for k,d in p.groupby(['match_id','team_id'])};rows=[]
for r in pd.read_csv(S/'assist_pass_boundary/validation_plan.csv').to_dict('records'):
 key=(r['match_id'],r['team_id']);goals=gg[key];players=pp[key];assert len(goals)==players.own_team_goals.iloc[0]
 remaining=players.set_index('player_id').assists.to_dict();allowed=[];conflicts=0
 for x in goals.itertuples():
  actors=set(json.loads(x.allowed))
  if x.status=='awarded':
   conflicts+=x.recipient_player_id not in actors;remaining[x.recipient_player_id]-=1
  elif x.status=='unresolved':allowed.append(actors)
  else:assert x.status=='no_assist'
 nonnegative=all(v>=0 and v%1==0 for v in remaining.values());units=[player for player,n in remaining.items() for _ in range(max(0,int(n)))];ok=nonnegative and not conflicts and feasible(units,allowed);rows.append({**r,'goals':len(goals),'bounded_goals':int(goals.bounded.sum()),'protected_award_conflicts':int(conflicts),'nonnegative_residuals':nonnegative,'feasible':bool(ok)})
d=pd.DataFrame(rows);d.to_csv(P/'joint_comparisons.csv',index=False);v=dict(teams=len(d),fixtures=int(d.match_id.nunique()),infeasible_teams=int((~d.feasible).sum()),protected_award_conflicts=int(d.protected_award_conflicts.sum()),qualified=bool(d.feasible.all()),limits='Intersection regression over reused shared-Opta controls, not independent validation. Fixed awards forced, not optional slots.');(P/'joint_validation_summary.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
