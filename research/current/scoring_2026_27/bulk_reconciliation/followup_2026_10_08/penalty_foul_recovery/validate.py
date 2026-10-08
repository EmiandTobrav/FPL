from pathlib import Path
import pandas as pd,json,hashlib
P=Path(__file__).resolve().parent;S=P.parent;K=['season','fixture','code']
f=json.loads((P/'freeze.json').read_text())
for n,h in f['inputs'].items():assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h
assert hashlib.sha256((P/'predictions.csv.gz').read_bytes()).hexdigest()==f['predictions_sha256']
pred=pd.read_csv(P/'predictions.csv.gz').fillna({'recipient_player_id':''});plan=pd.read_csv(P/'validation_plan.csv');people=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz').merge(pd.read_csv(S/'assist_intentional_pass/baseline/fpl_baseline.csv.gz')[K+['assists']],on=K,validate='one_to_one');cover=pd.read_csv(S/'assist_intentional_pass/results/team_coverage.csv').set_index(['match_id','team_id']).coverage_ok.to_dict();rows=[]
for r in pred.merge(plan,left_on=['season','fixture','match_id','scoring_team_id'],right_on=['season','fixture','match_id','team_id'],validate='many_to_one').itertuples():
 p=people[people.match_id.eq(r.match_id)&people.team_id.eq(r.scoring_team_id)]
 assert cover.get((r.match_id,r.scoring_team_id),False) and p.assists.notna().all() and not p.player_id.duplicated().any()
 expected=p.player_id.eq(r.recipient_player_id).astype(int);correct=expected.eq(p.assists).all();rows.append(dict(season=r.season,fixture=r.fixture,event_id=r.event_id,kind=r.kind,status=r.status,recipient_player_id=r.recipient_player_id,correct=bool(correct),players=len(p)))
c=pd.DataFrame(rows);c.to_csv(P/'validation_comparisons.csv',index=False)
old=pd.read_csv(S/'assist_actor_bounds/results/goal_decisions.csv.gz').fillna({'recipient_player_id':''});z=pred.merge(old[['match_id','event_id','status','recipient_player_id']],on=['match_id','event_id'],suffixes=('','_old'),validate='one_to_one');conf=z[z.status_old.ne('unresolved')&(~z.status.eq(z.status_old)|~z.recipient_player_id.eq(z.recipient_player_id_old))];conf.to_csv(P/'protected_conflicts.csv',index=False)
den=pd.read_csv(S/'assist_actor_bounds/results/candidate_exclusions.csv.gz');d={(int(r.event_id),r.player_id) for r in den.itertuples()};d.update((int(x['goal_event_id']),x['candidate_player_id']) for x in json.loads((S/'assist_intentional_pass/inputs/official_cases.json').read_text()) if not x['expected_award']);dc=sum((int(r.event_id),r.recipient_player_id) in d for r in pred[pred.status.eq('awarded')].itertuples())
counts=c.groupby('kind').size().to_dict();gate=len(c)>=20 and c.correct.all() and len(conf)==0 and dc==0
v=dict(comparisons=len(c),by_kind=counts,errors=int((~c.correct).sum()),protected_conflicts=len(conf),denial_conflicts=dc,qualified_kinds=[k for k,n in counts.items() if gate and n>=5],limits='Temporal regression/shared Opta source; reused outcomes, not independent validation.')
(P/'validation_summary.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
