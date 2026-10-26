"""Recover PL fixture versions strictly preceding each historical forecast."""
import concurrent.futures,urllib.parse,urllib.request,json,gzip,sys
from common import *
from fetch import fetch
class Redirect(urllib.request.HTTPRedirectHandler):
 http_error_308=urllib.request.HTTPRedirectHandler.http_error_302
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  return super().redirect_request(req,fp,302 if code==308 else code,msg,headers,newurl)
OPENER=urllib.request.build_opener(Redirect)
def payload(season,commit):
 name=f'{season}_{commit["sha"]}.csv'
 for folder,filename in [(R/'FPL_training_dataset/research/current/calendar_audit/portable',name),(R/'reports/calendar_dataset_2026_10_16/raw','old_'+name)]:
  if (folder/filename).exists():return folder/filename
 path=P/'raw'/('calendar_'+name)
 if not path.exists():
  url=f'https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/{commit["sha"]}/data/{season}/fixtures.csv'
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FPLResearch'}),timeout=45) as r:data=r.read()
  path.write_bytes(data);path.with_name(path.name+'.source.json').write_text(json.dumps(dict(url=url,fetched_at=datetime.now(timezone.utc).isoformat(),sha256=sha(path)),indent=2))
 return path
def main():
 if len(sys.argv)>1 and sys.argv[1]=='primary':
  sources={
   'lfc2019':('2019-08-29','https://www.liverpoolfc.com/news/first-team/362666-liverpool-s-champions-league-fixture-details-confirmed'),
   'lfc2020qf':('2021-03-19','https://www.liverpoolfc.com/news/first-team/429170-champions-league-real-madrid-fixture-dates'),
   'lfc2021':('2021-08-27','https://www.liverpoolfc.com/amp/news/first-team/441710-liverpool-s-champions-league-fixture-dates-confirmed'),
   'city2022':('2022-08-27','https://www.mancity.com/news/mens/manchester-city-uefa-champions-league-fixture-confirmation-63797184'),
   'lfc2023':('2023-09-02','https://www.liverpoolfc.com/news/liverpools-europa-league-fixture-schedule-confirmed'),
   'ucl2024':('2024-08-31','https://editorial.uefa.com/resources/0290-1bbe0f238404-c5dbaf60ad4d-1000/uefa_champions_league_2024-25_league_phase_draw_results_calendar_by_pot.pdf')}
  for key,(published,url) in sources.items():
   ext='pdf' if '.pdf' in url else 'html';path=P/'raw'/f'primary_{key}.{ext}'
   if not path.exists():
    try:
     with OPENER.open(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 FPLResearch'}),timeout=45) as r:data=r.read()
    except Exception as error:
     print(key,'unavailable',str(error),flush=True);continue
    if data[:2]==b'\x1f\x8b':data=gzip.decompress(data)
    path.write_bytes(data);path.with_name(path.name+'.source.json').write_text(json.dumps(dict(url=url,publication_date=published,fetched_at=datetime.now(timezone.utc).isoformat(),sha256=sha(path)),indent=2))
   print(key,path.stat().st_size,flush=True)
  (P/'primary_calendar_sources.json').write_text(json.dumps(sources,indent=2));return
 seasons,rounds,_=config();commits={};errors=[]
 for season,z in seasons.items():
  allrows=[]
  for page in range(1,5):
   q=urllib.parse.urlencode(dict(path=f'data/{season}/fixtures.csv',since=f'{season[:4]}-01-01T00:00:00Z',until=z['end'].isoformat(),per_page=100,page=page))
   try:d=fetch('https://api.github.com/repos/vaastav/Fantasy-Premier-League/commits?'+q,P/'raw'/f'calendar_commits_{season}_{page}.json')
   except Exception as e:errors.append(dict(season=season,error=str(e)));break
   allrows+=d
   if len(d)<100:break
  commits[season]=[dict(sha=c['sha'],source_time=max(c['commit']['author']['date'],c['commit']['committer']['date'])) for c in allrows]
  print('Calendar commits',season,len(allrows),flush=True)
 (P/'calendar_commits.json').write_text(json.dumps(commits,indent=2))
 selected=[];needed={}
 for (season,gw),kick in sorted(rounds.items()):
  at=kick-timedelta(minutes=90);valid=[c for c in commits[season] if dt(c['source_time'])<at];chosen=max(valid,key=lambda c:dt(c['source_time'])) if valid else None
  row=dict(season=season,round=gw,forecast_at=at.isoformat(),source_sha=chosen['sha'] if chosen else '',source_time=chosen['source_time'] if chosen else '',raw_file='',status='pending' if chosen else 'no_pre_origin_fixture_snapshot')
  selected.append(row)
  if chosen:needed[(season,chosen['sha'])]=chosen
 paths={}
 def get(item):
  (season,digest),c=item
  try:return (season,digest),str(payload(season,c).relative_to(R)),None
  except Exception as e:return (season,digest),'',str(e)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for key,path,error in pool.map(get,needed.items()):
   paths[key]=path
   if error:errors.append(dict(season=key[0],sha=key[1],error=error))
 for row in selected:
  if row['source_sha']:
   row['raw_file']=paths[(row['season'],row['source_sha'])];row['status']='ok' if row['raw_file'] else 'snapshot_fetch_failed'
 (P/'calendar_origin_selection.json').write_text(json.dumps(selected,indent=2));(P/'calendar_fetch_errors.json').write_text(json.dumps(errors,indent=2));print('Calendar origins',len(selected),'available',sum(r['status']=='ok' for r in selected),'errors',len(errors),flush=True)
if __name__=='__main__':main()
