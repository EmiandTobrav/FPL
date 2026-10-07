"""Conservative missing-cell supplementation; preserves all frozen known labels."""
from pathlib import Path
import sys,json,hashlib
import pandas as pd
P=Path(__file__).resolve().parent;R=P.parents[1];O=P/'results';G=P.parent/'gap_repair';H=P.parent/'historical_fbref'
sys.path.insert(0,str(G));sys.path.insert(0,str(H))
from repair import point_bounds,COUNTS,OVERRIDES,source_frame
MAP={'tackles':'Tkl_Tackles','blocks':'Sh_Blocks','interceptions':'Int','clearances':'Clr','recoveries':'Recov'}
def run():
 for name,sha in json.loads((P/'input_sha256.json').read_text()).items():assert hashlib.sha256((P.parents[3]/name).read_bytes()).hexdigest()==sha,name
 src=pd.read_csv(O/'fotmob_players.csv');assert not src.duplicated(['season','fixture','code']).any()
 gaps=pd.read_csv(G/'results/remaining_gaps.csv');manifest=pd.read_csv(O/'fixture_manifest.csv')
 master=pd.read_csv(H/'raw/Master.csv');master=master[master.fbref.notna()]
 for code,(old,new,name) in OVERRIDES.items():master.loc[master.code==code,'fbref']=new
 d=source_frame(pd.read_csv(H/'raw/defense.csv'));m=source_frame(pd.read_csv(H/'raw/misc.csv'));keys=['Season_End_Year','home','away','fbref']
 ref=d.merge(m[keys+['Recov']],on=keys,how='left',validate='one_to_one')
 summaries=[];audits=[];controls=[];identities=[];metrics=[]
 for season in ['2022-23','2023-24']:
  f=pd.read_csv(R/f'project/data/{season}_gw.csv');players=pd.read_csv(R/f'project/data/{season}_players.csv')
  if 'position' not in f:f['position']=f.element.map(players.set_index('id').element_type).map({1:'GK',2:'DEF',3:'MID',4:'FWD'})
  f['position']=f.position.replace({'GKP':'GK'});f=f[f.minutes>0].merge(players[['id','code']],left_on='element',right_on='id',validate='many_to_one')
  fixtures=manifest[manifest.season==season].set_index('id')
  f['home']=f.fixture.map(fixtures.home);f['away']=f.fixture.map(fixtures.away);f['expected_team']=f.home.where(f.was_home,f.away)
  j=f.merge(src[src.season==season],on=['fixture','code'],suffixes=('_fpl','_source'),validate='one_to_one')
  j['minute_difference']=j.source_minutes-j.minutes;j['identity_ok']=(j.expected_team==j.source_team)&(j.goals_scored==j.source_goals)&j.source_minutes.gt(0)&j.minute_difference.abs().le(2)
  identities.append(j[['season','fixture','element','code','name_fpl','name_source','position','minutes','source_minutes','minute_difference','goals_scored','source_goals','expected_team','source_team','identity_ok']])
  z=gaps[gaps.season==season].merge(j[['fixture','element','code','match_id','identity_ok','source_minutes','source_goals']+list(MAP)],on=['fixture','element'],how='left',validate='one_to_one')
  for new,old in MAP.items():
   z[old+'_before']=z[old];z[old]=z[old].where(z[old].notna(),z[new].where(z.identity_ok.eq(True)))
  ex,lo,hi,inferred=point_bounds(z);z['defcon_new']=ex;z['lower_new']=lo;z['upper_new']=hi;z['quality_new']='fbref_known_fotmob_missing_provisional'
  z.loc[ex.isna(),'quality_new']='missing';audits.append(z)
  patch=z[ex.notna()][['element','fixture','defcon_new','lower_new','upper_new','quality_new','match_id']]
  baseline=pd.read_csv(G/f'results/{season}_labels.csv');out=baseline.merge(patch,on=['element','fixture'],how='left',validate='one_to_one');changed=out.defcon_new.notna();assert out.loc[changed,'defcon_v2'].isna().all()
  for old,new in [('defcon_v2','defcon_new'),('defcon_lower','lower_new'),('defcon_upper','upper_new'),('quality','quality_new')]:out.loc[changed,old]=out.loc[changed,new]
  known=baseline.defcon_v2.notna();assert out.loc[known,'defcon_v2'].equals(baseline.loc[known,'defcon_v2']);assert out[['element','fixture','minutes','total_points']].equals(baseline[['element','fixture','minutes','total_points']])
  out['historical_plus_defcon']=out.total_points+out.defcon_v2
  out[baseline.columns].rename(columns={'defcon_v2':'defcon'}).to_csv(O/f'{season}_labels.csv',index=False);patch.to_csv(O/f'{season}_patch.csv',index=False)
  active=(out.minutes>0)&(out.position!='GK')
  summaries.append({'season':season,'gap_matches':int(fixtures[fixtures.purpose=='gap'].shape[0]),'active_outfield_rows':int(active.sum()),'missing_before':len(z),'filled':len(patch),'missing_after':int(out.loc[active,'defcon_v2'].isna().sum()),'new_awards':int((patch.defcon_new==2).sum())})
  c=j[(j.purpose=='control')&j.identity_ok&(j.position!='GK')].merge(master[['code','fbref']],on='code',how='left',validate='many_to_one')
  c=c.merge(ref[ref.Season_End_Year==int(season[:4])+1][['home','away','fbref']+COUNTS],on=['home','away','fbref'],how='left',validate='many_to_one')
  c['reference_defcon']=point_bounds(c)[0];c['fotmob_defcon']=point_bounds(c.drop(columns=COUNTS).rename(columns=MAP))[0]
  controls.append(c[['season','fixture','element','code','name_fpl','position']+list(MAP)+COUNTS+['reference_defcon','fotmob_defcon']])
  for new,old in {**MAP,'fotmob_defcon':'reference_defcon'}.items():
   ok=c[new].notna()&c[old].notna();metrics.append({'season':season,'metric':new,'compared':int(ok.sum()),'equal':int((c.loc[ok,new]==c.loc[ok,old]).sum())})
 pd.DataFrame(summaries).to_csv(O/'summary.csv',index=False);pd.concat(audits).to_csv(O/'gap_fill_audit.csv',index=False);pd.concat(identities).to_csv(O/'identity_audit.csv',index=False);pd.concat(controls).to_csv(O/'control_comparison.csv',index=False);pd.DataFrame(metrics).to_csv(O/'control_metrics.csv',index=False)
 print(pd.DataFrame(summaries).to_string(index=False));print(pd.DataFrame(metrics).to_string(index=False))
if __name__=='__main__':run()
