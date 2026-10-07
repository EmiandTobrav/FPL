"""Targeted primary-source diagnostic, not an unbiased error-rate estimate."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import pandas as pd
import json,sys,hashlib,urllib.request
P=Path(__file__).resolve().parent;R=P.parents[1];O=P/'results';RAW=P/'raw';H=P.parent/'historical_fbref';OLD=P.parent/'missing_2021'
sys.path.insert(0,str(P.parent/'gap_repair'));sys.path.insert(0,str(H))
from repair import source_frame,OVERRIDES,point_bounds,COUNTS

def spaced(frame,n):
 n=min(n,len(frame));return frame.iloc[[i*(len(frame)-1)//max(n-1,1) for i in range(n)]]

def manifest():
 c=pd.read_csv(OLD/'results/control_comparison.csv').sort_values(['fixture','code'])
 flips=c[c.reference_defcon!=c.fotmob_defcon];others=c[(c.Clr!=c.clearances)&~c.index.isin(flips.index)]
 z=pd.concat([flips,spaced(others,16),spaced(c[c.Clr==c.clearances],10)]).copy();z['season']='2021-22';z['purpose']='historical_clearance_diagnostic'
 z=z.rename(columns={'name_fpl':'name','Clr':'fbref_clearances','clearances':'fotmob_clearances'})
 f=pd.read_csv(R/'project/data/2021-22_gw.csv');z=z.merge(f[['fixture','element','minutes','goals_scored']],on=['fixture','element'],validate='one_to_one')
 z=z[['season','fixture','element','code','name','position','minutes','goals_scored','purpose','fbref_clearances','fotmob_clearances']]
 f=pd.read_csv(R/'project/data/2025-26_gw.csv');players=pd.read_csv(R/'project/data/2025-26_players.csv');fixtures=pd.read_csv(R/'project/data/2025-26_fixtures.csv').set_index('id');teams=pd.read_csv(R/'project/data/2025-26_teams.csv').set_index('id')
 f['position']=f.position.replace({'GKP':'GK'});f=f[(f.minutes>0)&(f.position!='GK')].merge(players[['id','code']],left_on='element',right_on='id',validate='many_to_one')
 f['home']=f.fixture.map(fixtures.team_h).map(teams.name);f['away']=f.fixture.map(fixtures.team_a).map(teams.name)
 master=pd.read_csv(H/'raw/Master.csv');master=master[master.fbref.notna()]
 for code,(old,new,name) in OVERRIDES.items():master.loc[master.code==code,'fbref']=new
 d=source_frame(pd.read_csv(H/'raw/defense.csv'));m=source_frame(pd.read_csv(H/'raw/misc.csv'));keys=['Season_End_Year','home','away','fbref']
 d=d.merge(m[keys+['Recov']],on=keys,how='left',validate='one_to_one');d=d[d.Season_End_Year==2026]
 f=f.merge(master[['code','fbref']],on='code',how='left',validate='many_to_one').merge(d[['home','away','fbref']+COUNTS],on=['home','away','fbref'],how='inner',validate='many_to_one')
 f['fbref_defcon_count']=f[['Tkl_Tackles','Sh_Blocks','Int','Clr']].sum(axis=1,min_count=4)+f.Recov.where(f.position.isin(['MID','FWD']),0)
 f['reference_defcon']=point_bounds(f)[0];threshold=f.position.map({'DEF':10,'MID':12,'FWD':12});f['official_award']=2*(f.defensive_contribution>=threshold)
 f=f[f.reference_defcon.notna()].sort_values(['fixture','code'])
 bad=f[f.reference_defcon!=f.official_award].copy();bad['purpose']='2025_official_award_disagreement'
 good=spaced(f[f.reference_defcon==f.official_award],10).copy();good['purpose']='2025_matched_control'
 n=pd.concat([bad,good]);n['season']='2025-26';n=n.rename(columns={'Clr':'fbref_clearances'})
 n=n[['season','fixture','element','code','name','position','minutes','goals_scored','purpose','fbref_clearances','clearances_blocks_interceptions','defensive_contribution','tackles','recoveries','official_award','reference_defcon','fbref_defcon_count']]
 z=pd.concat([z,n],ignore_index=True)
 for season in z.season.unique():
  idx=z.season==season;fixtures=pd.read_csv(R/f'project/data/{season}_fixtures.csv').set_index('id');z.loc[idx,'pulse_id']=z.loc[idx,'fixture'].map(fixtures.pulse_id)
 maps={}
 for season,file in [('2021-22',OLD/'raw/pl_recoveries_season.json'),('2025-26',RAW/'pl_recoveries_2025.json')]:
  data=json.loads(file.read_text());maps[season]={int(x['owner']['altIds']['opta'].lstrip('p')):int(x['owner']['id']) for x in data['stats']['content']}
 z['pl_player_id']=[maps[s].get(int(c)) for s,c in zip(z.season,z.code)];assert z[['pulse_id','pl_player_id']].notna().all().all();z[['pulse_id','pl_player_id']]=z[['pulse_id','pl_player_id']].astype(int)
 z.to_csv(O/'clearance_manifest.csv',index=False);return z

def run():
 z=pd.read_csv(O/'clearance_manifest.csv') if (O/'clearance_manifest.csv').exists() else manifest();rows=[];sources=[]
 expected={x['file']:x['sha256'] for x in json.loads((O/'clearance_sources.json').read_text())} if (O/'clearance_sources.json').exists() else {}
 def fetch(row):
  pid=row['pl_player_id'];fixture=row['pulse_id'];url=f'https://footballapi.pulselive.com/football/stats/player/{pid}?fixtures={fixture}';path=RAW/f'pl_{pid}_{fixture}.json'
  if not path.exists():
   with urllib.request.urlopen(url,timeout=25) as r:path.write_bytes(r.read())
  b=path.read_bytes()
  if path.name in expected:assert hashlib.sha256(b).hexdigest()==expected[path.name], 'Official source revision changed; review required'
  d=json.loads(b);assert int(d['entity']['id'])==pid
  stats={x['name']:x['value'] for x in d['stats']};assert stats.get('appearances')==1
  row['pl_minutes']=stats.get('mins_played');row['minute_ok']=abs(row['pl_minutes']-row['minutes'])<=2
  row['goals_ok']=stats.get('goals',0)==row['goals_scored']
  for key in ['total_clearance','effective_clearance','blocked_cross','effective_blocked_cross','outfielder_block','interception','total_tackle','ball_recovery']:
   row['pl_'+key]=stats.get(key,0);row[key+'_present']=key in stats
  row['pl_cbi']=row['pl_total_clearance']+row['pl_outfielder_block']+row['pl_interception']
  row['pl_defcon_count']=row['pl_cbi']+row['pl_total_tackle']+(row['pl_ball_recovery'] if row['position'] in ['MID','FWD'] else 0)
  row['pl_award']=2*int(row['pl_defcon_count']>=({'DEF':10,'MID':12,'FWD':12}[row['position']]))
  if row['season']=='2025-26':
   row['clearance_only_count']=row['fbref_defcon_count']-row['fbref_clearances']+row['pl_total_clearance']
   row['clearance_only_award']=2*int(row['clearance_only_count']>=({'DEF':10,'MID':12,'FWD':12}[row['position']]))
  return row,{'season':row['season'],'fixture':row['fixture'],'code':row['code'],'url':url,'file':path.name,'sha256':hashlib.sha256(b).hexdigest()}
 with ThreadPoolExecutor(max_workers=2) as pool:
  jobs=[pool.submit(fetch,r) for r in z.to_dict('records')]
  for i,job in enumerate(as_completed(jobs),1):
   try:a,b=job.result()
   except Exception:
    for other in jobs:other.cancel()
    raise
   rows.append(a);sources.append(b)
   if i%10==0:print(i,'/',len(jobs),flush=True)
 a=pd.DataFrame(rows).sort_values(['season','fixture','code']);a.to_csv(O/'clearance_audit.csv',index=False)
 (O/'clearance_sources.json').write_text(json.dumps(sorted(sources,key=lambda x:(x['season'],x['fixture'],x['code'])),indent=2)+'\n')
 summaries=[]
 for purpose,g in a.groupby('purpose'):
  n=g[g.season=='2025-26'];h=g[g.season=='2021-22']
  summaries.append({'purpose':purpose,'n':len(g),'minutes_ok':int(g.minute_ok.sum()),'goals_ok':int(g.goals_ok.sum()),'fbref_equals_pl_clearance':int((g.fbref_clearances==g.pl_total_clearance).sum()),'fbref_equals_clearance_plus_blocked_cross':int((g.fbref_clearances==g.pl_total_clearance+g.pl_blocked_cross).sum()),'fotmob_equals_pl_clearance':int((h.fotmob_clearances==h.pl_total_clearance).sum()),'official_cbi_equal':int((n.clearances_blocks_interceptions==n.pl_cbi).sum()),'official_count_equal':int((n.defensive_contribution==n.pl_defcon_count).sum()),'official_award_equal':int((n.official_award==n.pl_award).sum()),'clearance_only_award_equal':int((n.official_award==n.clearance_only_award).sum())})
 pd.DataFrame(summaries).to_csv(O/'clearance_summary.csv',index=False);print(pd.DataFrame(summaries).to_string(index=False))
if __name__=='__main__':run()
