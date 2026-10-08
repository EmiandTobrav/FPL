from pathlib import Path
import pandas as pd,json,hashlib
P=Path(__file__).resolve().parent;S=P.parent
for n,h in json.loads((P/'freeze.json').read_text()).items():assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h
plan=pd.read_csv(P/'control_plan.csv');pred=pd.read_csv(P/'control_predictions.csv').fillna({'recipient':''});old=pd.read_csv(S/'assist_certificate_expansion/direct_validation.csv');assert old.correct.all() and old.new_null_flag.sum()==14
people=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz').merge(pd.read_csv(S/'assist_intentional_pass/baseline/fpl_baseline.csv.gz')[['season','fixture','code','assists']],on=['season','fixture','code'],validate='one_to_one');cover=pd.read_csv(S/'assist_intentional_pass/results/team_coverage.csv').set_index(['match_id','team_id']).coverage_ok.to_dict();rows=[];vectors=[]
for r in plan.itertuples():
 p=people[people.match_id.eq(r.match_id)&people.team_id.eq(r.team_id)];g=pred[pred.match_id.eq(r.match_id)&pred.team_id.eq(r.team_id)];counts=g[g.recipient.ne('')].recipient.value_counts().to_dict();assert cover.get((r.match_id,r.team_id),False) and p.player_id.notna().all() and not p.player_id.duplicated().any() and p.assists.notna().all() and len(g)==p.own_team_goals.iloc[0] and set(counts)<=set(p.player_id)
 correct=True
 for a in p.itertuples():
  v=counts.get(a.player_id,0);ok=v==a.assists;correct &=ok;rows.append(dict(match_id=r.match_id,team_id=r.team_id,player_id=a.player_id,predicted=v,expected=a.assists,correct=ok))
 vectors.append(dict(match_id=r.match_id,team_id=r.team_id,new_null=r.new_null,correct=correct))
pd.DataFrame(rows).to_csv(P/'control_comparisons.csv',index=False);pd.DataFrame(vectors).to_csv(P/'control_vectors.csv',index=False)
s={'previous_single_goal_null_checks':14,'new_team_vectors':len(vectors),'new_goal_occurrences':int(plan.new_null.sum()),'total_goal_occurrences':14+int(plan.new_null.sum()),'new_player_comparisons':len(rows),'new_vector_errors':sum(not r['correct'] for r in vectors),'qualified':bool(len(vectors)>=5 and 14+plan.new_null.sum()>=20 and all(r['correct'] for r in vectors)),'limits':'20 goal occurrences across19 team vectors; two new awards share one vector and are not individually identified by match totals. Temporal/shared-source regression evidence, not independent provider validation.'}
(P/'validation_summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2))
