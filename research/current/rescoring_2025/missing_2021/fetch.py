"""Public FotMob match data, cached and validated against official FPL fixtures."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib, json, sys, urllib.request, urllib.error
import pandas as pd

P=Path(__file__).resolve().parent; R=P.parents[1]; H=P.parent/'historical_fbref'
sys.path.insert(0,str(H))
from build import ALIASES
ALIASES={**ALIASES,'Brighton and Hove Albion':'Brighton'}
RAW=P/'raw'; OUT=P/'results'
ARCHIVE='https://github.com/JaseZiv/worldfootballR_data/releases/download/fotmob_match_details/47_match_details.csv'
FIELDS={'minutes_played':'source_minutes','goals':'source_goals','matchstats.headers.tackles':'tackles','shot_blocks':'blocks','clearances':'clearances','interceptions':'interceptions','recoveries':'recoveries'}
EXPECTED={x['match_id']:x['sha256'] for x in json.loads((OUT/'sources.json').read_text())} if (OUT/'sources.json').exists() else {}

def manifest():
    RAW.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
    path=RAW/'fotmob_47.csv'
    if not path.exists(): urllib.request.urlretrieve(ARCHIVE,path)
    a=pd.read_csv(path,low_memory=False)
    a=a[['match_id','match_time_utc','home_team','away_team']].drop_duplicates()
    a['date']=pd.to_datetime(a.match_time_utc,format='%a, %b %d, %Y, %H:%M UTC',utc=True).dt.strftime('%Y-%m-%d')
    a['home']=a.home_team.replace(ALIASES);a['away']=a.away_team.replace(ALIASES)
    f=pd.read_csv(R/'project/data/2021-22_fixtures.csv');t=pd.read_csv(R/'project/data/2021-22_teams.csv').set_index('id')
    f['home']=f.team_h.map(t.name);f['away']=f.team_a.map(t.name);f['date']=pd.to_datetime(f.kickoff_time,utc=True).dt.strftime('%Y-%m-%d')
    z=f.merge(a[['match_id','date','home','away']],on=['date','home','away'],how='left',validate='one_to_one')
    gaps=pd.read_csv(P.parent/'gap_repair/results/remaining_matches.csv')
    target=set(gaps.loc[gaps.season=='2021-22','fixture'])
    z['purpose']=z.id.map(lambda x:'gap' if x in target else 'control')
    controls=z[z.purpose=='control'].sort_values(['date','id'])
    # Fixed evenly spaced complete-fixture controls; selection never uses outcomes.
    ids=controls.iloc[[i*(len(controls)-1)//19 for i in range(20)]].id
    z=z[(z.purpose=='gap')|z.id.isin(ids)].copy()
    assert len(z[z.purpose=='gap'])==76 and z.match_id.notna().all()
    z['match_id']=z.match_id.astype(int)
    z=z[['id','code','event','pulse_id','kickoff_time','date','home','away','team_h_score','team_a_score','match_id','purpose']]
    z.to_csv(OUT/'fixture_manifest.csv',index=False)
    return z

def parse(d,fixture):
    g=d['general'];assert int(g['matchId'])==int(fixture['match_id']) and g['leagueId']==47
    assert pd.to_datetime(g['matchTimeUTCDate'],utc=True).strftime('%Y-%m-%d')==fixture['date']
    assert ALIASES.get(g['homeTeam']['name'],g['homeTeam']['name'])==fixture['home']
    assert ALIASES.get(g['awayTeam']['name'],g['awayTeam']['name'])==fixture['away']
    assert g['finished'] and [x['score'] for x in d['header']['teams']]==[fixture['team_h_score'],fixture['team_a_score']]
    rows=[]
    for player in d['content'].get('playerStats',{}).values():
        code=player.get('optaId')
        if not code:continue
        row={'fixture':fixture['id'],'match_id':fixture['match_id'],'purpose':fixture['purpose'],'code':int(code),'fotmob_id':player['id'],'name':player['name'],'source_team':ALIASES.get(player.get('teamName'),player.get('teamName'))}
        for group in player.get('stats',[]):
            for metric in group.get('stats',{}).values():
                key=metric.get('key')
                if key in FIELDS:
                    value=metric.get('stat',{}).get('value')
                    dest=FIELDS[key]
                    assert dest not in row or row[dest]==value
                    row[dest]=value
        rows.append(row)
    assert rows
    return rows

def fetch(fixture):
    mid=fixture['match_id'];path=RAW/f'fotmob_{mid}.json';url=f'https://www.fotmob.com/api/data/matchDetails?matchId={mid}'
    if not path.exists():
        with urllib.request.urlopen(url,timeout=30) as response: data=response.read()
        path.write_bytes(data)
    data=path.read_bytes()
    if mid in EXPECTED:assert hashlib.sha256(data).hexdigest()==EXPECTED[mid], f'Source revision changed for {mid}; review before replacing frozen data'
    rows=parse(json.loads(data),fixture)
    return rows,{'fixture':fixture['id'],'match_id':mid,'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def run():
    z=manifest();rows=[];sources=[];errors=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs={pool.submit(fetch,row):row for row in z.to_dict('records')}
        for i,job in enumerate(as_completed(jobs),1):
            f=jobs[job]
            try:
                a,b=job.result();rows.extend(a);sources.append(b)
            except urllib.error.HTTPError as e:
                errors.append({'fixture':f['id'],'match_id':f['match_id'],'error':str(e)})
                if e.code in (401,403,429):
                    for pending in jobs:pending.cancel()
                    raise
            except Exception as e:errors.append({'fixture':f['id'],'match_id':f['match_id'],'error':repr(e)})
            if i%10==0:print(f'{i}/{len(jobs)} matches, {len(errors)} errors',flush=True)
    (OUT/'fetch_errors.json').write_text(json.dumps(errors,indent=2)+'\n')
    assert not errors, 'Incomplete download: raw cache retained, frozen normalized data not replaced'
    pd.DataFrame(rows).sort_values(['fixture','code']).reindex(columns=['fixture','match_id','purpose','code','fotmob_id','name','source_team']+list(FIELDS.values())).to_csv(OUT/'fotmob_players.csv',index=False)
    (OUT/'sources.json').write_text(json.dumps(sorted(sources,key=lambda x:x['fixture']),indent=2)+'\n')
    print('completed',len(sources),'matches;',len(rows),'player rows;',len(errors),'errors',flush=True)

if __name__=='__main__':run()
