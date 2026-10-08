from pathlib import Path
import pandas as pd,json,sys,hashlib
P=Path(__file__).resolve().parent;S=P.parent;sys.path.insert(0,str(S/'assist_candidate_bounds'));from validate import feasible
f=json.loads((P/'freeze.json').read_text())
for n,h in f['inputs'].items():assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h
assert hashlib.sha256((P/'predictions.csv.gz').read_bytes()).hexdigest()==f['prediction_sha256']
pred=pd.read_csv(P/'predictions.csv.gz');bounds={(r.match_id,r.event_id):set(json.loads(r.candidates)) for r in pred.itertuples()};kind=pred.set_index(['match_id','event_id']).kind.to_dict();goals=pd.read_csv(S/'assist_actor_bounds/results/goal_decisions.csv.gz');idx=goals.set_index(['match_id','event_id']);people=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz').merge(pd.read_csv(S/'assist_intentional_pass/baseline/fpl_baseline.csv.gz')[['season','fixture','code','assists']],on=['season','fixture','code'],validate='one_to_one');gg={k:g for k,g in goals.groupby(['match_id','scoring_team_id'])};pp={k:p for k,p in people.groupby(['match_id','team_id'])};rows=[];counts={};single=[]
for c in pd.read_csv(P/'validation_plan.csv').to_dict('records'):
 key=(c['match_id'],c['team_id']);g=gg[key];p=pp[key];assert p.assists.notna().all() and len(g)==p.own_team_goals.iloc[0];players=set(p.player_id.dropna());allowed=[]
 for r in g.itertuples():
  k=(r.match_id,r.event_id);allowed.append(bounds[k] if k in bounds else players if r.own_goal else players-{r.scorer_player_id})
  if k in bounds and r.status=='unresolved':counts[kind[k]]=counts.get(kind[k],0)+1
 units=[r.player_id for r in p.itertuples() for _ in range(int(r.assists))];rows.append({**c,'feasible':feasible(units,allowed)})
 if len(g)==1 and (g.iloc[0].match_id,g.iloc[0].event_id) in bounds:single.append({**c,'compatible':all(u in allowed[0] for u in units)})
conflicts=[]
for k,actors in bounds.items():
 r=idx.loc[k]
 if r.status=='awarded' and r.recipient_player_id not in actors:conflicts.append(dict(match_id=k[0],event_id=k[1],kind=kind[k],recipient=r.recipient_player_id))
pd.DataFrame(rows).to_csv(P/'vector_controls.csv',index=False);pd.DataFrame(single).to_csv(P/'single_goal_controls.csv',index=False);pd.DataFrame(conflicts,columns=['match_id','event_id','kind','recipient']).to_csv(P/'protected_conflicts.csv',index=False)
prior=pd.read_csv(S/'assist_actor_bounds/results/applied_bounds.csv')
positive_conflicts=[]
for r in prior.itertuples():
 k=(r.match_id,r.event_id)
 if k in bounds and not (bounds[k]&set(json.loads(r.candidates))):positive_conflicts.append(dict(match_id=r.match_id,event_id=r.event_id))
pd.DataFrame(positive_conflicts,columns=['match_id','event_id']).to_csv(P/'positive_bound_conflicts.csv',index=False)
ok=not positive_conflicts and sum(counts.values())>=20 and len(single)>=20 and all(r['feasible'] for r in rows) and all(r['compatible'] for r in single) and not conflicts
v={'teams':len(rows),'fixtures':len({r['match_id'] for r in rows}),'infeasible_teams':sum(not r['feasible'] for r in rows),'single_goal_checks':len(single),'single_goal_errors':sum(not r['compatible'] for r in single),'new_bound_controls':counts,'protected_conflicts':len(conflicts),'positive_bound_conflicts':len(positive_conflicts),'qualified_kinds':[k for k,n in counts.items() if n>=5] if ok else [],'limits':'Temporal regression with previously seen2025 outcomes and sharedOpta source, not independent validation. Candidate exclusions only.'}
(P/'validation_summary.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
