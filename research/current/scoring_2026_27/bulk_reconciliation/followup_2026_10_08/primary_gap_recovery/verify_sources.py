from pathlib import Path
import pandas as pd,json,hashlib
P=Path(__file__).resolve().parent;K=['season','fixture','code'];roster=[]
for r in pd.read_csv(P/'fixture_plan.csv').itertuples():
 d=json.loads((P/f'inputs/fixture_{r.pulse_id}.json').read_text());assert d['id']==r.pulse_id and int(d['altIds']['opta'][1:])==r.fixture_code and d['status']=='C';assert d['teams'][0]['team']['id']==r.home_primary_id and d['teams'][1]['team']['id']==r.away_primary_id and d['teams'][0]['score']==r.home_score and d['teams'][1]['score']==r.away_score;assert pd.to_datetime(d['kickoff']['millis'],unit='ms',utc=True).strftime('%Y-%m-%d')==r.date
 on={e['personId'] for e in d['events'] if e['type']=='S' and e['description']=='ON'}
 for team in d['teamLists']:
  assert team['teamId'] in [r.home_primary_id,r.away_primary_id] and len(team['lineup'])==11
  for p in team['lineup']+team['substitutes']:
   if p not in team['lineup'] and p['id'] not in on:continue
   roster.append(dict(season=r.season,fixture=r.fixture,code=int(p['altIds']['opta'][1:]),pl_player_id=p['id'],pulse_id=r.pulse_id,primary_team_id=team['teamId']))
a=pd.DataFrame(roster);b=pd.read_csv(P/'roster.csv');assert not a.duplicated(K).any();pd.testing.assert_frame_equal(a.sort_values(K).reset_index(drop=True),b[a.columns].sort_values(K).reset_index(drop=True),check_dtype=False)
rows=json.loads((P/'players.json').read_text());assert len(rows)==len(a)
for r in rows:
 d=json.loads((P/f"inputs/player_{r['pl_player_id']}_{r['pulse_id']}.json").read_text());assert d['entity']['id']==r['pl_player_id'] and int(d['entity']['altIds']['opta'][1:])==r['code'];s={x['name']:x['value'] for x in d['stats']};assert len(s)==len(d['stats']) and s.get('appearances')==1 and all(r[k]==v for k,v in s.items())
for r in json.loads((P/'sources.json').read_text()):assert hashlib.sha256((P/r['file']).read_bytes()).hexdigest()==r['sha256']
print('Verified',len(a),'player identities and full stat projections, 24 fixture identities, all source hashes')
