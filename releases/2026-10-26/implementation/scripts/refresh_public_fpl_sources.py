"""Capture official FPL and external56day observations into a fresh release.

No cached response is relabelled. Event screening uses the current official
club roster; missing competitions/summaries remain explicit failures.
"""
import sys,json,gzip,hashlib,urllib.request,concurrent.futures,datetime,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
P=R/'reports/component_freshness_2026_10_26';D=R/'datasets/fpl_external_live_2026_10_26'
from scripts import component_live_fetch as official

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def capture(url,path):
 if path.exists():return json.loads(path.read_text())
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FPLResearch/1.0'}),timeout=40) as response:raw=response.read()
   if raw[:2]==b'\x1f\x8b':raw=gzip.decompress(raw)
   value=json.loads(raw);path.write_bytes(raw);path.with_name(path.name+'.source.json').write_text(json.dumps(dict(url=url,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=sha(path)),indent=2)+'\n');return value
  except Exception:
   if attempt==2:raise
   time.sleep(attempt+1)

def main():
 D.mkdir(exist_ok=True);(D/'raw').mkdir(exist_ok=True);official.P=P/'raw';
 if not (official.P/'receipts.json').exists():official.main()
 boot=json.loads((official.P/'bootstrap.json').read_text());start=datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=56);end=datetime.datetime.now(datetime.timezone.utc);window=start.strftime('%Y%m%d')+'-'+end.strftime('%Y%m%d');clubs={t['name'] for t in boot['teams']}
 import importlib.util
 spec=importlib.util.spec_from_file_location('external_config',R/'datasets/fpl_all_competitions_context_v1/common.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 leagues=list(m.CLUB_LEAGUES)+m.INT_LEAGUES;events={};coverage=[]
 def board(league):
  path=D/'raw'/f'{league}_live.json';url=f'https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates={end.year}&limit=1000';return league,path,capture(url,path)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for league,path,data in pool.map(board,leagues):
   rows=data.get('events',[]);assert len(rows)<1000,(league,'truncated');n=0
   for event in rows:
    at=m.dt(event['date'])
    if not event['status']['type']['completed'] or not start<=at<=end:continue
    isclub=league in m.CLUB_LEAGUES
    if isclub and not any(m.cup.club(v['team']['displayName']) in clubs for v in event['competitions'][0]['competitors']):continue
    key=league+':'+event['id'];events[key]=dict(league=league,label=m.CLUB_LEAGUES.get(league,data.get('leagues',[{}])[0].get('name',league)),event=event,seasons=['2026-27'],competition_type='club_cup' if isclub else 'international');n+=1
   coverage.append(dict(league=league,source_events=len(rows),selected_completed_events=n,status='ok',raw_file=str(path.relative_to(R))))
 (D/'events.json').write_text(json.dumps(events));(D/'source_coverage.json').write_text(json.dumps(coverage,indent=2));print('Fresh scoreboards',len(coverage),'selected completed events',len(events),flush=True)
 def summary(item):
  key,z=item;eid=z['event']['id'];path=D/'raw'/f'{z["league"]}_{eid}_summary.json';capture(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{z["league"]}/summary?event={eid}',path);return dict(key=key,raw_file=str(path.relative_to(R)),error=None)
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for result in pool.map(summary,events.items()):
   results.append(result)
   if len(results)%100==0:print('Fresh summaries',len(results),'/',len(events),flush=True)
 (D/'summary_sources.json').write_text(json.dumps(results,indent=2));(D/'capture.json').write_text(json.dumps(dict(start=start.isoformat(),end=end.isoformat(),captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),leagues=len(coverage),completed_events=len(events),all_competitions_complete=False),indent=2)+'\n');print('Official and external capture complete',flush=True)
if __name__=='__main__':main()
