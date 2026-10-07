"""Evidence-based repairs and explicit bounds; never fill unknown defcon with zero."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parent;H=P.parent/'historical_fbref';R=P.parents[1];O=P/'results'
sys.path.insert(0,str(H))
from build import ALIASES
OVERRIDES={478969:('f503ea63','3d554589','Hjalmar Ekdal'),444884:('c8387671','b9e1436c','Harvey Elliott'),515024:('42dd1b56','8c3078cd','Luke Harris')}
KEY=['Season_End_Year','home','away','fbref']
COUNTS=['Tkl_Tackles','Sh_Blocks','Int','Clr','Recov']

def source_frame(d):
 d=d.copy();d['fbref']=d.Player_Href.str.extract(r'/players/([^/]+)');d['home']=d.Home_Team.replace(ALIASES);d['away']=d.Away_Team.replace(ALIASES)
 assert not d.duplicated(KEY).any()
 return d

def resolve_duplicates(f,fixtures):
 duplicate=f.duplicated(['element','fixture'],keep=False)
 pieces=[f.loc[~duplicate]];logs=[]
 for (element,fixture),g in f.loc[duplicate].groupby(['element','fixture'],sort=False):
  if len(g)==1:pieces.append(g);continue
  info=fixtures.loc[fixture]
  same_time=pd.to_datetime(g.kickoff_time,utc=True)==pd.to_datetime(info.kickoff_time,utc=True)
  same_gw=g.GW==info.event
  chosen=g[same_time&same_gw]
  assert len(chosen)==1, f'Unresolved duplicate {element}/{fixture}'
  pieces.append(chosen)
  for idx,row in g.iterrows():
   logs.append({'element':element,'fixture':fixture,'GW':row.GW,'minutes':row.minutes,'points':row.total_points,'retained':idx in chosen.index,'reason':'matches official fixture kickoff and event'})
 return pd.concat(pieces,ignore_index=True),logs

def point_bounds(j):
 vals=j[COUNTS].copy();vals.loc[j.position=='DEF','Recov']=0
 assert (vals.fillna(0).values>=0).all()
 known=vals.sum(axis=1); complete=vals.notna().all(axis=1)
 threshold=j.position.map({'DEF':10,'MID':12,'FWD':12})
 eligible=(j.minutes>0)&threshold.notna()
 lo=pd.Series(0.,index=j.index);hi=lo.copy()
 hi.loc[eligible]=2
 lo.loc[eligible&(known>=threshold)]=2
 hi.loc[eligible&complete&(known<threshold)]=0
 exact=lo.where(lo==hi)
 return exact,lo,hi,eligible&~complete&(lo==2)

def tests():
 j=pd.DataFrame({'position':['MID','MID','DEF','GK'],'minutes':[90]*4,'Tkl_Tackles':[3,3,3,np.nan],'Sh_Blocks':[1,1,1,np.nan],'Int':[3,2,3,np.nan],'Clr':[5,5,3,np.nan],'Recov':[np.nan,np.nan,np.nan,np.nan]})
 ex,lo,hi,inferred=point_bounds(j)
 assert ex.iloc[[0,2,3]].tolist()==[2,2,0] and pd.isna(ex.iloc[1])
 assert inferred.tolist()==[True,False,False,False]
 assert lo.iloc[1]==0 and hi.iloc[1]==2
 f=pd.DataFrame({'element':[7,7],'fixture':[275,275],'kickoff_time':['2020-03-11T19:30:00Z','2020-06-17T19:15:00Z'],'GW':[29,39],'minutes':[0,90],'total_points':[0,6]})
 fixtures=pd.DataFrame({'id':[275],'kickoff_time':['2020-06-17T19:15:00Z'],'event':[39]}).set_index('id')
 chosen,logs=resolve_duplicates(f,fixtures)
 assert chosen.GW.tolist()==[39] and sum(x['retained'] for x in logs)==1

def run():
 tests();O.mkdir(exist_ok=True)
 for name,h in json.loads((H/'source_sha256.json').read_text()).items():assert hashlib.sha256((H/'raw'/name).read_bytes()).hexdigest()==h
 d=source_frame(pd.read_csv(H/'raw/defense.csv'));m=source_frame(pd.read_csv(H/'raw/misc.csv'))
 merged=d.merge(m[KEY+['Recov']],on=KEY,how='left',validate='one_to_one')
 master=pd.read_csv(H/'raw/Master.csv');master=master[master.fbref.notna()].copy()
 for code,(old,new,name) in OVERRIDES.items():
  assert master.loc[master.code==code,'fbref'].tolist()==[old]
  evidence=d[(d.fbref==new)&(d.Player==name)]
  assert len(evidence)>0
  master.loc[master.code==code,'fbref']=new
 rows=[];gaps=[];bounds=[];audits=[];patches=[];matches=[]
 for end in range(2020,2025):
  season=f'{end-1}-{str(end)[2:]}';f=pd.read_csv(R/f'project/data/{season}_gw.csv');players=pd.read_csv(R/f'project/data/{season}_players.csv');fixtures=pd.read_csv(R/f'project/data/{season}_fixtures.csv').set_index('id');teams=pd.read_csv(R/f'project/data/{season}_teams.csv').set_index('id')
  if 'position' not in f:f['position']=f.element.map(players.set_index('id').element_type).map({1:'GK',2:'DEF',3:'MID',4:'FWD'})
  f=f[f.position.isin(['GK','DEF','MID','FWD'])].copy()
  f,logs=resolve_duplicates(f,fixtures);audits.extend([dict(season=season,**x) for x in logs])
  # Fixture teams also avoid stale club names around player transfers.
  f['home']=f.fixture.map(fixtures.team_h).map(teams.name);f['away']=f.fixture.map(fixtures.team_a).map(teams.name)
  cross=players[['id','code']].merge(master[['code','fbref']],on='code',how='left',validate='many_to_one')
  f=f.merge(cross,left_on='element',right_on='id',how='left',validate='many_to_one')
  sd=merged[merged.Season_End_Year==end];j=f.merge(sd[['home','away','fbref','Team','Player','MatchURL']+COUNTS],on=['home','away','fbref'],how='left',validate='many_to_one',indicator=True)
  # Verify every corrected identity also belongs to the expected side in this fixture.
  corrected=j.code.isin(OVERRIDES)&(j._merge=='both')
  expected_team=j.home.where(j.was_home,j.away)
  assert (j.loc[corrected,'Team'].replace(ALIASES)==expected_team[corrected]).all()
  exact,lo,hi,inferred=point_bounds(j);active=(j.minutes>0)&(j.position!='GK')
  j['defcon_v2']=exact;j['defcon_lower']=lo;j['defcon_upper']=hi;j['season']=season
  j['quality']='fbref_provisional';j.loc[inferred,'quality']='threshold_proven_with_partial_counts';j.loc[exact.isna(),'quality']='missing';j.loc[j.minutes==0,'quality']='zero_official_no_minutes';j.loc[j.position=='GK','quality']='zero_ineligible'
  j['historical_plus_defcon']=j.total_points+exact
  baseline=pd.read_csv(H/f'results/{season}_labels.csv')
  compare=j.merge(baseline[['element','fixture','defcon_shotblocks','total_points','minutes','quality']],on=['element','fixture'],suffixes=('','_v1'),validate='one_to_one')
  delta=(compare.defcon_v2.fillna(-999)!=compare.defcon_shotblocks.fillna(-999))|(compare.total_points!=compare.total_points_v1)|(compare.minutes!=compare.minutes_v1)|(compare.quality!=compare.quality_v1)
  cols=['season','element','fixture','round','position','minutes','total_points','defcon_v2','historical_plus_defcon','quality','defcon_lower','defcon_upper']
  # Store a compact patch and leave the frozen v1 dataset intact.
  compare.loc[delta,cols+['defcon_shotblocks','total_points_v1','minutes_v1']].to_csv(O/f'{season}_patch.csv',index=False)
  j[cols].to_csv(O/f'{season}_labels.csv',index=False)
  unknown=active&exact.isna();j['reason']=''
  source_matches=set(sd.home+'|'+sd.away)
  j.loc[unknown,'reason']='missing_defensive_fields'
  j.loc[unknown&(j._merge!='both'),'reason']='player_identity_or_source_row'
  j.loc[unknown&~(j.home+'|'+j.away).isin(source_matches),'reason']='defense_match_missing'
  j.loc[unknown&j[COUNTS[:4]].notna().all(axis=1)&j.Recov.isna(),'reason']='recoveries_missing'
  gcols=['season','element','name','fixture','round','position','minutes','home','away','fbref','reason','MatchURL']+COUNTS+['defcon_lower','defcon_upper']
  gaps.append(j.loc[unknown,gcols]);matches.append(j.loc[unknown,['season','fixture','home','away','MatchURL','reason']].drop_duplicates())
  bounds.append(j.loc[active].groupby(['season','element','position'],as_index=False).agg(name=('name','last'),defcon_lower=('defcon_lower','sum'),defcon_upper=('defcon_upper','sum'),unknown_matches=('defcon_v2',lambda s:int(s.isna().sum()))))
  before=baseline[(baseline.minutes>0)&(baseline.position!='GK')]
  rows.append({'season':season,'active_outfield_rows':int(active.sum()),'missing_before':int(before.defcon_shotblocks.isna().sum()),'missing_after':int(unknown.sum()),'covered_pct':100*float(exact[active].notna().mean()),'threshold_rescued':int(inferred.sum()),'resolved_duplicate_keys':len({(x['element'],x['fixture']) for x in logs}),'known_defcon_points':float(exact[active].sum()),'unresolved_player_point_span':int((hi[active]-lo[active]).sum())})
 pd.DataFrame(rows).to_csv(O/'summary.csv',index=False)
 pd.concat(gaps).to_csv(O/'remaining_gaps.csv',index=False);pd.concat(matches).to_csv(O/'remaining_matches.csv',index=False);pd.concat(bounds).to_csv(O/'player_uncertainty.csv',index=False);pd.DataFrame(audits).to_csv(O/'duplicate_resolution.csv',index=False)
 print(pd.DataFrame(rows).to_string(index=False));print(pd.concat(gaps).groupby(['season','reason']).size().to_string())
if __name__=='__main__':run()
