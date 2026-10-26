"""Fetch missing historical scoreboards and summaries; cache and source hashes."""
import concurrent.futures,gzip,json,time,urllib.request,urllib.error,sys
from datetime import datetime,timezone
from common import *
(P/'raw').mkdir(exist_ok=True)
def fetch(url,path):
 if path.exists():return json.loads(path.read_text())
 for attempt in range(4):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FPLResearch/1.0'}),timeout=45) as r:data=r.read()
   if data[:2]==b'\x1f\x8b':data=gzip.decompress(data)
   parsed=json.loads(data);path.write_bytes(data);path.with_name(path.name+'.source.json').write_text(json.dumps(dict(url=url,fetched_at=datetime.now(timezone.utc).isoformat(),sha256=sha(path)),indent=2));return parsed
  except urllib.error.HTTPError as e:
   if e.code in [400,404] or attempt==3:raise
   time.sleep(2*(attempt+1))
  except (urllib.error.URLError,TimeoutError):
   if attempt==3:raise
   time.sleep(2*(attempt+1))
def main():
 if len(sys.argv)>1 and sys.argv[1]=='profiles':
  ids=json.loads((P/'profile_candidates.json').read_text())
  def get(pid):
   try:fetch(f'https://sports.core.api.espn.com/v2/sports/soccer/leagues/eng.1/athletes/{pid}?lang=en&region=us',locate(f'athlete_{pid}.json'));return None
   except Exception as e:return dict(id=pid,error=str(e))
  with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:errors=[x for x in pool.map(get,ids) if x]
  (P/'profile_errors.json').write_text(json.dumps(errors,indent=2));print('Profiles',len(ids),'errors',len(errors),flush=True);return
 seasons,rounds,members=config();jobs=[(league,year) for league in list(CLUB_LEAGUES)+INT_LEAGUES for year in range(2019,2027)]
 def board(job):
  league,year=job;path=locate(f'{league}_{year}.json')
  try:
   d=fetch(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates={year}&limit=1000',path)
   return league,year,path,d,None
  except Exception as e:return league,year,path,None,str(e)
 events={};coverage=[];rawrefs={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for n,(league,year,path,d,error) in enumerate(pool.map(board,jobs),1):
   es=d.get('events',[]) if d else [];assert len(es)<1000,(league,year,'potential truncated response')
   chosen=0;label=(d or {}).get('leagues',[{}])[0].get('name',league)
   for e in es:
    if not e['status']['type']['completed']:continue
    t=dt(e['date']);isclub=league in CLUB_LEAGUES
    if isclub:
     ey=e.get('season',{}).get('year');season=f'{ey}-{str(ey+1)[-2:]}' if isinstance(ey,int) else None
     ss=[season] if season in seasons and seasons[season]['history_start']<=t<(datetime(2020,9,1,tzinfo=timezone.utc) if season=='2019-20' else seasons[season]['end']) and any(cup.club(c['team']['displayName']) in seasons[season]['clubs'] for c in e['competitions'][0]['competitors']) else []
    else:ss=[s for s,z in seasons.items() if z['history_start']<=t<z['end']]
    if not ss:continue
    key=league+':'+e['id'];chosen+=1;events[key]=dict(league=league,label=CLUB_LEAGUES.get(league,label),event=e,seasons=ss,competition_type='club_cup' if isclub else 'international')
   rawrefs[str(path.relative_to(R))]=sha(path) if path.exists() else None
   coverage.append(dict(league=league,year=year,source_events=len(es),selected_completed_events=chosen,status='ok' if not error else error,raw_file=str(path.relative_to(R))))
   if n%24==0:print('Scoreboards',n,'/',len(jobs),'selected',len(events),flush=True)
 (P/'events.json').write_text(json.dumps(events));(P/'source_coverage.json').write_text(json.dumps(coverage,indent=2));(P/'scoreboard_input_hashes.json').write_text(json.dumps(rawrefs,indent=2))
 def summary(item):
  key,z=item;eid=z['event']['id'];league=z['league'];path=locate(f'{league}_{eid}_summary.json')
  try:fetch(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary?event={eid}',path);return dict(key=key,raw_file=str(path.relative_to(R)),error=None)
  except Exception as e:return dict(key=key,raw_file=str(path.relative_to(R)),error=str(e))
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for n,result in enumerate(pool.map(summary,events.items()),1):
   results.append(result)
   if n%100==0 or n==len(events):
    (P/'summary_fetch_progress.json').write_text(json.dumps(dict(completed=n,total=len(events),errors=sum(bool(r['error']) for r in results))))
    print('Summaries',n,'/',len(events),'errors',sum(bool(r['error']) for r in results),flush=True)
 (P/'summary_sources.json').write_text(json.dumps(results,indent=2))
if __name__=='__main__':main()
