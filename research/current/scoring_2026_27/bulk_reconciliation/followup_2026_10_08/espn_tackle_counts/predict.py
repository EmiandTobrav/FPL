"""Keep explicit source counters and exact native duration gates."""
import json,math
import pandas as pd
from prepare import P,K,digest,save

def number(v):
    return int(v) if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 and v==int(v) else None

def main():
    freeze=json.loads((P/'selection_freeze.json').read_text())
    for n,h in freeze['files'].items():assert digest(P/n)==h,n
    sources=json.loads((P/'inputs/sources.json').read_text())
    for s in sources:assert digest(P/s['file'])==s['sha256']
    n=pd.read_csv(P/'inputs/native_players.csv.gz');b=pd.read_csv(P/'inputs/player_bridge.csv',dtype={'espn_player_id':str,'espn_event_id':str,'espn_team_id':str})
    bad=b.duplicated(K[:3],keep=False)|b.duplicated(K[:2]+['espn_player_id'],keep=False)
    nc=b.groupby(['season','code']).espn_player_id.nunique();np=b.groupby(['season','espn_player_id']).code.nunique()
    bad|=pd.Series([nc[(r.season,r.code)]!=1 or np[(r.season,r.espn_player_id)]!=1 for r in b.itertuples()],index=b.index)
    x=n.merge(b[~bad],on=K[:3],how='left',validate='one_to_one');rows=[];gates=[]
    for r in x.itertuples():
        why=[];s={}
        if pd.isna(r.espn_player_id):why.append('identity_unresolved')
        else:
            data=json.loads((P/f'inputs/raw/stats_{r.espn_event_id}_{r.espn_player_id}.json').read_bytes())
            assert '/athletes/'+str(r.espn_player_id)+'?' in data['athlete']['$ref']
            assert '/events/'+str(r.espn_event_id)+'/competitions/'+str(r.espn_event_id)+'?' in data['competition']['$ref']
            entries=[q for c in data.get('splits',{}).get('categories',[]) for q in c.get('stats',[])];s={q['name']:number(q.get('value')) for q in entries}
            if len(s)!=len(entries):why.append('duplicate_counter')
            if s.get('appearances')!=1:why.append('appearance_unknown')
            if s.get('minutes') is None or s['minutes']!=r.minutes:why.append('native_minute_mismatch')
            total=s.get('totalTackles');won=s.get('effectiveTackles')
            if total is None or won is None or won>total:why.append('invalid_or_missing_tackle_counter')
        gates.append(dict(season=r.season,fixture=r.fixture,code=r.code,scope=r.scope,eligible=not why,reasons=';'.join(why),native_minutes=r.minutes,source_minutes=s.get('minutes'),total_tackles=s.get('totalTackles'),won_tackles=s.get('effectiveTackles')))
        if why:continue
        for field,v in [('total_tackles',total),('won_tackles',won),('legacy_net_tackles',2*won-total)]:rows.append(dict(season=r.season,fixture=r.fixture,code=r.code,scope=r.scope,field=field,value=v,espn_player_id=r.espn_player_id))
    save(pd.DataFrame(gates),P/'player_gates.csv');save(pd.DataFrame(rows),P/'predictions.csv.gz')
    files=['protocol.json','prepare.py','collect.py','predict.py','selection_freeze.json','plan.csv','inputs/native_players.csv.gz','inputs/fixture_plan.csv','inputs/primary_identities.csv','inputs/parent_CURRENT.json','inputs/player_bridge.csv','inputs/sources.json','player_gates.csv','predictions.csv.gz']
    record={'files':{n:digest(P/n) for n in files},'sources':sources}
    f=P/'prediction_freeze.json'
    if f.exists():assert json.loads(f.read_text())==record
    f.write_text(json.dumps(record,indent=2)+'\n');print(pd.DataFrame(rows).groupby(['scope','field']).size().to_dict());print(pd.DataFrame(gates).reasons.value_counts().to_dict())

if __name__=='__main__':main()
