"""Exact season exhaustion plus an opponent big-chance subset; no scores."""
import gzip,hashlib,json,math
from pathlib import Path
import pandas as pd
P=Path(__file__).resolve().parent;B=P.parents[1];R=P.parents[3];K=['season','fixture','code','field']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(x,p):p.write_bytes(gzip.compress(x.to_csv(index=False).encode(),mtime=0))
def valid(x):return x is not None and math.isfinite(x) and x>=0 and x%1==0

def main():
    deps={};parent=json.loads((P/'inputs/parent_CURRENT.json').read_text())
    def pin(f):deps[str(f.relative_to(R))]=digest(f)
    for f in [B/parent['requirements'],B/parent['player_match_readiness'],B/parent['match_readiness'],B/'full_sources.json',B/'full_team_totals.csv',R/'training_dataset/scoring/results/historical_inventory.csv.xz']:pin(f)
    assert digest(B/parent['requirements'])==parent['requirements_sha256']
    plan=json.loads((P/'plan.json').read_text());teams=pd.read_csv(B/'full_team_totals.csv').set_index(['season','fixture','side'])
    totals={};rows=[]
    for source in json.loads((P/'sources.json').read_text()):
        f=P/source['file'];assert digest(f)==source['sha256'];d=json.loads(f.read_text());assert d['entity']=='big_chance_missed' and d['stats']['pageInfo']['numPages']==1
        content=d['stats']['content'];assert len(content)==20
        for x in content:
            key=(source['season'],int(x['owner']['id']));assert key not in totals and valid(x['value']);totals[key]=int(x['value'])
    for s in json.loads((B/'full_sources.json').read_text()):
        if s['season'] not in plan['seasons']:continue
        f=B/s['file'];raw=gzip.decompress(f.read_bytes()) if f.suffix=='.gz' else f.read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256'];pin(f);d=json.loads(raw);e=d['entity']
        assert e['status']=='C' and e['gameweek']['compSeason']['id']==plan['seasons'][s['season']]
        for i,side in enumerate(['home','away']):
            t=teams.loc[(s['season'],s['fixture'],side)];tid=int(e['teams'][i]['team']['id']);assert tid==t.primary_team_id and e['id']==t.pulse_id
            assert e['teams'][0]['score']==t.home_score and e['teams'][1]['score']==t.away_score
            assert pd.to_datetime(e['kickoff']['millis'],unit='ms',utc=True).strftime('%Y-%m-%d')==t.date
            entries=d['data'][str(tid)]['M'];stats={v['name']:v['value'] for v in entries};assert len(stats)==len(entries)
            value=stats.get('big_chance_missed');assert value is None or valid(value)
            rows.append(dict(season=s['season'],fixture=s['fixture'],primary_team_id=tid,side=side,big_chance_missed=value))
    matches=pd.DataFrame(rows);assert not matches.duplicated(['season','fixture','side']).any();proofs=[]
    for key,g in matches.groupby(['season','primary_team_id']):
        total=totals.get(key);known=g.big_chance_missed.sum();qualified=len(g)==38 and valid(total) and known==total
        proofs.append(dict(season=key[0],primary_team_id=key[1],matches=len(g),explicit_matches=int(g.big_chance_missed.notna().sum()),known_sum=known,season_total=total,qualified=qualified))
    proofs=pd.DataFrame(proofs);matches=matches.merge(proofs[['season','primary_team_id','qualified']],on=['season','primary_team_id'],validate='many_to_one')
    matches['zero_bound']=matches.qualified & (matches.big_chance_missed.isna()|matches.big_chance_missed.eq(0))
    req=pd.read_csv(B/parent['requirements'],low_memory=False);native=pd.read_csv(R/'training_dataset/scoring/results/historical_inventory.csv.xz',usecols=['season','fixture','code','was_home'])
    targets=req[req.field.eq('big_chance_saves')][K].merge(native,on=K[:3],validate='one_to_one');targets['opponent_side']=targets.was_home.map({True:'away',False:'home'});assert targets.opponent_side.notna().all()
    bounds=targets.merge(matches,many_to_many=None) if False else targets.merge(matches,left_on=['season','fixture','opponent_side'],right_on=['season','fixture','side'],validate='many_to_one')
    bounds=bounds[bounds.zero_bound].copy();bounds['value']=0
    pending=req[req.is_open & req.status.eq('missing_data') & req.value.isna()][K]
    pred=bounds.merge(pending,on=K,validate='one_to_one')
    save(proofs,P/'season_proofs.csv.gz');save(matches,P/'match_bounds.csv.gz');save(bounds,P/'all_counter_bounds.csv.gz');save(pred,P/'predictions.csv.gz')
    f=P/'dependencies.json'
    if f.exists():assert json.loads(f.read_text())==deps
    f.write_text(json.dumps(deps,indent=2)+'\n')
    names=['predict.py','plan.json','sources.json','inputs/parent_CURRENT.json','dependencies.json','season_proofs.csv.gz','match_bounds.csv.gz','all_counter_bounds.csv.gz','predictions.csv.gz']+[s['file'] for s in json.loads((P/'sources.json').read_text())]
    frozen={n:digest(P/n) for n in names};f=P/'prediction_freeze.json'
    if f.exists():assert json.loads(f.read_text())==frozen
    f.write_text(json.dumps(frozen,indent=2)+'\n')
    print('Qualified team-seasons',int(proofs.qualified.sum()),'of',len(proofs),'zero-bound keeper rows',len(bounds),'missing candidates',len(pred));print(pred[K+['value']].to_string(index=False))
if __name__=='__main__':main()
