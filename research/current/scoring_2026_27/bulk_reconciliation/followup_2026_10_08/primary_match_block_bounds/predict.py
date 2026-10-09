"""Predict from previously qualified counters before GL outcome comparison."""
import gzip,json
import pandas as pd
from collect import P,B,R,digest,write
K=['season','fixture','code'];T=['season','fixture','primary_team_id']
def save(frame,name):
 raw=frame.to_csv(index=False).encode();(P/name).write_bytes(gzip.compress(raw,mtime=0) if name.endswith('.gz') else raw)
def main():
 for n,h in json.loads((P/'selection_freeze.json').read_text()).items():assert digest(P/n)==h
 plan=json.loads((P/'plan.json').read_text());parent=json.loads((P/'inputs/parent_CURRENT.json').read_text())
 assert digest(B/parent['requirements'])==parent['requirements_sha256']
 deps={str((B/parent['requirements']).relative_to(R)):parent['requirements_sha256']}
 for n,h in plan['sources'].items():
  path=P.parent/n;assert digest(path)==h,n;deps[str(path.relative_to(R))]=h
 primary=P.parent/'primary_gap_recovery';frozen=json.loads((primary/'freeze.json').read_text())
 for n,h in frozen['inputs'].items():
  # These two old GL-specific dependencies do not derive outfielder_block.
  if n in ['bulk_followup/results/requirements.csv.gz','season_conservation/combined/season_proofs.csv']:continue
  path=P.parent/n;assert digest(path)==h,n;deps[str(path.relative_to(R))]=h
 validation=json.loads((primary/'validation_summary.json').read_text())
 assert validation['field_errors']==validation['explicit_component_errors']==0 and validation['explicit_component_comparisons']==344
 checks=pd.read_csv(primary/'explicit_component_controls.csv');assert len(checks)==344
 ledger=pd.read_csv(B/parent['requirements'],low_memory=False);population=ledger[ledger.field.eq('goal_line_clearances')][K+['position']]
 q=pd.read_csv(primary/'qualified_components.csv.gz');raw=pd.DataFrame(json.loads((primary/'players.json').read_text()))
 assert len(q)==len(raw)==685 and not q.duplicated(K).any() and not raw.duplicated(K).any()
 teams=pd.read_csv(P.parent/'season_conservation/inputs/full_team_totals.csv').set_index(T)
 proof=pd.read_csv(primary/'conservation.csv');proof=proof[proof.counter.eq('outfielder_block')].set_index(T)
 a=q[q.outfielder_block.eq(0)].merge(raw[K+['outfielder_block']],on=K,validate='one_to_one',suffixes=('','_raw'))
 origins=[]
 for row in a.itertuples():
  if pd.notna(row.outfielder_block_raw):
   assert row.outfielder_block_raw==0;origins.append('explicit_primary_player_zero')
  else:
   x=proof.loc[(row.season,row.fixture,row.primary_team_id)]
   assert x.qualified and x.total==x.known_sum and x.missing_players>0
   vals=raw[(raw.season==row.season)&(raw.fixture==row.fixture)&(raw.primary_team_id==row.primary_team_id)].outfielder_block
   assert teams.loc[(row.season,row.fixture,row.primary_team_id),'outfielder_block']==x.total
   assert len(vals)==x.active_players and int(vals.notna().sum())==x.explicit_players
   assert vals.dropna().ge(0).all() and vals.dropna().mod(1).eq(0).all() and vals.sum()==x.total
   origins.append('original_exact_complete_roster_team_conservation')
 a['block_zero_proof']=origins;a=a.merge(population,on=K,validate='one_to_one');a=a[a.position.isin(['DEF','MID','FWD'])]
 a['value']=0;a['proof']='qualified_primary_zero_match_block_subset'
 pred=a[K+['value','proof','block_zero_proof']];assert not pred.duplicated(K).any();save(pred,'predictions.csv.gz')
 season=P.parent/'player_season_block_bounds';v=json.loads((season/'results/validation.json').read_text());assert v['qualified'] and v['errors']==v['positive_contradictions']==0
 regression=pd.read_csv(season/'predictions.csv.gz')[K+['value']];regression['scope']='prior_qualified_season_regression'
 current=pred[K+['value']].copy();current['scope']='primary_match_block';regression=pd.concat([current,regression],ignore_index=True).drop_duplicates(K,keep='first')
 save(regression,'regression_predictions.csv.gz');write(P/'dependencies.json',deps)
 write(P/'prediction_freeze.json',{n:digest(P/n) for n in ['plan.json','selection_freeze.json','dependencies.json','predictions.csv.gz','regression_predictions.csv.gz']})
 print('Frozen primary predictions',len(pred),'all regression predictions',len(regression))
if __name__=='__main__':main()
