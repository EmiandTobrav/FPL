"""Season-specific ground mapping and reconciliation against cached FPL sources."""
import collections
import csv
import html
import json
import re
import shutil
from datetime import datetime, timezone

CLUB_NAMES={
 'Brighton':'Brighton & Hove Albion','Leeds':'Leeds United','Leicester':'Leicester City',
 'Man City':'Manchester City','Man Utd':'Manchester United','Newcastle':'Newcastle United',
 "Nott'm Forest":'Nottingham Forest','Spurs':'Tottenham Hotspur','West Ham':'West Ham United',
 'Wolves':'Wolverhampton Wanderers','Norwich':'Norwich City','Sheffield Utd':'Sheffield United',
 'West Brom':'West Bromwich Albion','Luton':'Luton Town','Ipswich':'Ipswich Town',
}

def prepare(e):
    root,base,season=e.ROOT,e.BASE,e.SEASON
    rows=e.master_rows()
    groups=collections.defaultdict(list)
    for r in rows:groups[r['fixture']].append(r)
    assert rows
    if season=='2026-27':
        sources=json.loads((root/'raw/fixtures.json').read_text())
        source={str(r['id']):r for r in sources}
        teams={str(r['id']):r['name'] for r in json.loads((root/'raw/bootstrap-static.json').read_text())['teams']}
        source_file=root/'raw/fixtures.json'
    else:
        source={r['id']:r for r in e.read_csv('raw/fixtures.csv')}
        teams={r['id']:r['name'] for r in e.read_csv('raw/teams.csv')}
        source_file=root/'raw/fixtures.csv'
    assert set(groups)<=set(source)
    full=season!='2026-27'
    assert len(groups)==(380 if full else 50)
    if full:assert set(groups)==set(source)
    source_url=json.loads(source_file.with_name(source_file.name+'.source.json').read_text()).get('source','')

    # Infer no grounds from today's teams: use each season's team/ground table.
    tables=re.findall(r'<table\b[^>]*>.*?</table>',(root/'raw/season.html').read_text(),re.S)
    table=next(t for t in tables if 'Stadium' in t and 'Capacity' in t)
    clean=lambda x:' '.join(html.unescape(re.sub('<[^>]+>',' ',x)).split())
    venues={}
    for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',table,re.S):
        cells=re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>',row,re.S)
        if len(cells)>=3:venues[clean(cells[0])]=clean(cells[2])
    coords={}
    for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',(base/'raw/stadiums.html').read_text(),re.S):
        cells=re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>',row,re.S)
        c=re.findall(r'class="geo"[^>]*>(.*?)</span>',row,re.S)
        if cells and c:coords[clean(cells[0])]=tuple(map(float,c[0].split(';')))
    stadiums={}
    for club in sorted({r['historical_team'] for r in rows}):
        canonical=CLUB_NAMES.get(club,club)
        venue=venues[canonical]
        if venue=='City of Manchester Stadium':venue='Etihad Stadium'
        name=next(n for n in coords if n==venue or n.startswith(venue+' '))
        lat,lon=coords[name]
        coordinate_source='https://en.wikipedia.org/wiki/List_of_Premier_League_stadiums'
        correction=''
        if venue=='Hill Dickinson Stadium':
            old=(lat,lon)
            dedicated=re.findall(r'class="geo"[^>]*>(.*?)</span>',(base/'raw/everton_stadium.html').read_text(),re.S)
            lat,lon=map(float,dedicated[0].split(';'))
            assert 53.40<lat<53.45 and -3.03<lon<-2.98
            coordinate_source='https://en.wikipedia.org/wiki/Hill_Dickinson_Stadium'
            correction=f'Dedicated stadium article used; summary table coordinate {old} disagrees.'
        stadiums[club]=dict(home_team=club,stadium=venue,latitude=lat,longitude=lon,
            coordinate_source=coordinate_source,
            venue_source=f'https://en.wikipedia.org/wiki/{season[:4]}%E2%80%93{season[-2:]}_Premier_League',
            venue_scope=season+' only; corroborated season home-ground mapping',coordinate_note=correction)
    assert len(stadiums)==20
    e.write_csv('stadiums.csv',list(stadiums.values()))

    fixtures=[];conflicts=[]
    for fid,rs in sorted(groups.items(),key=lambda x:int(x[0])):
        s=source[fid]
        home,away=teams[str(s['team_h'])],teams[str(s['team_a'])]
        # Native source team names can be Ipswich vs Ipswich Town in different years.
        home_master=next(r['historical_team'] for r in rs if r['was_home']=='True')
        away_master=next(r['historical_team'] for r in rs if r['was_home']=='False')
        assert CLUB_NAMES.get(home_master,home_master)==CLUB_NAMES.get(home,home)
        assert CLUB_NAMES.get(away_master,away_master)==CLUB_NAMES.get(away,away)
        home,away=home_master,away_master
        assert {r['fixture_kickoff_time'] for r in rs}=={s['kickoff_time']},(season,fid,'fixture timestamp')
        assert e.dt(s['kickoff_time'])<datetime(2026,10,25,tzinfo=timezone.utc)
        raw_times=sorted({r['kickoff_time'] for r in rs})
        conflict=raw_times!=[s['kickoff_time']]
        if conflict:
            # The one known delayed actual kickoff is independently documented.
            assert (season,fid,raw_times,s['kickoff_time'])==('2021-22','263',['2022-02-26T15:00:00Z'],'2022-02-26T15:30:00Z')
            conflicts.append(dict(season=season,fixture=fid,native_kickoff_times=raw_times,
                selected_kickoff=s['kickoff_time'],affected_player_rows=len(rs),
                resolution='Canonical fixture time; 30-minute traffic delay. Original player rows retained.',
                evidence='https://www.brightonandhovenews.org/2022/02/26/traffic-delays-kick-off-as-brighton-and-hove-albion-prepare-to-host-aston-villa/'))
        for r in rs:
            h=r['was_home']=='True'
            assert r['historical_team']==(home if h else away)
            assert int(float(r['historical_team_id']))==int(s['team_h'] if h else s['team_a'])
            assert int(float(r['opponent_team']))==int(s['team_a'] if h else s['team_h'])
            assert int(float(r['fixture_event']))==int(s['event'])
        v=stadiums[home]
        fixtures.append(dict(season=season,fixture=fid,event=s['event'],kickoff_utc=s['kickoff_time'],
            home_team=home,away_team=away,stadium=v['stadium'],latitude=v['latitude'],longitude=v['longitude'],
            player_match_rows=len(rs),native_kickoff_conflict=conflict,
            native_kickoff_times=';'.join(raw_times),
            kickoff_selection='canonical_fixture_time',venue_coordinate_note=v['coordinate_note']))
    if full:
        for side in ['home_team','away_team']:
            assert collections.Counter(f[side] for f in fixtures)==collections.Counter({k:19 for k in stadiums})
    assert len({(f['home_team'],f['away_team']) for f in fixtures})==len(fixtures)
    e.write_csv('fixtures.csv',fixtures)
    e.dump('kickoff_conflicts.json',conflicts)
    e.dump('preflight.json',dict(season=season,fixtures=len(fixtures),stadiums=20,player_match_rows=len(rows),
        scope='all observed master-table fixtures; current season partial, 2019-20 reference-only labels retained',
        full_season=full,master_sha256=e.sha(e.MASTER),source_fixture_sha256=e.sha(source_file),source_fixture=source_url,
        historical_venue_mapping_check='20 clubs matched season table; explicit stadium aliases and coordinate provenance',
        canonical_fixture_time_team_opponent_event_checks='passed for every master row',
        native_timestamp_conflict_fixtures=len(conflicts),native_timestamp_conflict_rows=sum(c['affected_player_rows'] for c in conflicts),
        all_fixture_ids_match_source=True,each_club_has_19_home_and_19_away=full,
        model='ecmwf_ifs',window='[canonical actual kickoff, kickoff + 120 minutes)',originals_modified=False))
    print(season,'prepared',len(fixtures),'fixtures;',len(conflicts),'flagged native timestamp conflicts.',flush=True)
    if season=='2022-23':
        pilot=e.PROJECT/'datasets/fpl_weather_pilot_2022_23_v1/raw'
        for p in pilot.glob('*_weather.json*'):
            if not (root/'raw'/p.name).exists():shutil.copy2(p,root/'raw'/p.name)
