"""Conservative historical FBref pilot. Partial coverage remains missing, never zero."""
from pathlib import Path
import hashlib,json
import pandas as pd
P=Path(__file__).resolve().parent; R=P.parents[1]; OUT=P/'results'
ALIASES={'Brighton & Hove Albion':'Brighton','Manchester City':'Man City','Manchester United':'Man Utd','Newcastle United':'Newcastle','Nottingham Forest':"Nott'm Forest",'Tottenham Hotspur':'Spurs','West Ham United':'West Ham','Wolverhampton Wanderers':'Wolves','Leeds United':'Leeds','Leicester City':'Leicester','Ipswich Town':'Ipswich','Sheffield United':'Sheffield Utd','West Bromwich Albion':'West Brom','Norwich City':'Norwich','Huddersfield Town':'Huddersfield','Cardiff City':'Cardiff','Luton Town':'Luton'}
def award(p,c):
 t=p.map({'DEF':10,'MID':12,'FWD':12});v=2*(c>=t).astype(float);v.loc[t.notna()&c.isna()]=float('nan');return v

def run():
 OUT.mkdir(exist_ok=True)
 assert award(pd.Series(['DEF','DEF','MID','MID','GK']),pd.Series([9,10,11,12,99])).tolist()==[0,2,0,2,0]
 assert pd.isna(award(pd.Series(['DEF']),pd.Series([float('nan')])).iloc[0])
 assert award(pd.Series(['DEF','DEF']),pd.Series([6,6])).sum()==0
 expected=json.loads((P/'source_sha256.json').read_text())
 for name,h in expected.items():
  assert hashlib.sha256((P/'raw'/name).read_bytes()).hexdigest()==h, name
 defense=pd.read_csv(P/'raw/defense.csv');misc=pd.read_csv(P/'raw/misc.csv');master=pd.read_csv(P/'raw/Master.csv',dtype={'fbref':str})
 for d in [defense,misc]:
  d['fbref']=d.Player_Href.str.extract(r'/players/([^/]+)')
  d['home']=d.Home_Team.replace(ALIASES);d['away']=d.Away_Team.replace(ALIASES)
  assert not d.duplicated(['Season_End_Year','home','away','fbref']).any()
 key=['Season_End_Year','home','away','fbref']
 d=defense.merge(misc[key+['Recov']],on=key,how='left',validate='one_to_one')
 master=master[master.fbref.notna() & master.code.notna()].copy()
 assert not master.code.duplicated().any()
 summaries=[]; validation=[]
 for end in range(2020,2027):
  season=f'{end-1}-{str(end)[2:]}'
  f=pd.read_csv(R/f'project/data/{season}_gw.csv');players=pd.read_csv(R/f'project/data/{season}_players.csv')
  if 'position' not in f: f['position']=f.element.map(players.set_index('id').element_type).map({1:'GK',2:'DEF',3:'MID',4:'FWD'})
  if 'team' not in f:
   fixtures=pd.read_csv(R/f'project/data/{season}_fixtures.csv').set_index('id');teams=pd.read_csv(R/f'project/data/{season}_teams.csv').set_index('id')
   teamid=f.fixture.map(fixtures.team_h).where(f.was_home,f.fixture.map(fixtures.team_a));f['team']=teamid.map(teams.name)
  f=f[f.position.isin(['GK','DEF','MID','FWD'])].copy()
  # Separate exact duplicates from conflicting FPL labels.
  dup=f[f.duplicated(['element','fixture'],keep=False)]
  conflicts=dup.groupby(['element','fixture'])[['minutes','total_points']].nunique().max(axis=1)
  badkeys=set(conflicts[conflicts>1].index)
  f=f.drop_duplicates(['element','fixture']).copy()
  f['conflict']=[(e,fi) in badkeys for e,fi in zip(f.element,f.fixture)]
  if pd.api.types.is_numeric_dtype(f.team):
   teams=pd.read_csv(R/f'project/data/{season}_teams.csv');f['team']=f.team.map(teams.set_index('id').name)
  fm=[]
  for fi,g in f.groupby('fixture'):
   h=g.loc[g.was_home,'team'].unique();a=g.loc[~g.was_home,'team'].unique();assert len(h)==len(a)==1
   fm.append({'fixture':fi,'home':h[0],'away':a[0]})
  f=f.merge(pd.DataFrame(fm),on='fixture',validate='many_to_one')
  cross=players[['id','code']].merge(master[['code','fbref']],on='code',how='left',validate='many_to_one')
  assert not cross.id.duplicated().any()
  f=f.merge(cross[['id','fbref']],left_on='element',right_on='id',how='left',validate='many_to_one')
  sd=d[d.Season_End_Year==end]
  j=f.merge(sd[['home','away','fbref','Tkl_Tackles','Sh_Blocks','Blocks_Blocks','Int','Clr','Recov']],on=['home','away','fbref'],how='left',validate='many_to_one',indicator=True)
  j['cbit_shotblocks']=j[['Tkl_Tackles','Sh_Blocks','Int','Clr']].sum(axis=1,min_count=4)
  j['cbit_allblocks']=j[['Tkl_Tackles','Blocks_Blocks','Int','Clr']].sum(axis=1,min_count=4)
  for mode in ['shotblocks','allblocks']:
   count=j[f'cbit_{mode}'].where(j.position=='DEF',j[f'cbit_{mode}']+j.Recov)
   j[f'defcon_{mode}']=award(j.position,count)
   j.loc[(j.minutes==0)|(j.position=='GK'),f'defcon_{mode}']=0
   j.loc[j.conflict,f'defcon_{mode}']=float('nan')
  active=(j.minutes>0)&(j.position!='GK')
  if end==2026:
   official=j.clearances_blocks_interceptions+j.tackles
   official=official.where(j.position=='DEF',official+j.recoveries)
   truth=award(j.position,official)
   for mode in ['shotblocks','allblocks']:
    mask=active&j[f'defcon_{mode}'].notna(); delta=j.loc[mask,f'defcon_{mode}']-truth[mask]
    validation.append({'variant':mode,'rows':int(mask.sum()),'errors':int((delta!=0).sum()),'agreement_pct':float((delta==0).mean()*100),'false_positive':int(((j.loc[mask,f'defcon_{mode}']==2)&(truth[mask]==0)).sum()),'false_negative':int(((j.loc[mask,f'defcon_{mode}']==0)&(truth[mask]==2)).sum())})
  j['quality']='fbref_provisional';j.loc[j.defcon_shotblocks.isna(),'quality']='missing';j.loc[j.minutes==0,'quality']='zero_official_no_minutes';j.loc[j.position=='GK','quality']='zero_ineligible';j.loc[j.conflict,'quality']='conflicting_fpl_label'
  j['historical_plus_defcon']=j.total_points+j.defcon_shotblocks
  j['season']=season
  cols=['season','fixture','element','round','position','minutes','total_points','defcon_shotblocks','historical_plus_defcon','quality']
  # Only new historical seasons: preserve approved 2024/25 and official 2025/26.
  if end<=2024:
   j[cols].sort_values(['fixture','element']).to_csv(OUT/f'{season}_labels.csv',index=False)
  summaries.append({'season':season,'defense_matches':int(defense.loc[defense.Season_End_Year==end,'MatchURL'].nunique()),'recovery_matches':int(misc.loc[misc.Season_End_Year==end,'MatchURL'].nunique()),'active_outfield_rows':int(active.sum()),'matched_source_rows':int((active&(j._merge=='both')).sum()),'usable_defcon_rows':int((active&j.defcon_shotblocks.notna()).sum()),'missing_defcon_rows':int((active&j.defcon_shotblocks.isna()).sum()),'coverage_pct':float(j.loc[active,'defcon_shotblocks'].notna().mean()*100),'conflicting_fpl_keys':len(badkeys),'known_added_points':float(j.loc[active,'defcon_shotblocks'].sum())})
 pd.DataFrame(summaries).to_csv(OUT/'coverage.csv',index=False);pd.DataFrame(validation).to_csv(OUT/'validation.csv',index=False)
 print(pd.DataFrame(summaries).to_string(index=False));print(pd.DataFrame(validation).to_string(index=False))
 inputs=list((P/'raw').glob('*.csv'))
 (OUT/'input_sha256.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in inputs},indent=2)+'\n')
if __name__=='__main__':run()
