from pathlib import Path
import pandas as pd,json,sys,hashlib
P=Path(__file__).resolve().parent;S=P.parent
sys.path.insert(0,str(S/'assist_certificate_expansion'));from certificates import q
p=pd.read_csv(S/'assist_certificate_expansion/predictions.csv.gz');g=pd.read_csv(S/'assist_team_identity/results/goal_decisions.csv.gz');old=set(pd.read_csv(S/'assist_certificate_expansion/direct_control_plan.csv').match_id)
anchors=pd.read_csv(S/'assist_intentional_pass/inputs/goal_episodes.csv.gz',usecols=['match_id','event_id','qualifier_json']).drop_duplicates(['match_id','event_id']).set_index(['match_id','event_id']).qualifier_json.to_dict();idx=p[p.award].set_index(['match_id','event_id']);plan=[];pred=[]
allowed=['paired_intentional_direct_assist_markers','paired_explicit_intentional_assist_pass','explicit_goal_linked_foul_winner','paired_successful_goal_creating_pass','official_scorer_own_rebound']
for (mid,tid),group in g[g.season.eq('2020-21')&~g.match_id.isin(old)].groupby(['match_id','scoring_team_id']):
 if len(group)<2:continue
 new=0;ok=True;rows=[]
 for r in group.itertuples():
  if r.status in ['awarded','no_assist'] and r.reason in allowed:
   rows.append(dict(match_id=mid,team_id=tid,event_id=r.event_id,recipient=r.recipient_player_id if r.status=='awarded' else '',new_null=False));continue
  if r.status=='unresolved' and (mid,r.event_id) in idx.index:
   v=idx.loc[(mid,r.event_id)];marker=q(anchors[(mid,v.anchor_event_id)])
   if '210' in marker and marker['210'] is None:
    new+=1;rows.append(dict(match_id=mid,team_id=tid,event_id=r.event_id,recipient=v.candidate_player_id,new_null=True));continue
  ok=False
 if ok and new:
  plan.append(dict(match_id=mid,team_id=tid,goals=len(group),new_null=new));pred.extend(rows)
pd.DataFrame(plan).to_csv(P/'control_plan.csv',index=False);pd.DataFrame(pred).to_csv(P/'control_predictions.csv',index=False)
protocol={'rule':'Unchanged frozen assist_certificate_expansion award=True clean pass210 rule. No new causal rule or threshold relaxation.','plan':'All 2020/21 multi-goal teams in fixtures excluded from the old one-goal plan, whose entire goal inventory is either approved compatible direct/foul assist or this unchanged null-flag proposal. Selection uses no FPL assist outcomes.','gate':'Original 14 null-flag single-goal checks plus every new-null goal in complete multi-goal team vectors; at least20 goal occurrences total, zero vector errors, coverage and identities complete, no protected conflicts. Count goal occurrences and team vectors separately, not independent per-goal labels.','validation_limits':'2020/21 follows 2019/20 development encoding. Five new team vectors are regression/temporal evidence, not independent provider validation. Two proposed awards in one vector cannot be individually identified from match totals. All proposals and the selection rule remain frozen; no lower threshold if failure.','scope':'Apply qualified null-flag rule to pre2025 unknown goals only, preserve existing goals/exclusions/values. Input availability only.'}
(P/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
files=[P/'prepare.py',P/'protocol.json',P/'control_plan.csv',P/'control_predictions.csv']+[S/'assist_certificate_expansion'/n for n in ['predictions.csv.gz','prediction_freeze.json','direct_validation.csv','validation_summary.json']]+[S/'assist_team_identity/results/goal_decisions.csv.gz']
record={str(f.relative_to(S)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
if (P/'freeze.json').exists():assert json.loads((P/'freeze.json').read_text())==record
(P/'freeze.json').write_text(json.dumps(record,indent=2)+'\n');print(pd.DataFrame(plan).to_string(index=False))
