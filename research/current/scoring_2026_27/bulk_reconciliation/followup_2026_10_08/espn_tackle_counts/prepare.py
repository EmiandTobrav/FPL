from pathlib import Path
import json,gzip,hashlib
import pandas as pd

P=Path(__file__).resolve().parent;B=P.parents[1];R=P.parents[3];K=['season','fixture','code','field']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(x,p):
    b=x.to_csv(index=False).encode();p.write_bytes(gzip.compress(b,mtime=0) if p.suffix=='.gz' else b)

def main():
    (P/'inputs').mkdir(exist_ok=True)
    # The identity batch is the pinned next parent; CURRENT publication follows its verification.
    parent=json.loads((B/'CURRENT.json').read_text())
    identity=P.parent/'espn_primary_identity'
    for key,file in [('requirements','requirements.csv.xz'),('remaining_fields','remaining_fields.csv.xz'),('player_match_readiness','player_match_readiness.csv.xz'),('match_readiness','match_readiness.csv')]:
        parent[key]='followup_2026_10_08/espn_primary_identity/results/'+file
    parent['requirements_sha256']=digest(B/parent['requirements']);parent['remaining_fields_sha256']=digest(B/parent['remaining_fields']);parent['open_fields']=11258
    req=pd.read_csv(B/parent['requirements'],low_memory=False)
    targets=req[req.field.eq('won_tackles')&req.status.eq('missing_data')&req.is_open][K[:3]];assert len(targets)==16
    rows=[dict(**r,scope='target') for r in targets.to_dict('records')]
    oldplayers=pd.read_csv(identity/'players.csv.gz');oldplan=pd.read_csv(identity/'plan.csv')
    controls=oldplayers[oldplayers.scope.eq('control') & oldplayers.position.isin(['DEF','MID'])].sort_values(K[:3]).groupby(K[:2]).head(5)
    assert len(controls)==150
    rows += [dict(season=r.season,fixture=r.fixture,code=r.code,scope='control') for r in controls.itertuples()]
    plan=pd.DataFrame(rows).sort_values(K[:3]);assert not plan.duplicated(K[:3]).any()
    histpath=R/'training_dataset/scoring/results/historical_inventory.csv.xz';hist=pd.read_csv(histpath,low_memory=False).merge(plan,on=K[:3],validate='one_to_one')
    native=[];fixtures=[];inputs={str(histpath.relative_to(R)):digest(histpath),str((B/parent['requirements']).relative_to(R)):digest(B/parent['requirements']),str((identity/'players.csv.gz').relative_to(R)):digest(identity/'players.csv.gz')}
    for year,g in hist.groupby('season'):
        pp=R/f'project/data/{year}_players.csv.gz';ff=R/f'project/data/{year}_fixtures.csv.gz';tt=R/f'project/data/{year}_teams.csv.gz'
        for file in [pp,ff,tt]:inputs[str(file.relative_to(R))]=digest(file)
        x=pd.read_csv(pp)[['code','first_name','second_name','web_name']]
        native.append(g.merge(x,on='code',validate='many_to_one')[['season','fixture','code','scope','historical_team','minutes','position','first_name','second_name','web_name','tackles']])
        fs=pd.read_csv(ff).set_index('id');ts=pd.read_csv(tt).set_index('id').name.to_dict()
        for fid in sorted(g.fixture.unique()):
            f=fs.loc[fid];fixtures.append(dict(season=year,fixture=int(fid),date=f.kickoff_time[:10],home=ts[f.team_h],away=ts[f.team_a],home_score=int(f.team_h_score),away_score=int(f.team_a_score)))
    save(pd.concat(native,ignore_index=True),P/'inputs/native_players.csv.gz');save(plan,P/'plan.csv');save(pd.DataFrame(fixtures),P/'inputs/fixture_plan.csv')
    source=P.parent/'primary_gap_recovery/roster.csv';(P/'inputs/primary_identities.csv').write_bytes(source.read_bytes());inputs[str(source.relative_to(R))]=digest(source)
    (P/'inputs/parent_CURRENT.json').write_text(json.dumps(parent,indent=2)+'\n')
    freeze=dict(source_inputs=inputs,files={n:digest(P/n) for n in ['protocol.json','plan.csv','inputs/native_players.csv.gz','inputs/fixture_plan.csv','inputs/primary_identities.csv','inputs/parent_CURRENT.json']})
    (P/'selection_freeze.json').write_text(json.dumps(freeze,indent=2)+'\n');print(plan.scope.value_counts().to_dict())

if __name__=='__main__':main()
