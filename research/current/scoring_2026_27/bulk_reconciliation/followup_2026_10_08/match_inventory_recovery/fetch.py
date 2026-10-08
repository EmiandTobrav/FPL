from pathlib import Path
import pandas as pd,json,hashlib,urllib.request,concurrent.futures
P=Path(__file__).resolve().parent; S=P.parent
r=pd.read_csv(S/'tackle_event_recovery_v2/results/remaining_fields.csv.gz',low_memory=False);p=pd.read_csv(S/'tackle_event_recovery_v2/inputs/players.csv.gz');t=pd.read_csv(S/'season_conservation/inputs/full_team_totals.csv');g=pd.read_csv(S/'tackle_event_recovery_v2/team_gates.csv').dropna(subset=['match_id','recipient_team_id'])
x=r[r.field.eq('times_tackled')&r.status.eq('missing_data')].dropna(subset=['match_id','player_id']).merge(p[['season','fixture','player_id','team_id','totalContest']],on=['season','fixture','player_id'],how='inner',validate='one_to_one');x=x.merge(g[['match_id','recipient_team_id','complete']],left_on=['match_id','team_id'],right_on=['match_id','recipient_team_id'],how='inner',validate='many_to_one')
req=x[x.complete.eq(True)&x.totalContest.isna()][['season','fixture','match_id']].drop_duplicates().merge(t[['season','fixture','pulse_id']].drop_duplicates(),on=['season','fixture']);req['scope']='target'
control=t[t.season.eq('2023-24')].sort_values('fixture')[['season','fixture','match_id','pulse_id']].drop_duplicates().head(30);control['scope']='regression'
req=pd.concat([req,control],ignore_index=True);req.to_csv(P/'inputs/target_fixtures.csv',index=False)
def fetch(row):
 pid=int(row.pulse_id);path=P/'inputs/primary'/f'{pid}.json';url=f'https://footballapi.pulselive.com/football/stats/match/{pid}'
 if not path.exists():
  raw=urllib.request.urlopen(urllib.request.Request(url,headers={'Origin':'https://www.premierleague.com','User-Agent':'FPL-research/1.0'}),timeout=45).read();d=json.loads(raw);assert d['entity']['id']==pid;path.write_bytes(raw)
 raw=path.read_bytes();assert json.loads(raw)['entity']['id']==pid
 return dict(file=str(path.relative_to(P)),url=url,sha256=hashlib.sha256(raw).hexdigest(),pulse_id=pid,scope=row.scope)
records=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for rec in pool.map(fetch,req.itertuples()):
  records.append(rec)
  if len(records)%40==0: print('verified',len(records),flush=True)
(P/'inputs/sources.json').write_text(json.dumps(records,indent=2)+'\n');print('Complete',len(records),flush=True)
