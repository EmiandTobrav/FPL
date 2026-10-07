"""Evaluate the frozen goal predictions on the preselected official FPL controls."""
from pathlib import Path
import hashlib,json
import pandas as pd
P=Path(__file__).resolve().parent;S=P.parent;KEY=['season','fixture','code']

def main():
 freeze=json.loads((P/'prediction_freeze.json').read_text())
 for name,digest in freeze['inputs'].items():
  if hashlib.sha256((P/name).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen input changed')
 if hashlib.sha256((P/'raw_goal_decisions.csv.gz').read_bytes()).hexdigest()!=freeze['prediction_sha256']:raise ValueError('Predictions changed')
 plan=pd.read_csv(P/'validation_plan.csv');pred=pd.read_csv(P/'raw_goal_decisions.csv.gz')
 people=pd.read_csv(P/'inputs/participants.csv.gz',low_memory=False)
 baseline=pd.read_csv(S/'fpl_authority/fpl_baseline.csv.gz',usecols=KEY+['assists'],low_memory=False)
 people=people.merge(baseline,on=KEY,validate='one_to_one')
 rows=[]
 for c in plan.to_dict('records'):
  g=pred[pred.match_id.eq(c['match_id'])&pred.scoring_team_id.eq(c['team_id'])]
  p=people[people.match_id.eq(c['match_id'])&people.team_id.eq(c['team_id'])]
  if len(g)!=1 or p.assists.isna().any() or p.assists.sum() not in [0,1]:raise ValueError('Control goal/label not uniquely attributable')
  expected=p[p.assists.eq(1)].player_id.iloc[0] if p.assists.sum()==1 else ''
  r=g.iloc[0];actual=r.recipient_player_id if r.status=='awarded' else ''
  outcome='unresolved' if r.status=='unresolved' else ('correct' if actual==expected else 'incorrect')
  rows.append({**c,'event_id':int(r.event_id),'route':r.route,'prediction_status':r.status,'expected_recipient_player_id':expected,'predicted_recipient_player_id':actual,'outcome':outcome,'source':'historical official FPL 2025/26 snapshot; unchanged target assist rules'})
 result=pd.DataFrame(rows);result.to_csv(P/'validation_results.csv',index=False)
 routes=[]
 for route,g in result.groupby('route',sort=True):
  n=int(g.outcome.ne('unresolved').sum());errors=int(g.outcome.eq('incorrect').sum())
  routes.append(dict(route=route,controls=len(g),resolved=n,correct=int(g.outcome.eq('correct').sum()),incorrect=errors,unresolved=int(g.outcome.eq('unresolved').sum()),qualified=bool(n>0 and errors==0)))
 route=pd.DataFrame(routes);route.to_csv(P/'validation_routes.csv',index=False)
 summary=dict(controls=len(result),fixtures=int(result[['season','fixture']].drop_duplicates().shape[0]),resolved=int(result.outcome.ne('unresolved').sum()),correct=int(result.outcome.eq('correct').sum()),incorrect=int(result.outcome.eq('incorrect').sum()),unresolved=int(result.outcome.eq('unresolved').sum()),qualified_routes=route.loc[route.qualified,'route'].tolist(),limits='A new temporal assist control split, not independent event-provider validation. Zero observed errors does not prove universal accuracy. Routes absent from resolved controls remain gated. Old ten narrative cases remain development only.',baseline_sha256=hashlib.sha256((S/'fpl_authority/fpl_baseline.csv.gz').read_bytes()).hexdigest())
 (P/'validation_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
