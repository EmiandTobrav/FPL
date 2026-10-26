"""Shared all-season availability inputs; prior releases remain immutable."""
import csv,gzip,lzma,json,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timedelta,timezone
P=Path(__file__).resolve().parent;R=P.parents[1];OLD=R/'reports/availability_dataset_2026_10_16';PILOT=R/'datasets/fpl_availability_pilot_2023_24_v1';MASTER=R/'datasets/fpl_master_enriched_v2';OUT=R/'datasets/fpl_master_enriched_v3'
s=importlib.util.spec_from_file_location('availability_pilot_builder',PILOT/'build.py');pilot=importlib.util.module_from_spec(s);s.loader.exec_module(pilot)
dt=pilot.dt;num=pilot.num;truth=pilot.truth;sha=pilot.sha;read=pilot.read
def write(name,rows,fields=None):
 it=iter(rows);first=next(it,None)
 if first is None and fields is None:raise ValueError(name)
 op=lzma.open if name.endswith('.xz') else gzip.open if name.endswith('.gz') else open;kw={'preset':3} if name.endswith('.xz') else {}
 with op(P/name,'wt',newline='',**kw) as f:
  w=csv.DictWriter(f,fieldnames=fields or list(first));w.writeheader()
  if first is not None:w.writerow(first)
  w.writerows(it)
def origins():
 rows={}
 for r in read(MASTER/'player_matches.csv.xz'):
  key=r['season'],int(float(r['round']));at=dt(r['wl_forecast_at'])
  if key in rows:assert rows[key]['master_origin']==at.isoformat()
  else:rows[key]=dict(season=key[0],round=key[1],master_origin=at.isoformat(),selection_cutoff=at.isoformat(),actual_deadline='')
 for s in json.loads((OLD/'full_selected_snapshots.json').read_text()):
  key=s['season'],s['gw'];path=OLD/'raw'/f'{s["season"]}_gw{s["gw"]}.json.xz'
  if key not in rows or not path.exists():continue
  data=json.loads(lzma.decompress(path.read_bytes()));event=next((e for e in data['events'] if e['id']==s['gw']),None)
  if event:
   deadline=dt(event['deadline_time']);rows[key]['actual_deadline']=deadline.isoformat();rows[key]['selection_cutoff']=min(dt(rows[key]['master_origin']),deadline).isoformat()
 overrides=json.loads((P/'deadline_overrides.json').read_text()) if (P/'deadline_overrides.json').exists() else {}
 for key,value in overrides.items():
  season,gw=key.split(':');row=rows[(season,int(gw))];row['actual_deadline']=value;row['selection_cutoff']=min(dt(row['master_origin']),dt(value)).isoformat()
 return list(sorted(rows.values(),key=lambda r:(r['season'],r['round'])))
