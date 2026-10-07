"""Quality gate and immutable manifest; run only after collection and label building."""
from pathlib import Path
import hashlib,json
import pandas as pd
from build_labels import P,R,O,SEASONS
VERSION='historical_points_plus_harmonized_defcon_v1'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 coverage=pd.read_csv(O/'coverage.csv');v=pd.read_csv(O/'validation_2025.csv')
 ok=v.source_identity_valid&v.defcon_reconstructed.notna();v['comparable']=ok
 v['mismatch']=ok&(v.defcon_reconstructed!=v.defcon_award)
 v['false_positive']=ok&(v.defcon_reconstructed==2)&(v.defcon_award==0)
 v['false_negative']=ok&(v.defcon_reconstructed==0)&(v.defcon_award==2)
 v['source_cbi']=v.blocks+v.interceptions+v.clearances
 for a,b in [('source_cbi','clearances_blocks_interceptions'),('source_tackles','tackles'),('source_recoveries','recoveries')]:v[a+'_difference']=v[a]-v[b]
 v.loc[v.mismatch].to_csv(O/'award_discrepancies_2025.csv',index=False)
 metrics=[]
 for group in ['position','round']:
  for key,g in v.groupby(group):
   z=g[g.comparable];tp=int(((z.defcon_award==2)&(z.defcon_reconstructed==2)).sum());fp=int(z.false_positive.sum());fn=int(z.false_negative.sum())
   metrics.append(dict(group=group,value=str(key),rows=len(g),comparable=len(z),mismatches=int(z.mismatch.sum()),false_positives=fp,false_negatives=fn,agreement=1-z.mismatch.mean(),precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None))
 pd.DataFrame(metrics).to_csv(O/'validation_breakdown.csv',index=False)
 summary=json.loads((O/'validation_summary.json').read_text());summary['award_agreement']=summary['equal_awards']/summary['comparable'];summary['count_agreement']=summary['equal_counts']/summary['comparable']
 tp=int(((v.loc[ok,'defcon_award']==2)&(v.loc[ok,'defcon_reconstructed']==2)).sum())
 summary.update(award_precision=tp/(tp+summary['false_positives']),award_recall=tp/(tp+summary['false_negatives']),population_point_error=2*(summary['false_positives']-summary['false_negatives']))
 (O/'validation_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 sources=json.loads((O/'sources.json').read_text());src=pd.DataFrame(sources)
 assert not src.duplicated(['season','fixture']).any()
 invariants=[]
 for season in SEASONS:
  cp=O/f'{season}_counts.csv';lp=O/f'{season}_labels.csv'
  if not cp.exists() or not lp.exists():continue
  c=pd.read_csv(cp);l=pd.read_csv(lp)
  assert not c.duplicated(['fixture','code']).any() and not l.duplicated(['fixture','element']).any()
  assert set(l.defcon_award.dropna().unique())<= {0,2}
  assert ((l.minutes>0)|(l.defcon_award==0)).all()
  assert l.loc[l.position=='GK','defcon_award'].eq(0).all()
  assert (l.defcon_lower<=l.defcon_upper).all()
  if season=='2025-26':assert l.points_scoring_version.equals(l.total_points)
  else:assert (l.points_scoring_version-l.total_points).fillna(-999).equals(l.defcon_award.fillna(-999))
  invariants.append(season)
 gates={'all_seasons':set(coverage.season)==set(SEASONS),'380_matches_per_season':len(src)==2660 and src.groupby('season').fixture.nunique().eq(380).all(),'no_unresolved_historical_awards':coverage.loc[coverage.season!='2025-26','source_missing_awards'].eq(0).all(),'complete_official_validation':summary['missing']==0,'agreement_at_least_99_percent':summary['award_agreement']>=.99,'all_season_invariants':set(invariants)==set(SEASONS)}
 integrity=json.loads((O/'source_integrity.json').read_text()) if (O/'source_integrity.json').exists() else {}
 gates['raw_responses_and_cache_verified']=integrity.get('raw_hashes_verified')==2660 and integrity.get('cache_rows_reproduced')==2660
 reproduction=json.loads((O/'reproduction_check.json').read_text()) if (O/'reproduction_check.json').exists() else {}
 gates['byte_identical_reproduction']=reproduction.get('verified_files')==14 and reproduction.get('restored_byte_identical') is True and reproduction.get('rebuilt_byte_identical') is True
 inputs={str(p.relative_to(R)):digest(p) for s in SEASONS for kind in ['gw','players','fixtures','teams'] if (p:=R/f'project/data/{s}_{kind}.csv').exists()}
 outputs={str(p.relative_to(P)):digest(p) for p in sorted(O.glob('*')) if p.suffix in ['.csv','.json'] and p.name not in ['manifest.json','progress.json','progress_subset.json','errors.json','errors_subset.json']}
 result=dict(version=VERSION,status='frozen_research' if all(gates.values()) else 'unlocked_candidate',gates={k:bool(x) for k,x in gates.items()},source='FotMob public match data; official FPL 2025/26 labels authoritative',scope='Historical original points plus harmonized defensive contributions; historical assists and bonus retained; not complete 2025/26 rule conversion',download_date='2026-10-07',cost_nok=0,inputs_sha256=inputs,outputs_sha256=outputs)
 (O/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['version','status','gates']},indent=2))
if __name__=='__main__':run()
