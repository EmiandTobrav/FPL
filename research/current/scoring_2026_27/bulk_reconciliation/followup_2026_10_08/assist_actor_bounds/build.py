from pathlib import Path
import pandas as pd,json,sys,gzip,hashlib
P=Path(__file__).resolve().parent;S=P.parent;K=['season','fixture','code'];sys.path.insert(0,str(S/'assist_intentional_pass'));from baseline.build import aggregate

def save(df,n):(P/'results'/n).write_bytes(gzip.compress(df.to_csv(index=False).encode(),mtime=0) if n.endswith('.gz') else df.to_csv(index=False).encode())
def main():
 v=json.loads((P/'validation_summary.json').read_text());assert v['qualified_kinds'];f=json.loads((P/'freeze.json').read_text())
 for n,h in f['inputs'].items():assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h
 assert hashlib.sha256((P/'predictions.csv.gz').read_bytes()).hexdigest()==f['prediction_sha256']
 goals=pd.read_csv(S/'assist_null_pass_recovery/results/goal_decisions.csv.gz');idx=goals.set_index(['match_id','event_id']);people=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz').merge(pd.read_csv(S/'assist_intentional_pass/baseline/fpl_baseline.csv.gz')[K+['assists']],on=K,validate='one_to_one');cover=pd.read_csv(S/'assist_intentional_pass/results/team_coverage.csv').set_index(['match_id','team_id']).coverage_ok.to_dict();pteam={k:p for k,p in people.groupby(['match_id','team_id'])};prior=pd.read_csv(S/'assist_certificate_expansion/results/candidate_exclusions.csv.gz');denials={(int(r.event_id),r.player_id) for r in prior.itertuples()};denials.update((int(c['goal_event_id']),c['candidate_player_id']) for c in json.loads((S/'assist_intentional_pass/inputs/official_cases.json').read_text()) if not c['expected_award']);pred=pd.read_csv(P/'predictions.csv.gz');rows=[];applied=[]
 for r in pred[pred.kind.isin(v['qualified_kinds'])&pred.season.ne('2025-26')].itertuples():
  old=idx.loc[(r.match_id,r.event_id)]
  if old.status!='unresolved' or not cover.get((r.match_id,r.scoring_team_id),False):continue
  candidates=set(json.loads(r.candidates));p=pteam[(r.match_id,r.scoring_team_id)];assert candidates<=set(p.player_id.dropna())
  assert any((int(r.event_id),c) not in denials for c in candidates),'Empty intersection with prior positive bounds'
  applied.append(r._asdict())
  for a in p.player_id.dropna():
   key=(int(r.event_id),a)
   if a in candidates or key in denials:continue
   denials.add(key);rows.append(dict(match_id=r.match_id,event_id=r.event_id,player_id=a,candidate_player_id=None,pass_event_id=None,reason='multi_actor_source_certificate_'+r.kind,candidate_set=r.candidates))
 additions=pd.DataFrame(rows);all_ex=pd.concat([prior,additions],ignore_index=True).drop_duplicates(['match_id','event_id','player_id']);save(additions,'new_candidate_exclusions.csv.gz');save(all_ex,'candidate_exclusions.csv.gz');save(pd.DataFrame(applied),'applied_bounds.csv');save(goals,'goal_decisions.csv.gz')
 gm={k:g.to_dict('records') for k,g in goals.groupby(['match_id','scoring_team_id'])};totals=[]
 for r in people.to_dict('records'):
  key=(r['match_id'],r['team_id']);out=dict(value=r['assists'],reason='authoritative_fpl') if r['season']=='2025-26' else aggregate(gm.get(key,[]),r['player_id'],r['own_team_goals'],cover.get(key,False),denials);totals.append({**{k:r[k] for k in K+['name','match_id','team_id','player_id']},'historical_fpl_assists':r['assists'],**out})
 totals=pd.DataFrame(totals);save(totals,'player_match_totals.csv.gz');before=pd.read_csv(S/'tackle_event_recovery_v2/results/requirements.csv.gz',low_memory=False);layer=before[before.is_open&before.field.eq('assists_2026_27')][K+['field']].merge(totals,on=K,validate='one_to_one').dropna(subset=['value']);save(layer,'overlay.csv.gz')
 oldtot=pd.read_csv(S/'assist_null_pass_recovery/results/player_match_totals.csv.gz');known=oldtot.dropna(subset=['value'])[K+['value']].merge(totals[K+['value']],on=K,validate='one_to_one',suffixes=('_before','_after'));assert known.value_before.eq(known.value_after).all()
 s=dict(new_bound_goals=len(applied),new_candidate_exclusions=len(rows),new_assist_fields_including_null_pass=len(layer),additional_assist_fields=len(layer)-json.loads((S/'assist_null_pass_recovery/results/summary.json').read_text())['new_complete_assist_fields'],zero_values=int(layer.value.eq(0).sum()),positive_values=int(layer.value.gt(0).sum()),different_from_historical_fpl=int(layer.value.ne(layer.historical_fpl_assists).sum()),validation=v);(P/'results/summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2))
if __name__=='__main__':main()
