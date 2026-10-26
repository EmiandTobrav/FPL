"""Select archived sources by pre-origin metadata, never by player outcomes."""
import concurrent.futures,urllib.request,urllib.parse,urllib.error,time,sys
from common import *
(P/'raw').mkdir(exist_ok=True)
def get(url,path,binary=False):
 if path.exists():return path.read_bytes() if binary else json.loads(path.read_text())
 for attempt in range(4):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FPL-availability-history-research'}),timeout=45) as response:data=response.read();headers=dict(response.headers)
   path.write_bytes(data);path.with_name(path.name+'.source.json').write_text(json.dumps(dict(url=url,retrieved_at=datetime.now(timezone.utc).isoformat(),sha256=sha(path),headers=headers),indent=2));return data if binary else json.loads(data)
  except urllib.error.HTTPError as e:
   if e.code in [400,401,403,404,429] or attempt==3:raise
   time.sleep(2*(attempt+1))
  except (urllib.error.URLError,TimeoutError):
   if attempt==3:raise
   time.sleep(2*(attempt+1))
def main():
 origin_rows=origins();(P/'origin_lock.json').write_text(json.dumps(origin_rows,indent=2))
 tree=get('https://api.github.com/repos/Randdalf/fplcache/git/trees/main?recursive=1',P/'raw/tree.json');assert not tree['truncated'];paths=[]
 for v in tree['tree']:
  parts=v['path'].split('/')
  if len(parts)==5 and parts[0]=='cache' and parts[-1].endswith('.json.xz'):
   try:t=datetime(int(parts[1]),int(parts[2]),int(parts[3]),int(parts[4][:2]),int(parts[4][2:4]),tzinfo=timezone.utc);paths.append((t,v))
   except ValueError:pass
 earliest=min(t for t,v in paths);selected=[];errors=[];known={(r['season'],r['gw']):r for r in json.loads((OLD/'full_selected_snapshots.json').read_text())}
 for season in sorted({r['season'] for r in origin_rows}):
  oo=[r for r in origin_rows if r['season']==season];need=[o for o in oo if (season,o['round']) not in known or (known[(season,o['round'])].get('payload_url') and max(dt(known[(season,o['round'])]['author_at']),dt(known[(season,o['round'])]['committer_at']))>=dt(o['selection_cutoff']))]
  commits=[]
  if need and dt(oo[-1]['selection_cutoff'])>earliest:
   since=max(dt(need[0]['selection_cutoff'])-timedelta(days=1),earliest-timedelta(days=1));until=dt(need[-1]['selection_cutoff'])
   for page in range(1,20):
    query=urllib.parse.urlencode(dict(path='cache',since=since.isoformat(),until=until.isoformat(),per_page=100,page=page));path=P/'raw'/f'commits_{season}_{page}.json'
    try:batch=get('https://api.github.com/repos/Randdalf/fplcache/commits?'+query,path)
    except Exception as e:errors.append(dict(season=season,kind='bootstrap_metadata',error=str(e)));break
    assert isinstance(batch,list);commits+=batch
    if len(batch)<100:break
  for o in oo:
   key=season,o['round'];existing=known.get(key);cutoff=dt(o['selection_cutoff'])
   if existing and existing.get('payload_url') and max(dt(existing['author_at']),dt(existing['committer_at']))<cutoff:
    selected.append(dict(o,format='bootstrap',source_time=max(existing['author_at'],existing['committer_at']),source_file=str((OLD/'raw'/f'{season}_gw{o["round"]}.json.xz').relative_to(R)),source_url=existing['payload_url'],commit=existing['commit'],blob_sha=existing['blob_sha'],status='selected_existing_pre_origin'));continue
   valid=[c for c in commits if max(dt(c['commit']['author']['date']),dt(c['commit']['committer']['date']))<cutoff]
   if valid:
    c=max(valid,key=lambda c:max(dt(c['commit']['author']['date']),dt(c['commit']['committer']['date'])));at=max(dt(c['commit']['author']['date']),dt(c['commit']['committer']['date']));candidates=[(t,v) for t,v in paths if 0<=(at-t).total_seconds()<=120]
    if candidates:
     nominal,v=max(candidates,key=lambda z:z[0]);url=f'https://raw.githubusercontent.com/Randdalf/fplcache/{c["sha"]}/{v["path"]}'
     selected.append(dict(o,format='bootstrap',source_time=at.isoformat(),source_file=str((P/'raw'/f'{season}_gw{o["round"]}.json.xz').relative_to(R)),source_url=url,commit=c['sha'],blob_sha=v['sha'],status='selected_new_pre_origin'));continue
   selected.append(dict(o,format='none',source_time='',source_file='',source_url='',commit='',blob_sha='',status='no_pre_origin_bootstrap_source'))
  print('Bootstrap selection',season,sum(r['format']=='bootstrap' for r in selected if r['season']==season),'/',len(oo),flush=True)
 # Older seasons: a dated complete player table may supply status/roster, but
 # without event metadata we do not guess which chance field targets the round.
 for season in sorted({r['season'] for r in selected if r['format']=='none'}):
  oo=[r for r in selected if r['season']==season and r['format']=='none'];commits=[]
  for page in range(1,5):
   query=urllib.parse.urlencode(dict(path=f'data/{season}/players_raw.csv',until=oo[-1]['selection_cutoff'],per_page=100,page=page))
   try:batch=get('https://api.github.com/repos/vaastav/Fantasy-Premier-League/commits?'+query,P/'raw'/f'player_commits_{season}_{page}.json')
   except Exception as e:errors.append(dict(season=season,kind='player_csv_metadata',error=str(e)));break
   commits+=batch
   if len(batch)<100:break
  for o in oo:
   valid=[c for c in commits if max(dt(c['commit']['author']['date']),dt(c['commit']['committer']['date']))<dt(o['selection_cutoff'])]
   if not valid:continue
   c=max(valid,key=lambda c:max(dt(c['commit']['author']['date']),dt(c['commit']['committer']['date'])));o.update(format='players_csv',source_time=max(c['commit']['author']['date'],c['commit']['committer']['date']),source_file=str((P/'raw'/f'{season}_{c["sha"]}_players.csv').relative_to(R)),source_url=f'https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/{c["sha"]}/data/{season}/players_raw.csv',commit=c['sha'],status='selected_csv_status_only_chance_unbound')
 (P/'selected_sources.json').write_text(json.dumps(selected,indent=2))
 def fetch(row):
  if row['format']=='none':return None
  try:
   path=R/row['source_file'];raw=get(row['source_url'],path,binary=True)
   if row['blob_sha']:assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['blob_sha'];json.loads(lzma.decompress(raw))
   return None
  except Exception as e:return dict(season=row['season'],round=row['round'],kind='payload',error=str(e))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:errors += [e for e in pool.map(fetch,selected) if e]
 overrides={};reselect=[]
 for row in selected:
  if row['format']!='bootstrap' or not (R/row['source_file']).exists():continue
  data=json.loads(lzma.decompress((R/row['source_file']).read_bytes()));event=next((e for e in data['events'] if e['id']==row['round']),None)
  if not event:continue
  actual=dt(event['deadline_time']);cutoff=min(dt(row['master_origin']),actual);row['original_selection_cutoff']=row['selection_cutoff'];row['actual_deadline']=actual.isoformat();row['selection_cutoff']=cutoff.isoformat()
  if actual<dt(row['master_origin']):overrides[row['season']+':'+str(row['round'])]=actual.isoformat()
  if dt(row['source_time'])>=cutoff:reselect.append(dict(season=row['season'],round=row['round'],reason='source_not_before_actual_deadline'))
 (P/'deadline_overrides.json').write_text(json.dumps(overrides,indent=2));(P/'selected_sources.json').write_text(json.dumps(selected,indent=2));(P/'deadline_reselection_required.json').write_text(json.dumps(reselect,indent=2))
 (P/'fetch_errors.json').write_text(json.dumps(errors,indent=2));print('Selected',len(selected),'sources',sum(r['format']!='none' for r in selected),'errors',len(errors),flush=True)
if __name__=='__main__':main()
