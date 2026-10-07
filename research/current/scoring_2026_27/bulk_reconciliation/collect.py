"""Bounded match-total acquisition, with hashes and resumable raw responses."""
from pathlib import Path
import argparse,json,hashlib,time,urllib.request,urllib.error,threading,gzip
from concurrent.futures import ThreadPoolExecutor,as_completed
import pandas as pd
P=Path(__file__).resolve().parent;S=P.parent
SEASONS={'2019-20':274,'2020-21':363,'2021-22':418,'2022-23':489,'2023-24':578,'2024-25':719}
STOP=threading.Event();LOCK=threading.Lock();NEXT=0.
FIELDS=['total_tackle','won_tackle','was_fouled','fk_foul_won','ontarget_scoring_att','clearance_off_line','total_scoring_att','saves','goals','own_goals','interception','total_clearance','outfielder_block']
def get(url,path):
 global NEXT
 if path.exists():return path.read_bytes()
 packed=path.with_suffix('.json.gz')
 if packed.exists():return gzip.decompress(packed.read_bytes())
 with LOCK:
  delay=max(0,NEXT-time.monotonic());NEXT=max(NEXT,time.monotonic())+.5
 if STOP.wait(delay):raise RuntimeError('Stopped after access/rate response')
 try:raw=urllib.request.urlopen(url,timeout=30).read()
 except urllib.error.HTTPError as e:
  if e.code in [401,403,429]:STOP.set()
  raise
 json.loads(raw)
 temp=path.with_suffix('.tmp');temp.write_bytes(raw);temp.replace(path);return raw

def plans():
 rawdir=P/'inputs/catalogs';rawdir.mkdir(exist_ok=True)
 coverage=pd.read_csv(S/'assist_reconciliation/fixture_coverage.csv')
 fixtures=[]
 for season,cid in SEASONS.items():
  url=f'https://footballapi.pulselive.com/football/fixtures?compSeasons={cid}&page=0&pageSize=500&altIds=true'
  data=json.loads(get(url,rawdir/f'{season}.json'))
  if data['pageInfo']['numPages']!=1:raise ValueError('Incomplete fixture catalog')
  bycode={int(x['altIds']['opta'].lstrip('g')):x for x in data['content'] if x.get('altIds',{}).get('opta')}
  fpl=pd.read_csv(S.parent/'project/data'/f'{season}_fixtures.csv.gz').set_index('id')
  for r in coverage[coverage.season.eq(season)].to_dict('records'):
   r['home_score']=int(fpl.loc[r['fixture'],'team_h_score']);r['away_score']=int(fpl.loc[r['fixture'],'team_a_score'])
   x=bycode[int(r['fixture_code'])]
   if [t['score'] for t in x['teams']]!=[r['home_score'],r['away_score']]:raise ValueError('Score identity mismatch')
   if pd.to_datetime(x['kickoff']['millis'],unit='ms',utc=True).strftime('%Y-%m-%d')!=r['date']:raise ValueError('Date mismatch')
   fixtures.append({**r,'pulse_id':int(x['id']),'home_primary_id':int(x['teams'][0]['team']['id']),'away_primary_id':int(x['teams'][1]['team']['id'])})
 d=pd.DataFrame(fixtures).sort_values(['season','date','fixture'])
 d.to_csv(P/'collection_plan.csv',index=False)
 pilot=pd.concat([g.head(2) for _,g in d.groupby('season')])
 pilot.to_csv(P/'pilot_plan.csv',index=False)
 # Later dated fixtures are reserved before outcomes and not used for method development.
 holdout=pd.concat([g.tail(2) for _,g in d.groupby('season')]);holdout.to_csv(P/'holdout_plan.csv',index=False)
 print('planned',len(d),'pilot',len(pilot),'holdout',len(holdout),flush=True)

def normalize(raw,row):
 d=json.loads(raw);entity=d['entity']
 if int(entity['id'])!=int(row['pulse_id']) or entity['status']!='C':raise ValueError('Fixture identity/status mismatch')
 if [int(t['team']['id']) for t in entity['teams']]!=[int(row['home_primary_id']),int(row['away_primary_id'])]:raise ValueError('Team mismatch')
 if [t['score'] for t in entity['teams']]!=[row['home_score'],row['away_score']]:raise ValueError('Score mismatch')
 result=[]
 for side in ['home','away']:
  tid=str(int(row[side+'_primary_id']));stats=d['data'][tid]['M']
  if len({x['name'] for x in stats})!=len(stats):raise ValueError('Duplicate stat')
  stats={x['name']:x['value'] for x in stats}
  result.append({**row,'side':side,'primary_team_id':int(tid),**{f:stats.get(f) for f in FIELDS}})
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['plan','pilot','holdout','full']);args=ap.parse_args()
 if args.stage=='plan':plans();return
 plan=pd.read_csv(P/({'pilot':'pilot_plan.csv','holdout':'holdout_plan.csv','full':'collection_plan.csv'}[args.stage]))
 root=P/'inputs/matches';root.mkdir(exist_ok=True)
 records=[];sources=[];errors=[]
 def fetch(row):
  url=f"https://footballapi.pulselive.com/football/stats/match/{int(row['pulse_id'])}"
  path=root/f"{int(row['pulse_id'])}.json"
  raw=get(url,path);values=normalize(raw,row)
  if not path.exists() and path.with_suffix('.json.gz').exists():path=path.with_suffix('.json.gz')
  return values,dict(url=url,file=str(path.relative_to(P)),sha256=hashlib.sha256(raw).hexdigest(),season=row['season'],fixture=row['fixture'])
 # Only four jobs outstanding; stop submitting after access errors.
 with ThreadPoolExecutor(max_workers=4) as pool:
  rows=iter(plan.to_dict('records'));active={}
  def submit():
   r=next(rows,None)
   if r is not None and not STOP.is_set():active[pool.submit(fetch,r)]=r
  for _ in range(4):submit()
  while active:
   done=next(as_completed(active));row=active.pop(done)
   try:
    values,src=done.result();records.extend(values);sources.append(src)
   except Exception as e:errors.append(dict(season=row['season'],fixture=row['fixture'],error=str(e)))
   if len(sources)%100==0 and sources:print('completed',len(sources),'errors',len(errors),flush=True)
   submit()
 pd.DataFrame(records).sort_values(['season','fixture','side']).to_csv(P/f'{args.stage}_team_totals.csv',index=False)
 (P/f'{args.stage}_sources.json').write_text(json.dumps(sorted(sources,key=lambda x:(x['season'],x['fixture'])),indent=2)+'\n')
 (P/f'{args.stage}_errors.json').write_text(json.dumps(errors,indent=2)+'\n')
 print(args.stage,'complete',len(sources),'errors',len(errors),flush=True)
 if errors:raise SystemExit(1)
if __name__=='__main__':main()
