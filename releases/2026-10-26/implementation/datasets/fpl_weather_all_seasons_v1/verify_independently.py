"""Independent minute-grid checks of saved match weather and time joins.

Does not import the enrichment implementation. Tests all 380 aggregate rows.
"""
import argparse
import collections
import gzip
import hashlib
import csv
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BASE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--season',required=True)
SEASON=parser.parse_args().season
ROOT=BASE/SEASON
parse=lambda s: datetime.fromisoformat(s.replace('Z','+00:00')).replace(tzinfo=timezone.utc)
with (ROOT/'match_weather.csv').open() as f:
    rows=list(csv.DictReader(f))
cache={}
for row in rows:
    if row['raw_file'] not in cache:
        d=json.loads((ROOT/row['raw_file']).read_text())
        cache[row['raw_file']]={parse(t):{k:v[i] for k,v in d['hourly'].items() if k!='time'}
                              for i,t in enumerate(d['hourly']['time'])}

errors=[]
for row in rows:
    start=parse(row['kickoff_utc'])
    data=cache[row['raw_file']]
    assert datetime.fromisoformat(row['kickoff_london']).astimezone(timezone.utc)==start
    assert row['kickoff_london']==start.astimezone(ZoneInfo('Europe/London')).isoformat()
    assert start.second==0
    # Midpoint sampling exactly integrates piecewise constant preceding-hour data.
    sums={v:0 for v in ['sunshine_duration','precipitation','rain','snowfall','direct_radiation','shortwave_radiation']}
    means={v:0 for v in ['temperature_2m','relative_humidity_2m','cloud_cover','wind_speed_10m','wind_gusts_10m']}
    for minute in range(120):
        t=start+timedelta(minutes=minute,seconds=30)
        lower=t.replace(minute=0,second=0,microsecond=0)
        upper=lower+timedelta(hours=1)
        fraction=(t-lower).total_seconds()/3600
        for v in sums:
            sums[v]+=data[upper][v]/(120 if 'radiation' in v else 60)
        for v in means:
            means[v]+=(data[lower][v]*(1-fraction)+data[upper][v]*fraction)/120
    for v,value in sums.items():
        key=v+('_mean' if 'radiation' in v else '_sum')
        errors.append(abs(float(row[key])-value))
        assert abs(float(row[key])-value)<0.000051,(row['fixture'],key,value,row[key])
    for v,value in means.items():
        errors.append(abs(float(row[v+'_mean'])-value))
        assert abs(float(row[v+'_mean'])-value)<0.000051

# Independently documented calendar traps, including original vs revised date.
cases=[
    dict(home='Man Utd',away='West Ham',date='2022-10-30',local='2022-10-30T16:15:00+00:00',
         venue='Old Trafford',reason='Winter-time change and quarter-hour kickoff',
         source='https://www.premierleague.com/es/news/2815650'),
    dict(home='Arsenal',away='Chelsea',date='2023-05-02',local='2023-05-02T20:00:00+01:00',
         venue='Emirates Stadium',reason='Moved from 29 April; use played date and summer time',
         source='https://www.premierleague.com/en/news/3146088'),
    dict(home='Fulham',away='Liverpool',date='2022-08-06',local='2022-08-06T12:30:00+01:00',
         venue='Craven Cottage',reason='Summer-time daytime and half-hour window',
         source='raw/fixtures.csv'),
]
if SEASON!='2022-23':
    cases=[]
if SEASON=='2021-22':
    cases.append(dict(home='Brighton',away='Aston Villa',date='2022-02-26',
        local='2022-02-26T15:30:00+00:00',venue='Falmer Stadium',
        reason='Actual kickoff delayed 30 minutes; native player timestamp retained and flagged',
        source='https://www.brightonandhovenews.org/2022/02/26/traffic-delays-kick-off-as-brighton-and-hove-albion-prepare-to-host-aston-villa/'))
samples=[]
for case in cases:
    row=next(r for r in rows if r['home_team']==case['home'] and r['away_team']==case['away'])
    assert row['kickoff_utc'].startswith(case['date'])
    assert row['kickoff_london']==case['local']
    assert row['stadium']==case['venue']
    samples.append(dict(case,fixture=row['fixture'],passed=True,
        sunshine_minutes=float(row['sunshine_minutes']),daylight_fraction=float(row['daylight_fraction'])))
dark=[r for r in rows if r['sun_category_heuristic']=='dark']
assert dark
# Rounded hour-long solar estimates may straddle sunrise/sunset: count, do not conceal.
dark_with_sun=[r['fixture'] for r in dark if float(r['sunshine_minutes'])>0]
assert all(float(r['sunshine_minutes_daylight_capped'])==0 for r in dark)
assert all(0<=float(r['sunshine_minutes_daylight_capped'])<=float(r['daylight_minutes']) for r in rows)
assert all(r['hourly_sunshine_exceeds_daylight']=='True' for r in dark if float(r['sunshine_minutes'])>0)
# Verify source-byte provenance and all many-to-one row links.
for path in (ROOT/'raw').glob('*_weather.json'):
    meta=json.loads(path.with_name(path.name+'.source.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==meta['sha256']
    assert 'models=ecmwf_ifs' in meta['url']
lookup={r['weather_key']:r for r in rows}
assert len(lookup)==len(rows)
with gzip.open(ROOT/'player_match_weather_links.csv.gz','rt') as f:
    links=list(csv.DictReader(f))
assert len({(r['season'],r['fixture'],r['element']) for r in links})==len(links)
counts=collections.Counter()
for link in links:
    match=lookup[link['weather_key']]
    assert link['season']==match['season']==SEASON
    assert link['fixture']==match['fixture']
    assert link['historical_team']==match['home_team' if link['was_home']=='True' else 'away_team']
    counts[match['fixture']]+=1
for row in rows:
    assert counts[row['fixture']]==int(row['player_match_rows'])
    assert row['native_kickoff_conflict'] in ['True','False']
    if row['home_team']=='Everton':
        assert row['stadium']==('Hill Dickinson Stadium' if SEASON>='2025-26' else 'Goodison Park')
    assert 0<=float(row['cloud_cover_mean'])<=100
    assert float(row['rain_sum'])>=0
if SEASON=='2021-22':
    delayed=next(r for r in rows if r['fixture']=='263')
    assert delayed['native_kickoff_conflict']=='True'
    assert delayed['native_kickoff_times']=='2022-02-26T15:00:00Z'
offsets=sorted({int(datetime.fromisoformat(r['kickoff_london']).utcoffset().total_seconds()/60) for r in rows})
assert offsets==([60] if SEASON=='2026-27' else [0,60])
preflight=json.loads((ROOT/'preflight.json').read_text())
assert len(rows)==preflight['fixtures'] and len(links)==preflight['player_match_rows']
result=dict(status='passed',season=SEASON,linked_player_rows=len(links),
    utc_offsets_minutes=offsets,raw_weather_hashes_verified=True,unique_weather_and_player_keys_verified=True,
    everton_historical_stadium_verified=True,fixtures_checked=len(rows),
    independently_recomputed_fields=len(errors),maximum_absolute_rounding_error=max(errors),
    method='120 minute-midpoint samples; separate implementation; raw preceding-hour labels',
    calendar_spot_checks=samples,dark_matches_with_positive_hourly_estimated_sunshine=dark_with_sun,
    dark_match_flags_and_separate_daylight_capped_values_verified=True)
(ROOT/'independent_verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
print(json.dumps(result,indent=2,ensure_ascii=False))
