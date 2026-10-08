from pathlib import Path
import sys,json,gzip,hashlib
import pandas as pd
P=Path(__file__).resolve().parent;S=P.parent;KEY=['season','fixture','code']
sys.path.insert(0,str(S/'assist_intentional_pass'));from baseline.build import aggregate
sys.path.insert(0,str(S/'assist_certificate_expansion'));from certificates import q

def save(df,n):(P/'results'/n).write_bytes(gzip.compress(df.to_csv(index=False).encode(),mtime=0) if n.endswith('.gz') else df.to_csv(index=False).encode())
def main():
 val=json.loads((P/'validation_summary.json').read_text());assert val['qualified']
 for n,h in json.loads((P/'freeze.json').read_text()).items():assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h
 old=pd.read_csv(S/'assist_team_identity/results/goal_decisions.csv.gz');goals=old.copy();pred=pd.read_csv(S/'assist_certificate_expansion/predictions.csv.gz');people=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz');cover=pd.read_csv(S/'assist_intentional_pass/results/team_coverage.csv').set_index(['match_id','team_id']).coverage_ok.to_dict();ids=people.groupby(['match_id','team_id','player_id']).size().to_dict()
 anchors=pd.read_csv(S/'assist_intentional_pass/inputs/goal_episodes.csv.gz',usecols=['match_id','event_id','qualifier_json']).drop_duplicates(['match_id','event_id']).set_index(['match_id','event_id']).qualifier_json.to_dict()
 exclusions=pd.read_csv(S/'assist_certificate_expansion/results/candidate_exclusions.csv.gz');denials={(int(r.event_id),r.player_id) for r in exclusions.itertuples()};denials.update((int(c['goal_event_id']),c['candidate_player_id']) for c in json.loads((S/'assist_intentional_pass/inputs/official_cases.json').read_text()) if not c['expected_award']);idx=goals.reset_index(names='_row').set_index(['match_id','event_id']);applied=[]
 for r in pred[pred.award&pred.season.ne('2025-26')].itertuples():
  marker=q(anchors[(r.match_id,r.anchor_event_id)])
  if '210' not in marker or marker['210'] is not None:continue
  prior=idx.loc[(r.match_id,r.event_id)]
  if prior.status!='unresolved':continue
  if not cover.get((r.match_id,r.scoring_team_id),False) or ids.get((r.match_id,r.scoring_team_id,r.candidate_player_id),0)!=1:continue
  assert prior.scoring_team_id==r.scoring_team_id and (int(r.event_id),r.candidate_player_id) not in denials
  i=int(prior['_row']);goals.loc[i,'status']='awarded';goals.loc[i,'recipient_player_id']=r.candidate_player_id;goals.loc[i,'reason']='paired_clean_pass_explicit_null210_flag';goals.loc[i,'evidence_event_ids']=str(r.anchor_event_id);goals.loc[i,'evidence_scope']='temporal_null_encoding_team_vector_regression_shared_opta_review';applied.append(i)
 pd.testing.assert_frame_equal(old.drop(index=applied),goals.drop(index=applied));save(goals,'goal_decisions.csv.gz');save(goals.loc[applied],'new_goal_awards.csv');save(exclusions,'candidate_exclusions.csv.gz')
 baseline=pd.read_csv(S/'assist_intentional_pass/baseline/fpl_baseline.csv.gz')[KEY+['assists']];people=people.merge(baseline,on=KEY,validate='one_to_one');gm={k:g.to_dict('records') for k,g in goals.groupby(['match_id','scoring_team_id'])};totals=[]
 for r in people.to_dict('records'):
  key=(r['match_id'],r['team_id']);out=dict(value=r['assists'],reason='authoritative_fpl') if r['season']=='2025-26' else aggregate(gm.get(key,[]),r['player_id'],r['own_team_goals'],cover.get(key,False),denials)
  totals.append({**{k:r[k] for k in KEY+['name','match_id','team_id','player_id']},'historical_fpl_assists':r['assists'],**out})
 totals=pd.DataFrame(totals);save(totals,'player_match_totals.csv.gz');before=pd.read_csv(S/'tackle_event_recovery_v2/results/requirements.csv.gz',low_memory=False);pending=before[before.is_open&before.field.eq('assists_2026_27')][KEY+['field']];layer=pending.merge(totals,on=KEY,validate='one_to_one').dropna(subset=['value']);save(layer,'overlay.csv.gz')
 # Every previously complete assist value must still agree with the extended goal inventory.
 known=before[~before.is_open&before.field.eq('assists_2026_27')][KEY+['value']].merge(totals[KEY+['value']],on=KEY,validate='one_to_one',suffixes=('_before','_after'));assert known.value_after.notna().all() and known.value_before.eq(known.value_after).all()
 summary=dict(new_goal_awards=len(applied),new_complete_assist_fields=len(layer),new_zero_values=int(layer.value.eq(0).sum()),new_positive_values=int(layer.value.gt(0).sum()),changed_from_historical_fpl=int(layer.value.ne(layer.historical_fpl_assists).sum()),previously_complete_assists_preserved=len(known),validation=val)
 (P/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
