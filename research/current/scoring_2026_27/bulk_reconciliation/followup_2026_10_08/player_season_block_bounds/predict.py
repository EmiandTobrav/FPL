"""Freeze player-season subset predictions before any outcome comparison."""
import gzip
import json
from pathlib import Path
import pandas as pd
from collect import P, B, digest, write

R = B.parents[1]
K = ['season', 'fixture', 'code']

def save(frame, name):
    raw = frame.to_csv(index=False).encode()
    (P / name).write_bytes(gzip.compress(raw, mtime=0) if name.endswith('.gz') else raw)

def main():
    for name, sha in json.loads((P / 'selection_freeze.json').read_text()).items():
        assert digest(P / name) == sha
    plan = json.loads((P / 'plan.json').read_text())
    parent = json.loads((P / 'inputs/parent_CURRENT.json').read_text())
    assert digest(B / parent['requirements']) == parent['requirements_sha256']
    ledger = pd.read_csv(B / parent['requirements'], low_memory=False)
    population = ledger[ledger.field.eq('goal_line_clearances')][K + ['position']]
    assert not population.duplicated(K).any()
    sources = json.loads((P / 'sources.json').read_text())
    dependencies = {str((B / parent['requirements']).relative_to(R)): parent['requirements_sha256']}
    predictions, groups = [], []
    for source in sources:
        season = source['season']
        path = P / source['file']
        assert digest(path) == source['sha256']
        team_path = B / plan['team_files'][season]
        assert digest(team_path) == plan['team_sha256'][season]
        ranked, team = json.loads(path.read_text()), json.loads(team_path.read_text())
        assert ranked['entity'] == team['entity'] == 'outfielder_block'
        assert ranked['stats']['pageInfo']['numPages'] == team['stats']['pageInfo']['numPages'] == 1
        assert len(ranked['stats']['content']) == ranked['stats']['pageInfo']['numEntries']
        assert len(team['stats']['content']) == team['stats']['pageInfo']['numEntries'] == 20
        codes = {}
        for x in ranked['stats']['content']:
            assert x['name'] == 'outfielder_block'
            code = int(x['owner']['altIds']['opta'].lstrip('p'))
            assert code not in codes and x['value'] >= 0 and int(x['value']) == x['value']
            codes[code] = int(x['value'])
        assert all(x['value'] >= 0 and int(x['value']) == x['value'] for x in team['stats']['content'])
        psum, tsum = sum(codes.values()), sum(int(x['value']) for x in team['stats']['content'])
        exact = psum == tsum
        groups.append(dict(season=season, ranked_player_sum=psum, team_sum=tsum, residual=tsum-psum, exact=exact))
        dependencies[str(team_path.relative_to(R))] = digest(team_path)
        if not exact:
            continue
        appearances = R / 'scoring_2026_27/delta_input_audit/inputs/primary' / ('players_' + season + '.json')
        body = json.loads(appearances.read_text())
        assert body['entity'] == 'appearances' and body['stats']['pageInfo']['numPages'] == 1
        assert len(body['stats']['content']) == body['stats']['pageInfo']['numEntries']
        roster = {}
        for x in body['stats']['content']:
            assert x['name'] == 'appearances' and x['value'] >= 0 and int(x['value']) == x['value']
            code = int(x['owner']['altIds']['opta'].lstrip('p'))
            assert code not in roster
            roster[code] = (int(x['owner']['id']), int(x['value']))
        active = {code: row[0] for code, row in roster.items() if row[1] > 0}
        assert set(codes).issubset(active)
        dependencies[str(appearances.relative_to(R))] = digest(appearances)
        selected = population[population.season.eq(season) & population.position.isin(['DEF', 'MID', 'FWD']) & population.code.isin(active)].copy()
        selected['season_blocks'] = selected.code.map(codes)
        # Omission implies zero only after exact whole-league exhaustion above.
        selected = selected[selected.season_blocks.isna() | selected.season_blocks.eq(0)].copy()
        selected['value'] = 0
        selected['proof'] = 'exact_league_player_season_block_exhaustion_outfield_subset'
        predictions.append(selected[K + ['value', 'proof']])
    pred = pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame(columns=K + ['value', 'proof'])
    assert not pred.duplicated(K).any()
    save(pred, 'predictions.csv.gz')
    save(pd.DataFrame(groups), 'season_conservation.csv')
    write(P / 'dependencies.json', dependencies)
    write(P / 'prediction_freeze.json', {name: digest(P / name) for name in ['plan.json', 'sources.json', 'selection_freeze.json', 'dependencies.json', 'predictions.csv.gz', 'season_conservation.csv']})
    print('Frozen predictions', len(pred), 'with complete failed season residual retained')

if __name__ == '__main__':
    main()
