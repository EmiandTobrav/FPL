from pathlib import Path
import sys,json,gzip,hashlib
import pandas as pd
from pairing import pair
P=Path(__file__).resolve().parent;S=P.parent
sys.path.insert(0,str(S/'assist_team_identity'))
from prepare import ALIASES

def save(df,n):
 b=df.to_csv(index=False).encode();(P/n).write_bytes(gzip.compress(b,mtime=0) if n.endswith('.gz') else b)
def main():
 files=[P/n for n in ['pairing.py','predict.py','protocol.json','validation_plan.csv','inputs/players.csv.gz','inputs/duels.csv.gz','inputs/primary/sources.json']]+list((P/'inputs/primary').glob('total_*.json'))+[S/'season_conservation/inputs/full_team_totals.csv',S/'assist_team_identity/prepare.py']
 frozen={str(p.relative_to(S)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 people=pd.read_csv(P/'inputs/players.csv.gz');e=pd.read_csv(P/'inputs/duels.csv.gz',low_memory=False);e['clock']=e.minute*60+e.second
 bridge=people[['season','team_id','team_name']].drop_duplicates();bridge['fpl_name']=bridge.team_name.replace(ALIASES);bridge=bridge[['season','team_id','fpl_name']].drop_duplicates();assert not bridge.duplicated(['season','fpl_name']).any()
 totals=[]
 for src in json.loads((P/'inputs/primary/sources.json').read_text()):
  raw=(P/'inputs/primary'/src['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==src['sha256']
  for r in json.loads(raw)['stats']['content']:totals.append(dict(season=src['season'],metric=src['metric'],fpl_name=ALIASES.get(r['owner']['name'],r['owner']['name']),primary_total=r['value']))
 totals=pd.DataFrame(totals).merge(bridge,on=['season','fpl_name'],validate='many_to_one');assert totals.team_id.notna().all()
 audit=[];complete={}
 for metric,field in [('total_contest','totalContest'),('total_tackle','totalTackle')]:
  sums=people.groupby(['season','team_id'])[field].sum(min_count=1).to_dict()
  for r in totals[totals.metric.eq(metric)].itertuples():
   observed=sums.get((r.season,r.team_id));ok=pd.notna(observed) and observed==r.primary_total and r.primary_total>=0
   audit.append(dict(season=r.season,team_id=r.team_id,metric=metric,primary_total=r.primary_total,known_sum=observed,exhausted=bool(ok)))
   complete[(r.season,r.team_id,field)]=bool(ok)
 for field in ['totalContest','totalTackle']:
  people['complete_'+field]=[v if pd.notna(v) else 0 if complete.get((season,team,field),False) else None for season,team,v in zip(people.season,people.team_id,people[field])]
 save(pd.DataFrame(audit),'season_conservation.csv')
 anchors,pairs=pair(e)
 ids=people.groupby(['match_id','team_id','player_id']).size().to_dict()
 pairs=pairs[[ids.get((r.match_id,r.team_id_t,r.player_id_t),0)==1 and ids.get((r.match_id,r.team_id_v,r.player_id_v),0)==1 for r in pairs.itertuples()]]
 keeper_counts=e[e.type_id.eq(54)].groupby(['match_id','team_id','player_id']).size().to_dict();keeper_source=people.set_index(['match_id','team_id','player_id']).gkSmother.to_dict()
 pairs=pairs[[r.type_id_t==7 or pd.notna(keeper_source.get((r.match_id,r.team_id_t,r.player_id_t))) and keeper_counts.get((r.match_id,r.team_id_t,r.player_id_t))==keeper_source[(r.match_id,r.team_id_t,r.player_id_t)] for r in pairs.itertuples()]]
 side=people[['season','fixture','match_id','team_id','team_position']].drop_duplicates();assert not side.duplicated(['match_id','team_position']).any()
 team=pd.read_csv(S/'season_conservation/inputs/full_team_totals.csv')[['season','fixture','match_id','side','total_tackle']]
 newer=[]
 for (season,fixture,mid,tid,pos),g in people[people.season.eq('2025-26')].groupby(['season','fixture','match_id','team_id','team_position']):
  newer.append(dict(season=season,fixture=fixture,match_id=mid,side=pos,total_tackle=g.complete_totalTackle.sum() if g.complete_totalTackle.notna().all() else None))
 team=pd.concat([team,pd.DataFrame(newer)],ignore_index=True).merge(side,left_on=['season','fixture','match_id','side'],right_on=['season','fixture','match_id','team_position'],how='left',validate='one_to_one')
 rawground=e[e.type_id.eq(7)].groupby(['match_id','team_id']).size().to_dict();pairedground=pairs[pairs.type_id_t.eq(7)].groupby(['match_id','team_id_t']).size().to_dict();partners=side.groupby('match_id').team_id.agg(list).to_dict();gates=[]
 for r in team.itertuples():
  others=[x for x in partners.get(r.match_id,[]) if x!=r.team_id];n=rawground.get((r.match_id,r.team_id),0);npair=pairedground.get((r.match_id,r.team_id),0)
  ok=len(others)==1 and pd.notna(r.total_tackle) and r.total_tackle==n==npair
  gates.append(dict(season=r.season,fixture=r.fixture,match_id=r.match_id,tackling_team_id=r.team_id,recipient_team_id=others[0] if len(others)==1 else None,primary_total=r.total_tackle,tackle_events=n,paired_tackles=npair,complete=ok))
 gates=pd.DataFrame(gates);goodteams=set(map(tuple,gates.loc[gates.complete,['match_id','recipient_team_id']].to_numpy()))
 attempts=e[e.type_id.eq(3)].groupby(['match_id','team_id','player_id']).size().to_dict()
 lost=e[e.type_id.eq(50)|(e.type_id.eq(3)&~e.outcome.eq(1))];unpaired=lost.merge(pairs[['match_id','event_id_v']].drop_duplicates(),left_on=['match_id','event_id'],right_on=['match_id','event_id_v'],how='left');blocked=set(map(tuple,unpaired.loc[unpaired.event_id_v.isna(),['match_id','team_id','player_id']].to_numpy()))
 values=pairs.groupby(['match_id','team_id_v','player_id_v']).size().to_dict();smothers=pairs[pairs.type_id_t.eq(54)].groupby(['match_id','team_id_v','player_id_v']).size().to_dict();out=[]
 for r in people.itertuples():
  key=(r.match_id,r.team_id,r.player_id)
  if (r.match_id,r.team_id) in goodteams and key not in blocked and pd.notna(r.complete_totalContest) and attempts.get(key,0)==r.complete_totalContest:
   out.append(dict(season=r.season,fixture=r.fixture,match_id=r.match_id,team_id=r.team_id,player_id=r.player_id,value=values.get(key,0),smother_contributions=smothers.get(key,0)))
 save(gates,'team_gates.csv');save(pairs,'paired_events.csv.gz');save(pd.DataFrame(out),'player_predictions.csv.gz')
 record=dict(inputs=frozen,outputs={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['season_conservation.csv','team_gates.csv','paired_events.csv.gz','player_predictions.csv.gz']})
 if (P/'prediction_freeze.json').exists():assert json.loads((P/'prediction_freeze.json').read_text())==record
 (P/'prediction_freeze.json').write_text(json.dumps(record,indent=2)+'\n');print(pd.DataFrame(out).groupby('season').size().to_string())
if __name__=='__main__':main()
