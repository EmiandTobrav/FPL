"""One defensive-count definition; official 2025/26 FPL labels remain authoritative."""
from pathlib import Path
import sys,json,hashlib
import pandas as pd
P=Path(__file__).resolve().parent;R=P.parents[1];O=P/'results';G=P.parent/'gap_repair';H=P.parent/'historical_fbref'
sys.path.insert(0,str(G));sys.path.insert(0,str(H))
from repair import resolve_duplicates,point_bounds,COUNTS
MAP={'tackles':'Tkl_Tackles','blocks':'Sh_Blocks','interceptions':'Int','clearances':'Clr','recoveries':'Recov'}
SEASONS=[f'{y}-{str(y+1)[2:]}' for y in range(2019,2026)]
BASE={'2019-20':('gap_repair','defcon_v2'),'2020-21':('gap_repair','defcon_v2'),'2021-22':('missing_2021','defcon'),'2022-23':('final_gaps','defcon'),'2023-24':('final_gaps','defcon'),'2024-25':('defcon_2024','defcon_estimated')}

def run(compare_prior=True):
 from package_data import prepare_inputs
 prepare_inputs()
 summaries=[];missing=[];identity=[];comparisons=[];validation=[];dups=[]
 for season in SEASONS:
  path=O/f'{season}_counts.csv'
  if not path.exists():continue
  src=pd.read_csv(path);assert not src.duplicated(['fixture','code']).any()
  f=pd.read_csv(R/f'project/data/{season}_gw.csv');players=pd.read_csv(R/f'project/data/{season}_players.csv');fixtures=pd.read_csv(R/f'project/data/{season}_fixtures.csv').set_index('id');teams=pd.read_csv(R/f'project/data/{season}_teams.csv').set_index('id')
  if 'position' not in f:f['position']=f.element.map(players.set_index('id').element_type).map({1:'GK',2:'DEF',3:'MID',4:'FWD'})
  f['position']=f.position.replace({'GKP':'GK'});f=f[f.position.isin(['GK','DEF','MID','FWD'])].copy()
  exact=f.duplicated();dups += [dict(season=season,element=int(x.element),fixture=int(x.fixture),retained=False,reason='exact duplicate across all input columns') for x in f.loc[exact].itertuples()];f=f.loc[~exact].copy()
  f,logs=resolve_duplicates(f,fixtures);dups += [dict(season=season,**x) for x in logs]
  f=f.merge(players[['id','code']],left_on='element',right_on='id',how='left',validate='many_to_one');assert f.code.notna().all();f['expected_team']=f.fixture.map(fixtures.team_h).where(f.was_home,f.fixture.map(fixtures.team_a)).map(teams.name)
  j=f.merge(src.rename(columns={'name':'source_name','tackles':'source_tackles','recoveries':'source_recoveries'}),on=['fixture','code'],how='left',validate='one_to_one',indicator=True)
  # Source code, official fixture, and fixture side define identity. Other statistics
  # are audited; discrepancies can reflect differing post-match revisions.
  matched=j._merge=='both';team_ok=j.source_team.eq(j.expected_team);valid=matched&team_ok
  active=(j.minutes>0)&(j.position!='GK')
  j['minutes_difference']=j.source_minutes-j.minutes;j['goals_difference']=j.source_goals-j.goals_scored
  issue=active&valid&(j.minutes_difference.abs().gt(2)|j.goals_difference.ne(0))
  identity.append(j.loc[issue,['element','fixture','code','name','source_name','position','minutes','source_minutes','minutes_difference','goals_scored','source_goals','goals_difference','expected_team','source_team']].assign(season=season))
  a=j[['position','minutes']].copy()
  for src_col,dest in {'source_tackles':'Tkl_Tackles','blocks':'Sh_Blocks','interceptions':'Int','clearances':'Clr','source_recoveries':'Recov'}.items():a[dest]=j[src_col].where(valid)
  pred,lo,hi,inferred=point_bounds(a)
  j['defcon_reconstructed']=pred;j['defcon_lower']=lo;j['defcon_upper']=hi
  j['defcon_count_reconstructed']=a[COUNTS[:4]].sum(axis=1,min_count=4)+a.Recov.where(j.position.isin(['MID','FWD']),0)
  j['quality']='fotmob_harmonized_observed';j.loc[issue,'quality']='fotmob_observed_stat_revision_disagreement';j.loc[inferred,'quality']='threshold_proven_partial_counts';j.loc[pred.isna(),'quality']='missing';j.loc[~active,'quality']='zero_ineligible_or_no_minutes'
  j['defcon_award']=pred;j['points_scoring_version']=j.total_points+pred
  if season=='2025-26':
   th=j.position.map({'DEF':10,'MID':12,'FWD':12});official=(2*(j.defensive_contribution>=th)).astype(float);official.loc[~active]=0
   j['defcon_award']=official;j['points_scoring_version']=j.total_points;j['quality']='official_fpl'
   v=j.loc[active,['element','fixture','round','code','name','position','minutes','source_minutes','clearances_blocks_interceptions','tackles','recoveries','defensive_contribution','source_tackles','blocks','interceptions','clearances','source_recoveries','defcon_count_reconstructed','defcon_reconstructed','defcon_award']].copy()
   v['source_identity_valid']=valid[active];validation.append(v)
  missing.append(j.loc[active&pred.isna(),['element','fixture','code','name','position','minutes','source_name','source_team','expected_team','source_minutes']].assign(season=season))
  outcols=['element','fixture','round','code','position','minutes','total_points','defcon_award','points_scoring_version','defcon_reconstructed','defcon_lower','defcon_upper','quality']
  j[outcols].to_csv(O/f'{season}_labels.csv',index=False)
  changed=None;delta=None
  if compare_prior and season in BASE:
   folder,col=BASE[season]
   b=pd.concat([pd.read_csv(x) for x in sorted((P.parent/folder/'results').glob('GW*.csv'))],ignore_index=True) if season=='2024-25' else pd.read_csv(P.parent/folder/f'results/{season}_labels.csv')
   c=j.merge(b[['element','fixture',col]].rename(columns={col:'prior_defcon'}),on=['element','fixture'],validate='one_to_one')
   validcomp=c.defcon_reconstructed.notna()&c.prior_defcon.notna();diff=validcomp&(c.defcon_reconstructed!=c.prior_defcon)
   changed=int(diff.sum());delta=float((c.loc[validcomp,'defcon_reconstructed']-c.loc[validcomp,'prior_defcon']).sum())
   comparisons.append(c.loc[diff,['element','fixture','code','name','position','prior_defcon','defcon_reconstructed']].assign(season=season))
  summaries.append({'season':season,'source_matches':int(src.fixture.nunique()),'active_outfield_rows':int(active.sum()),'source_complete_awards':int(pred[active].notna().sum()),'source_missing_awards':int(pred[active].isna().sum()),'official_label_missing':int(j.loc[active,'defcon_award'].isna().sum()),'awards':int((j.loc[active,'defcon_award']==2).sum()),'stat_revision_flags':int(issue.sum()),'changed_awards_vs_prior':changed,'player_population_point_delta_vs_prior':delta})
 pd.DataFrame(summaries).to_csv(O/'coverage.csv',index=False);pd.concat(missing).to_csv(O/'missing_rows.csv',index=False);pd.concat(identity).to_csv(O/'stat_disagreements.csv',index=False)
 if comparisons:pd.concat(comparisons).to_csv(O/'changed_awards.csv',index=False)
 if validation:
  v=pd.concat(validation);v.to_csv(O/'validation_2025.csv',index=False);ok=v.defcon_reconstructed.notna()&v.source_identity_valid
  report={'active_outfield_rows':len(v),'comparable':int(ok.sum()),'missing':int((~ok).sum()),'equal_awards':int((v.loc[ok,'defcon_reconstructed']==v.loc[ok,'defcon_award']).sum()),'false_positives':int(((v.loc[ok,'defcon_reconstructed']==2)&(v.loc[ok,'defcon_award']==0)).sum()),'false_negatives':int(((v.loc[ok,'defcon_reconstructed']==0)&(v.loc[ok,'defcon_award']==2)).sum()),'equal_counts':int((v.loc[ok,'defcon_count_reconstructed']==v.loc[ok,'defensive_contribution']).sum())}
  (O/'validation_summary.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
 pd.DataFrame(dups).to_csv(O/'duplicate_audit.csv',index=False)
 print(pd.DataFrame(summaries).to_string(index=False))
if __name__=='__main__':run(compare_prior='--skip-prior-comparison' not in sys.argv)
