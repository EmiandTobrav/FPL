"""Cache public source snapshots; retain local historical fallbacks explicitly."""
import csv
import gzip
import hashlib
import io
import json
import shutil
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[1]
PILOT=PROJECT/'datasets/fpl_weather_pilot_2022_23_v1'
SEASONS=[f'{y}-{str(y+1)[2:]}' for y in range(2019,2027)]

def save_meta(path,url,kind):
    path.with_name(path.name+'.source.json').write_text(json.dumps(dict(
        source=url,source_kind=kind,fetched_or_copied_at=datetime.now(timezone.utc).isoformat(),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest()),indent=2))

def download(url,path,fallback=None):
    if path.exists():return
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'FPLWeatherResearch/1.0'})
        with urllib.request.urlopen(request,timeout=60) as response:data=response.read()
        path.write_bytes(data)
        save_meta(path,url,'public_web_snapshot')
    except urllib.error.HTTPError as e:
        if e.code!=404 or not fallback:raise
        with gzip.open(fallback,'rb') as f:path.write_bytes(f.read())
        save_meta(path,str(fallback),'local_archived_FPL_snapshot_remote_404')
    print(path.relative_to(BASE),path.stat().st_size,flush=True)

if __name__=='__main__':
    (BASE/'raw').mkdir(exist_ok=True)
    for name in ['stadiums.html','weather_documentation.html']:
        target=BASE/'raw'/name
        if not target.exists():
            shutil.copy2(PILOT/'raw'/name,target)
            shutil.copy2(PILOT/'raw'/(name+'.source.json'),BASE/'raw'/(name+'.source.json'))
    download('https://en.wikipedia.org/wiki/Hill_Dickinson_Stadium',BASE/'raw/everton_stadium.html')
    for season in SEASONS:
        raw=BASE/season/'raw';raw.mkdir(parents=True,exist_ok=True)
        if season=='2022-23':
            for name in ['fixtures.csv','teams.csv','season.html']:
                if not (raw/name).exists():
                    shutil.copy2(PILOT/'raw'/name,raw/name)
                    shutil.copy2(PILOT/'raw'/(name+'.source.json'),raw/(name+'.source.json'))
            continue
        year=int(season[:4]);suffix=f'{year}%E2%80%93{str(year+1)[2:]}_Premier_League'
        download('https://en.wikipedia.org/wiki/'+suffix,raw/'season.html')
        if season=='2026-27':
            source=PROJECT/'FPL_training_dataset/research/current/training_dataset/snapshots/2026_10_08/raw'
            for name in ['fixtures.json','bootstrap-static.json']:
                if not (raw/name).exists():
                    shutil.copy2(source/name,raw/name);save_meta(raw/name,str(source/name),'local_archived_official_FPL_snapshot')
        else:
            for name in ['fixtures','teams']:
                fallback=PROJECT/'FPL_training_dataset/research/current/project/data'/f'{season}_{name}.csv.gz'
                download(f'https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{season}/{name}.csv',raw/(name+'.csv'),fallback)
