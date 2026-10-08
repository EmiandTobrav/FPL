from pathlib import Path
import pandas as pd,json,hashlib,gzip
P=Path(__file__).resolve().parent;S=P.parent

def save(df,n):(P/n).write_bytes(gzip.compress(df.to_csv(index=False).encode(),mtime=0) if n.endswith('.gz') else df.to_csv(index=False).encode())
def conserve(total,known):
 if total is None or pd.isna(total):return False
 if total<0 or total%1 or any(v<0 or v%1 for v in known):raise ValueError('Nonnegative integer counts required')
 return total==sum(known)
def main():
 people=pd.read_csv(S/'tackle_event_recovery_v2/inputs/players.csv.gz');assert not people.duplicated(['match_id','player_id']).any();teams=pd.read_csv(S/'season_conservation/inputs/full_team_totals.csv');sources=json.loads((P/'inputs/sources.json').read_text());proofs=[];good=set()
 for src in sources:
  raw=(P/src['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==src['sha256'];d=json.loads(raw);assert d['entity']['id']==src['pulse_id'];fixture=teams[teams.pulse_id.eq(src['pulse_id'])];assert len(fixture)==2
  for r in fixture.itertuples():
   primary_id=int(r.primary_team_id);sideindex=0 if r.side=='home' else 1;assert d['entity']['teams'][sideindex]['team']['id']==primary_id
   fields={x['name']:x['value'] for x in d['data'].get(str(primary_id),{}).get('M',[])};total=fields.get('total_contest');roster=people[people.match_id.eq(r.match_id)&people.team_position.eq(r.side)];known=roster.totalContest.dropna().tolist();ok=len(roster)>0 and roster.team_id.nunique()==1 and conserve(total,known)
   tid=roster.team_id.iloc[0] if len(roster) else None
   proofs.append(dict(season=r.season,fixture=r.fixture,match_id=r.match_id,team_id=tid,pulse_id=src['pulse_id'],primary_team_id=primary_id,primary_total=total,known_sum=sum(known),known_players=len(known),roster_players=len(roster),exhausted=ok,scope=src['scope']))
   if ok:good.add((r.match_id,tid))
 save(pd.DataFrame(proofs),'match_conservation.csv')
 e=pd.read_csv(S/'tackle_event_recovery_v2/inputs/duels.csv.gz',low_memory=False);pairs=pd.read_csv(S/'tackle_event_recovery_v2/paired_events.csv.gz',low_memory=False);gates=pd.read_csv(S/'tackle_event_recovery_v2/team_gates.csv');goodteams=set(map(tuple,gates.loc[gates.complete,['match_id','recipient_team_id']].to_numpy()))
 attempts=e[e.type_id.eq(3)].groupby(['match_id','team_id','player_id']).size().to_dict();lost=e[e.type_id.eq(50)|(e.type_id.eq(3)&~e.outcome.eq(1))];unpaired=lost.merge(pairs[['match_id','event_id_v']].drop_duplicates(),left_on=['match_id','event_id'],right_on=['match_id','event_id_v'],how='left');blocked=set(map(tuple,unpaired.loc[unpaired.event_id_v.isna(),['match_id','team_id','player_id']].to_numpy()));values=pairs.groupby(['match_id','team_id_v','player_id_v']).size().to_dict();smothers=pairs[pairs.type_id_t.eq(54)].groupby(['match_id','team_id_v','player_id_v']).size().to_dict();rows=[]
 for r in people.itertuples():
  key=(r.match_id,r.team_id,r.player_id)
  if pd.isna(r.totalContest) and (r.match_id,r.team_id) in good&goodteams and key not in blocked and attempts.get(key,0)==0 and smothers.get(key,0)==0:
   rows.append(dict(season=r.season,fixture=r.fixture,match_id=r.match_id,team_id=r.team_id,player_id=r.player_id,value=values.get(key,0)))
 save(pd.DataFrame(rows),'predictions.csv.gz')
 files=[P/'predict.py',P/'protocol.json',P/'inputs/target_fixtures.csv',P/'inputs/sources.json']+[P/s['file'] for s in sources]+[S/'tackle_event_recovery_v2'/n for n in ['inputs/players.csv.gz','inputs/duels.csv.gz','paired_events.csv.gz','team_gates.csv','prediction_freeze.json']]+[S/'season_conservation/inputs/full_team_totals.csv']
 f={'inputs':{str(p.relative_to(S)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'outputs':{n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['match_conservation.csv','predictions.csv.gz']}}
 if (P/'freeze.json').exists():assert json.loads((P/'freeze.json').read_text())==f
 (P/'freeze.json').write_text(json.dumps(f,indent=2)+'\n');print('Predictions',len(rows))
if __name__=='__main__':main()
