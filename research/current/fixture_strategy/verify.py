from pathlib import Path
import sys,json,gzip,pickle,hashlib
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
import experiment
from fixture_strategy.chips import TYPES
OUT=HERE/'results'

def read(path):return json.loads(gzip.decompress(path.read_bytes()))

def main():
    paths=sorted(OUT.glob('trace_*.json.gz'));assert len(paths)==84,len(paths)
    decisions=0;controls=0;rows=[]
    for path in paths:
        z=read(path);s=z['summary']['season'];state,opening=experiment.opening(s)
        games=pickle.load(open(CURRENT/f'results/games_{s}.pkl','rb'))
        total=sum(r['net'] for r in opening);last=None
        for r in z['trace']:
            gw=r['gw'];p=games[gw]['frame'];prices=p.set_index('pid').market.to_dict();chip=r['chip'] or None
            owned=state['owned'];squad=set(r['squad']);incoming=squad-set(owned);outgoing=set(owned)-squad
            assert incoming==set(r['incoming']) and outgoing==set(r['outgoing'])
            assert len(squad)==15 and len(r['starters'])==11 and set(r['bench'])==squad-set(r['starters'])
            assert r['captain'] in r['starters'] and r['vice'] in r['starters'] and r['captain']!=r['vice']
            assert p.set_index('pid').loc[list(squad)].pos.value_counts().to_dict()=={1:2,2:5,3:5,4:3}
            assert p[p.pid.isin(incoming)].can_buy.all()
            assert not(last=='free_hit' and chip=='free_hit')
            hits=0 if chip in ['wildcard','free_hit'] else 4*max(0,len(incoming)-state['ft']);assert hits==r['hits']
            after=state['bank']+sum(experiment.selling_price(owned[i],prices[i]) for i in outgoing)-sum(prices[i] for i in incoming)
            assert after>=0
            if chip!='free_hit':state['owned']={i:owned.get(i,prices[i]) for i in squad};state['bank']=after
            state['ft']=experiment.next_free(state['ft'],len(incoming),chip)
            assert state['bank']==r['bank'] and state['ft']==r['ft']
            assert r['net']==r['gross']-hits
            assert r['gross']==sum(games[gw]['actual'].get(i,0) for i in r['counted'])+r['captain_bonus']
            total+=r['net'];last=chip;decisions+=1
        assert total==z['summary']['points38']
        for lo,hi in [(5,19),(20,38)]:
            used=[r['chip'] for r in z['trace'] if lo<=r['gw']<=hi and r['chip']]
            if z['summary']['mode']=='no_chips':assert not used
            else:assert sorted(used)==sorted(TYPES),(path,used)
        if z['summary']['model']=='count_h3':
            old=read(CURRENT/f"calendar_counts/results/trace_{s}_calendar_count_h3_{z['summary']['mode']}.json.gz")
            for a,b in zip(z['trace'],old['trace']):
                for key in ['gw','net','squad','starters','bench','captain','vice','bank','ft','transfers']:assert a[key]==b[key],(path,key)
            controls+=1
        rows.append(dict(path=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),**z['summary']))
    a=pd.read_csv(OUT/'forecast_audit.csv')
    for col in ['max_team_time','max_player_time']:assert (pd.to_datetime(a[col],utc=True)<pd.to_datetime(a.cutoff,utc=True)).all()
    for s,r in json.loads((OUT/'coefficients.json').read_text()).items():assert pd.Timestamp(r['max_available'])<pd.Timestamp(r['season_cutoff'])
    paths=[CURRENT/'benchmark.json',CURRENT/'project/results/features.pkl',CURRENT/'calendar_audit/selection.csv',CURRENT/'calendar_audit/source_commits.json']+list((CURRENT/'calendar_audit/snapshots').glob('*.csv.gz'))+list((CURRENT/'results').glob('games_*.pkl'))+list((CURRENT/'decision_specialist/results').glob('gate_*.csv.gz'))+list((CURRENT/'decision_specialist/results').glob('horizon_*.csv.gz'))+list((CURRENT/'project/data').glob('*fixtures.csv'))+list((CURRENT/'project/data').glob('*teams.csv'))+list((CURRENT/'project/data').glob('*gw.csv'))
    (OUT/'verified_inputs.json').write_text(json.dumps({str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.exists()},indent=2))
    pd.DataFrame(rows).to_csv(OUT/'verified_runs.csv',index=False)
    result=dict(season_runs=len(rows),decisions=decisions,exact_archived_calendar_controls=controls,accounting_positions_chips_and_time_checks='passed')
    (OUT/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
