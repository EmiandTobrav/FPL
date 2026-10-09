from pathlib import Path
import gzip, hashlib, json
import pandas as pd

P = Path(__file__).resolve().parent
B = P.parents[1]
R = P.parents[3]
K = ['season', 'fixture', 'code', 'field']

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(x, p): p.write_bytes(gzip.compress(x.to_csv(index=False).encode(), mtime=0) if p.suffix == '.gz' else x.to_csv(index=False).encode())

def main():
    I = P / 'inputs'; I.mkdir(exist_ok=True)
    parent = json.loads((B / 'CURRENT.json').read_text())
    assert digest(B / parent['requirements']) == parent['requirements_sha256']
    req = pd.read_csv(B / parent['requirements'], low_memory=False)
    target = req[req.is_open & req.status.eq('missing_data') & req.field.isin(['penalty_goals', 'fouls_won'])][K[:2]].drop_duplicates()
    rows = [dict(season=r.season, fixture=int(r.fixture), scope='target') for r in target.itertuples()]
    pen = req[req.field.eq('penalty_goals')]
    ag = pen.groupby(K[:2]).agg(any_open=('is_open','any'), positive=('value', lambda x: x.gt(0).any()))
    archive_path = R / 'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz'
    archive = pd.read_csv(archive_path)
    native2025 = archive[archive.season.eq('2025-26')].groupby(K[:2]).attPenGoal.apply(lambda x: x.gt(0).any())
    ag = pd.concat([ag,pd.DataFrame({'any_open':False,'positive':native2025})])
    targetkeys = set(map(tuple,target.to_numpy()))
    for year in ['2019-20','2020-21','2022-23','2024-25','2025-26']:
        for positive in [False,True]:
            pool = [f for (s,f),r in ag.sort_index().iterrows() if s == year and not r.any_open and r.positive == positive and (s,f) not in targetkeys]
            assert len(pool) >= 3
            rows += [dict(season=year,fixture=int(f),scope='control') for f in pool[:3]]
    plan = pd.DataFrame(rows).sort_values(K[:2]); assert not plan.duplicated(K[:2]).any()
    inventory_path = R / 'training_dataset/scoring/results/historical_inventory.csv.xz'
    hist = pd.read_csv(inventory_path, low_memory=False).merge(plan,on=K[:2],validate='many_to_one')
    inputs = {str(inventory_path.relative_to(R)):digest(inventory_path),str((B/parent['requirements']).relative_to(R)):digest(B/parent['requirements']),str(archive_path.relative_to(R)):digest(archive_path)}
    native = []; metadata = []
    for year,g in plan.groupby('season'):
        pp = R / f'project/data/{year}_players.csv.gz'; ff = R / f'project/data/{year}_fixtures.csv.gz'; tt = R / f'project/data/{year}_teams.csv.gz'
        for f in [pp,ff,tt]: inputs[str(f.relative_to(R))] = digest(f)
        players = pd.read_csv(pp)[['code','first_name','second_name','web_name']]
        assert not players.code.duplicated().any()
        native.append(hist[hist.season.eq(year)].merge(players,on='code',validate='many_to_one')[['season','fixture','code','historical_team','minutes','goals_scored','own_goals','position','first_name','second_name','web_name']])
        fixtures = pd.read_csv(ff).set_index('id'); teams = pd.read_csv(tt).set_index('id').name.to_dict()
        for r in g.itertuples():
            f = fixtures.loc[r.fixture]
            metadata.append(dict(season=year,fixture=r.fixture,scope=r.scope,date=f.kickoff_time[:10],home=teams[f.team_h],away=teams[f.team_a],home_score=int(f.team_h_score),away_score=int(f.team_a_score)))
    save(pd.concat(native,ignore_index=True),I/'native_players.csv.gz')
    save(pd.DataFrame(metadata),P/'plan.csv')
    (I/'parent_CURRENT.json').write_text(json.dumps(parent,indent=2)+'\n')
    record = dict(source_inputs=inputs, plan_sha256=digest(P/'plan.csv'), native_players_sha256=digest(I/'native_players.csv.gz'), protocol_sha256=digest(P/'protocol.json'))
    freeze = P/'selection_freeze.json'
    if freeze.exists(): assert json.loads(freeze.read_text()) == record
    freeze.write_text(json.dumps(record,indent=2)+'\n')
    print(plan.groupby('scope').size().to_dict())

if __name__ == '__main__': main()
