"""Combine verified seasons, check pilot equivalence, and package the release."""
import collections
import csv
import gzip
import hashlib
import json
import lzma
import zipfile
from datetime import datetime, timezone
from pathlib import Path

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[1]
SEASONS=[f'{y}-{str(y+1)[2:]}' for y in range(2019,2027)]
MASTER=PROJECT/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def read(path):
    op=gzip.open if str(path).endswith('.gz') else open
    with op(path,'rt',newline='') as f:return list(csv.DictReader(f))

def write(path,rows):
    op=gzip.open if str(path).endswith('.gz') else open
    with op(path,'wt',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    season_summary=[];matches=[];links=[];stadiums=[];conflicts=[];boundary=[]
    for season in SEASONS:
        root=BASE/season
        a=json.loads((root/'verification.json').read_text())
        v=json.loads((root/'independent_verification.json').read_text())
        p=json.loads((root/'preflight.json').read_text())
        assert all(a['checks'].values()) and v['status']=='passed'
        assert a['unmatched_rows']==a['duplicate_weather_keys']==0
        assert a['player_match_rows']==a['linked_rows']==v['linked_player_rows']
        assert all(n==0 for n in a['raw_missing_by_variable'].values())
        assert sha(MASTER)==p['master_sha256']
        season_files=[f for f in root.rglob('*') if f.is_file() and f.name!='manifest.json']
        (root/'manifest.json').write_text(json.dumps(dict(season=season,
            status='verified',files={str(f.relative_to(root)):sha(f) for f in sorted(season_files)}),indent=2))
        ms=read(root/'match_weather.csv');matches.extend(ms)
        links.extend(read(root/'player_match_weather_links.csv.gz'))
        stadiums.extend(dict(season=season,**r) for r in read(root/'stadiums.csv'))
        conflicts.extend(json.loads((root/'kickoff_conflicts.json').read_text()))
        boundary.extend(r for r in ms if r['hourly_sunshine_exceeds_daylight']=='True')
        season_summary.append(dict(season=season,full_season=p['full_season'],fixtures=a['fixtures'],
            linked_player_rows=a['linked_rows'],hourly_rows=a['hourly_rows'],
            missing_weather_values=sum(a['raw_missing_by_variable'].values()),
            sunrise_sunset_flags=len(a['hourly_sunshine_exceeds_daylight_fixtures']),
            dark_with_unadjusted_sunshine=len(a['completely_dark_with_hourly_sunshine_fixtures']),
            native_timestamp_conflicts=a['native_timestamp_conflict_fixtures'],
            max_grid_distance_km=a['max_grid_distance_km'],
            independently_recomputed_fields=v['independently_recomputed_fields']))
    keys=[r['weather_key'] for r in matches]
    assert len(set(keys))==len(keys)==2710
    linkkeys={(r['season'],r['fixture'],r['element']) for r in links}
    assert len(linkkeys)==len(links)==187111
    with lzma.open(MASTER,'rt') as f:
        native={(r['season'],r['fixture'],r['element']) for r in csv.DictReader(f)}
    assert linkkeys==native
    assert {r['weather_key'] for r in links}==set(keys)

    # The larger release preserves every pilot value, using its cached raw data.
    pilot=PROJECT/'datasets/fpl_weather_pilot_2022_23_v1'
    old={r['weather_key']:r for r in read(pilot/'match_weather.csv')}
    current={r['weather_key']:r for r in matches if r['season']=='2022-23'}
    assert set(old)==set(current)
    compared=0
    for key,row in old.items():
        for column,value in row.items():
            assert current[key][column]==value,(key,column,value,current[key][column])
            compared+=1
    write(BASE/'match_weather.csv',matches)
    write(BASE/'player_match_weather_links.csv.gz',links)
    write(BASE/'stadiums.csv',stadiums)
    write(BASE/'season_summary.csv',season_summary)
    write(BASE/'sunrise_sunset_flags.csv',boundary)
    (BASE/'kickoff_conflicts.json').write_text(json.dumps(conflicts,indent=2,ensure_ascii=False))
    summary=dict(status='complete',seasons=season_summary,total_fixtures=len(matches),
        linked_player_rows=len(links),unmatched_rows=0,missing_weather_values=0,
        total_sunrise_sunset_flags=len(boundary),
        total_dark_with_unadjusted_sunshine=sum(s['dark_with_unadjusted_sunshine'] for s in season_summary),
        total_hourly_rows=sum(s['hourly_rows'] for s in season_summary),
        independently_recomputed_fields=sum(s['independently_recomputed_fields'] for s in season_summary),
        pilot_regression_fields_compared=compared,pilot_values_unchanged=True,
        input_master_sha256=sha(MASTER),all_master_player_match_keys_covered=True,
        unique_season_fixture_weather_keys=True,native_timestamp_conflicts=conflicts,
        max_grid_distance_km=max(s['max_grid_distance_km'] for s in season_summary),
        scope='2019-20 through 2025-26 complete; 2026-27 only 50 matches already in master through 20 September. Historical weather, no model training or pre-deadline qualification.')
    (BASE/'verification.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
    report=['VÆRDATA — ALLE OBSERVERTE SESONGER','',
        f'Kamper: {len(matches):,}. Koblede spillerrader: {len(links):,}. Manglende værverdier: 0.',
        f'Merkede tilfeller ved soloppgang/solnedgang: {len(boundary)}.',
        '','Sesong       Kamper   Spillerrader   Solgrenseflagg']
    for s in season_summary:report.append(f"{s['season']:12} {s['fixtures']:5}   {s['linked_player_rows']:11}   {s['sunrise_sunset_flags']:14}")
    report.extend(['','2026/27 omfatter bare de 50 kampene som finnes i mastertabellen.',
        '2019/20 følger med som historisk referanse; poengmålenes status endres ikke.',
        'Brighton–Aston Villa 26.02.2022 bruker 15.30 UTC, med originalt 15.00-felt merket.',
        'Everton bruker Goodison Park til 2024/25, Hill Dickinson Stadium fra 2025/26.',
        'Alle pilotverdier er kontrollert uendret. Originaltabellens filhash er uendret.',
        'Se README.txt for metode, enheter, forbehold og gjenskaping.'])
    (BASE/'RESULTATER.txt').write_text('\n'.join(report)+'\n')
    files=[p for p in BASE.rglob('*') if p.is_file() and p!=BASE/'manifest.json' and '__pycache__' not in p.parts]
    hashes={str(p.relative_to(BASE)):sha(p) for p in sorted(files)}
    (BASE/'manifest.json').write_text(json.dumps(dict(version='fpl_weather_all_seasons_v1',
        packaged_at=datetime.now(timezone.utc).isoformat(),input_master_sha256=sha(MASTER),
        files=hashes),indent=2))
    target=BASE.parent/(BASE.name+'.zip')
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(files+[BASE/'manifest.json']):archive.write(p,str(p.relative_to(BASE.parent)))
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        for name,digest in hashes.items():
            assert hashlib.sha256(archive.read(BASE.name+'/'+name)).hexdigest()==digest
    print(json.dumps(summary,indent=2,ensure_ascii=False))
    print('Verified package',target,target.stat().st_size,'bytes')

if __name__=='__main__':main()
