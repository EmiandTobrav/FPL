"""Reproducible, cached one-season historical weather enrichment. Stdlib only.

Run prepare, fetch (network), then build. Original FPL tables remain untouched.
"""
import argparse
import calendar
import collections
import csv
import gzip
import hashlib
import html
import io
import json
import lzma
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
ROOT = BASE
PROJECT = ROOT.parents[1]
MASTER = PROJECT / 'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz'
SEASON = '2022-23'
VARIABLES = ['temperature_2m', 'relative_humidity_2m', 'cloud_cover',
             'sunshine_duration', 'direct_radiation', 'shortwave_radiation',
             'is_day', 'precipitation', 'rain', 'snowfall',
             'wind_speed_10m', 'wind_gusts_10m']
VENUES = {
    'Arsenal': 'Emirates Stadium', 'Aston Villa': 'Villa Park',
    'Bournemouth': 'Dean Court', 'Brentford': 'Brentford Community Stadium',
    'Brighton': 'Falmer Stadium', 'Chelsea': 'Stamford Bridge',
    'Crystal Palace': 'Selhurst Park', 'Everton': 'Goodison Park',
    'Fulham': 'Craven Cottage', 'Leeds': 'Elland Road',
    'Leicester': 'King Power Stadium', 'Liverpool': 'Anfield',
    'Man City': 'Etihad Stadium', 'Man Utd': 'Old Trafford',
    'Newcastle': "St James' Park", "Nott'm Forest": 'City Ground',
    'Southampton': "St Mary's Stadium", 'Spurs': 'Tottenham Hotspur Stadium',
    'West Ham': 'London Stadium', 'Wolves': 'Molineux Stadium',
}

def dump(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False))

def write_csv(name, rows):
    op = gzip.open if name.endswith('.gz') else open
    with op(ROOT / name, 'wt', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def read_csv(name):
    with open(ROOT / name, newline='') as f:
        return list(csv.DictReader(f))

def dt(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)

def master_rows():
    with lzma.open(MASTER, 'rt') as f:
        return [r for r in csv.DictReader(f) if r['season'] == SEASON]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare():
    import sys
    from preparation import prepare as prepare_season
    prepare_season(sys.modules[__name__])


def fetch():
    fixtures = read_csv('fixtures.csv')
    for stadium in read_csv('stadiums.csv'):
        club = stadium['home_team']
        slug = re.sub('[^a-z0-9]+', '_', club.lower()).strip('_')
        path = ROOT / 'raw' / (slug + '_weather.json')
        if path.exists():
            continue
        kicks = [dt(f['kickoff_utc']) for f in fixtures if f['home_team']==club]
        params = dict(latitude=stadium['latitude'], longitude=stadium['longitude'],
            start_date=(min(kicks)-timedelta(days=1)).date().isoformat(),
            end_date=(max(kicks)+timedelta(days=1)).date().isoformat(),
            hourly=','.join(VARIABLES), daily='sunrise,sunset',
            models='ecmwf_ifs', timezone='GMT', wind_speed_unit='ms')
        url = 'https://archive-api.open-meteo.com/v1/archive?' + urllib.parse.urlencode(params)
        for attempt in range(6):
            try:
                req = urllib.request.Request(url, headers={'User-Agent':'FPLWeatherResearch/1.0'})
                with urllib.request.urlopen(req, timeout=60) as response:
                    data = response.read()
                parsed = json.loads(data)
                assert not parsed.get('error'), parsed
                assert all(v in parsed['hourly'] for v in VARIABLES)
                path.write_bytes(data)
                dump(str(path.relative_to(ROOT))+'.source.json', dict(url=url,
                    fetched_at=datetime.now(timezone.utc).isoformat(), sha256=sha(path),
                    model='ecmwf_ifs', data_kind='historical gridded reconstruction',
                    latitude_requested=float(stadium['latitude']), longitude_requested=float(stadium['longitude'])))
                print(club, len(parsed['hourly']['time']), 'hours', flush=True)
                break
            except (urllib.error.URLError, TimeoutError) as error:
                print(club, 'retry', attempt+1, str(error), flush=True)
                if attempt == 5:
                    raise
                time.sleep(min(60, 10*(attempt+1)))
        # Long seasonal requests count as several calls in the provider quota.
        time.sleep(4)

def distance(lat1, lon1, lat2, lon2):
    a,b = map(math.radians, (lat1,lat2))
    dlat,dlon = math.radians(lat2-lat1),math.radians(lon2-lon1)
    return 6371*2*math.asin(math.sqrt(math.sin(dlat/2)**2+math.cos(a)*math.cos(b)*math.sin(dlon/2)**2))

def interpolate(series, t):
    hour = t.replace(minute=0, second=0, microsecond=0)
    a = series[hour]
    if t == hour:
        return a
    b = series[hour+timedelta(hours=1)]
    return a+(b-a)*(t-hour).total_seconds()/3600

def instantaneous_mean(series, start, end):
    knots = [start]
    t = start.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)
    while t<end:
        knots.append(t)
        t+=timedelta(hours=1)
    knots.append(end)
    return sum((interpolate(series,a)+interpolate(series,b))/2*(b-a).total_seconds()
               for a,b in zip(knots,knots[1:]))/(end-start).total_seconds()

def interval_value(series, start, end, is_sum):
    # Each API timestamp t labels the PRECEDING hour (t-1h,t].
    result, coverage = 0, 0
    t = start.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)
    while t-timedelta(hours=1)<end:
        seconds=max(0,(min(t,end)-max(t-timedelta(hours=1),start)).total_seconds())
        value=series[t]
        result+=value*seconds/(3600 if is_sum else (end-start).total_seconds())
        coverage+=seconds
        t+=timedelta(hours=1)
    assert coverage==(end-start).total_seconds()
    return result

def build():
    fixtures = read_csv('fixtures.csv')
    cache, hourly_rows, grid_rows = {}, [], []
    missing_counts = collections.Counter()
    for stadium in read_csv('stadiums.csv'):
        club=stadium['home_team']
        slug=re.sub('[^a-z0-9]+','_',club.lower()).strip('_')
        name='raw/'+slug+'_weather.json'
        raw=json.loads((ROOT/name).read_text())
        assert raw['utc_offset_seconds']==0
        assert raw['hourly_units']['sunshine_duration']=='s'
        assert raw['hourly_units']['shortwave_radiation']=='W/m²'
        assert raw['hourly_units']['wind_speed_10m']=='m/s'
        times=[dt(t) for t in raw['hourly']['time']]
        assert len(times)==len(set(times))
        assert all((b-a).total_seconds()==3600 for a,b in zip(times,times[1:]))
        series={v:dict(zip(times,raw['hourly'][v])) for v in VARIABLES}
        for v in VARIABLES:
            assert len(raw['hourly'][v])==len(times)
            missing_counts[v]+=sum(x is None for x in raw['hourly'][v])
        for i,t in enumerate(times):
            hourly_rows.append(dict(season=SEASON, home_team=club, stadium=stadium['stadium'],
                time_utc=t.isoformat(), **{v:raw['hourly'][v][i] for v in VARIABLES}))
        daily={d:(dt(a),dt(b)) for d,a,b in zip(raw['daily']['time'],raw['daily']['sunrise'],raw['daily']['sunset'])}
        km=distance(float(stadium['latitude']),float(stadium['longitude']),raw['latitude'],raw['longitude'])
        assert km<20
        grid_rows.append(dict(home_team=club,stadium=stadium['stadium'],latitude=float(stadium['latitude']),
            longitude=float(stadium['longitude']),grid_latitude=raw['latitude'],grid_longitude=raw['longitude'],
            grid_distance_km=round(km,3),raw_file=name))
        cache[club]=(series,daily,km,name)
    output=[]
    for f in fixtures:
        start=dt(f['kickoff_utc']); end=start+timedelta(hours=2)
        series,daily,km,name=cache[f['home_team']]
        out=dict(f,weather_key=SEASON+':'+f['fixture'],window_end_utc=end.isoformat(),window_minutes=120,
            kickoff_london=start.astimezone(ZoneInfo('Europe/London')).isoformat(),
            weather_model='ecmwf_ifs',weather_kind='historical_reconstruction',
            grid_distance_km=round(km,3),raw_file=name)
        for v in ['temperature_2m','relative_humidity_2m','cloud_cover','wind_speed_10m','wind_gusts_10m']:
            out[v+'_kickoff']=round(interpolate(series[v],start),4)
            out[v+'_mean']=round(instantaneous_mean(series[v],start,end),4)
        for v in ['precipitation','rain','snowfall','sunshine_duration']:
            out[v+'_sum']=round(interval_value(series[v],start,end,True),4)
        for v in ['direct_radiation','shortwave_radiation']:
            out[v+'_mean']=round(interval_value(series[v],start,end,False),4)
        sunrise,sunset=daily[start.date().isoformat()]
        dayseconds=max(0,(min(end,sunset)-max(start,sunrise)).total_seconds())
        out['daylight_fraction']=round(dayseconds/7200,6)
        out['daylight_minutes']=round(dayseconds/60,4)
        out['sunshine_minutes']=round(out['sunshine_duration_sum']/60,4)
        # Do not silently replace source-derived values. Expose a separate cap
        # and a flag for hourly averages that straddle sunset/sunrise.
        out['sunshine_minutes_daylight_capped']=min(out['sunshine_minutes'],out['daylight_minutes'])
        out['hourly_sunshine_exceeds_daylight']=out['sunshine_minutes']>out['daylight_minutes']+0.0001
        assert 0<=out['sunshine_duration_sum']<=7200
        assert 0<=out['cloud_cover_mean']<=100
        assert 0<=out['relative_humidity_2m_mean']<=100
        assert out['precipitation_sum']>=0
        assert out['direct_radiation_mean']>=0
        out['sunshine_fraction_of_window']=round(out['sunshine_duration_sum']/7200,6)
        # Descriptive, explicitly heuristic category; raw values are authoritative.
        if dayseconds==0:
            category='dark'
        elif dayseconds<7200:
            category='daylight_transition'
        elif out['sunshine_fraction_of_window']>=0.5:
            category='mostly_sunny'
        elif out['sunshine_duration_sum']>0:
            category='some_sun'
        else:
            category='no_direct_sun'
        out['sun_category_heuristic']=category
        output.append(out)
    write_csv('match_weather.csv',output)
    write_csv('hourly_weather.csv.gz',hourly_rows)
    write_csv('grid_audit.csv',grid_rows)
    lookup={f['fixture']:f for f in output}
    links=[]
    rows=master_rows()
    for r in rows:
        f=lookup[r['fixture']]
        assert r['fixture_kickoff_time']==f['kickoff_utc']
        links.append(dict(season=SEASON,fixture=r['fixture'],element=r['element'],
            code=r['code'],source_key=r['source_key'],name=r['name'],
            historical_team=r['historical_team'],was_home=r['was_home'],
            weather_key=SEASON+':'+r['fixture']))
    assert len({(r['fixture'],r['element']) for r in links})==len(links)
    write_csv('player_match_weather_links.csv.gz',links)
    audit=dict(season=SEASON,fixtures=len(output),stadiums=len(cache),
        player_match_rows=len(rows),linked_rows=len(links),unmatched_rows=0,
        duplicate_weather_keys=len(output)-len(lookup),hourly_rows=len(hourly_rows),
        raw_missing_by_variable=dict(missing_counts),
        max_grid_distance_km=round(max(x['grid_distance_km'] for x in grid_rows),3),
        sun_categories=dict(collections.Counter(x['sun_category_heuristic'] for x in output)),
        hourly_sunshine_exceeds_daylight_fixtures=[x['fixture'] for x in output if x['hourly_sunshine_exceeds_daylight']],
        completely_dark_with_hourly_sunshine_fixtures=[x['fixture'] for x in output if x['daylight_minutes']==0 and x['sunshine_minutes']>0],
        checks=dict(all_fixture_ids_match_source=True,all_canonical_fixture_times_teams_opponents_events_match=True,
            season_schedule_structure_checked=True,unique_home_away_pairs=True,utc_hourly_continuity=True,
            units_verified=True,interval_overlap_covers_7200_seconds=True,physical_bounds_checked=True,
            master_hash_unchanged=sha(MASTER)==json.loads((ROOT/'preflight.json').read_text())['master_sha256']),
        native_timestamp_conflict_fixtures=json.loads((ROOT/'preflight.json').read_text())['native_timestamp_conflict_fixtures'],
        full_season=json.loads((ROOT/'preflight.json').read_text())['full_season'],
        scope='Retrospective enrichment only. No pre-deadline weather qualification; no model improvement claim.')
    dump('verification.json',audit)
    files=[p for p in ROOT.rglob('*') if p.is_file() and p.name!='manifest.json' and '__pycache__' not in str(p)]
    dump('manifest.json',dict(season=SEASON,created_at=datetime.now(timezone.utc).isoformat(),
        files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}))
    print(json.dumps(audit,indent=2),flush=True)

def package():
    audit=json.loads((ROOT/'verification.json').read_text())
    independent=json.loads((ROOT/'independent_verification.json').read_text())
    assert all(audit['checks'].values())
    assert independent['status']=='passed'
    assert audit['fixtures']==json.loads((ROOT/'preflight.json').read_text())['fixtures'] and audit['unmatched_rows']==0
    assert sha(MASTER)==json.loads((ROOT/'preflight.json').read_text())['master_sha256']
    files=[p for p in ROOT.rglob('*') if p.is_file() and p.name!='manifest.json' and '__pycache__' not in str(p)]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}
    dump('manifest.json',dict(season=SEASON,created_at=datetime.now(timezone.utc).isoformat(),
        status='season_completed_with_documented_hourly_solar_boundary_flags',files=hashes))
    target=ROOT.parent/(ROOT.name+'.zip')
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(files+[ROOT/'manifest.json']):
            archive.write(p,str(p.relative_to(ROOT.parent)))
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        for name,digest in hashes.items():
            assert hashlib.sha256(archive.read(ROOT.name+'/'+name)).hexdigest()==digest
    print('Package verified:',target,'bytes:',target.stat().st_size,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=['prepare','fetch','build','package'])
    parser.add_argument('--season',required=True,choices=[f'{y}-{str(y+1)[2:]}' for y in range(2019,2027)])
    args=parser.parse_args()
    SEASON=args.season
    ROOT=BASE/SEASON
    globals()[args.stage]()
