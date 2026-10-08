"""Exact season exhaustion proves omitted team-match block totals are zero."""
from pathlib import Path
import gzip
import hashlib
import json
import math
import pandas as pd

P = Path(__file__).resolve().parent
B = P.parent.parent
R = B.parent.parent
K = ['season', 'fixture', 'code']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def integer(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0 and int(value) == value

def exhaust(total, values, fixture_ids):
    if len(values) != 38 or len(fixture_ids) != 38 or len(set(fixture_ids)) != 38:
        return None, 'incomplete_or_duplicate_fixture_scope'
    if not integer(total):
        return None, 'missing_or_invalid_explicit_season_total'
    explicit = [value for value in values if value is not None and not pd.isna(value)]
    if not all(integer(value) for value in explicit):
        return None, 'invalid_match_counter'
    if sum(explicit) != total:
        return None, 'positive_residual_or_aggregate_conflict'
    return [0 if value is None or pd.isna(value) else int(value) for value in values], 'exact_season_exhaustion'

def save(frame, name):
    raw = frame.to_csv(index=False).encode()
    (P / name).write_bytes(gzip.compress(raw, mtime=0) if name.endswith('.gz') else raw)

def freeze_inputs():
    inp = P / 'inputs'
    parent = json.loads((inp / 'parent_CURRENT.json').read_text())
    files = [P / 'protocol.json', P / 'plan.json', P / 'collect.py', inp / 'sources.json',
             inp / 'parent_CURRENT.json', P.parent / 'season_conservation/inputs/full_team_totals.csv',
             R / 'training_dataset/scoring/results/historical_inventory.csv.xz',
             R / 'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz']
    files += [P / item['file'] for item in json.loads((inp / 'sources.json').read_text())]
    files += [B / parent[key] for key in ['requirements', 'player_match_readiness', 'match_readiness']]
    manifest = {'source_observed_date': '2026-10-09',
                'files': {str(f.relative_to(R)): digest(f) for f in files}}
    path = inp / 'manifest.json'
    raw = (json.dumps(manifest, indent=2) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == raw, 'Frozen source inputs changed'
    path.write_bytes(raw)

def main():
    freeze_inputs()
    parent = json.loads((P / 'inputs/parent_CURRENT.json').read_text())
    assert digest(B / parent['requirements']) == parent['requirements_sha256']
    totals = pd.read_csv(P.parent / 'season_conservation/inputs/full_team_totals.csv')
    assert not totals.duplicated(['season', 'fixture', 'side']).any()
    assert totals.groupby('season').fixture.nunique().eq(380).all()
    source_totals = []
    sources = json.loads((P / 'inputs/sources.json').read_text())
    plan = json.loads((P / 'plan.json').read_text())
    assert len(sources) == len(plan) == 6
    for source, expected in zip(sources, plan):
        assert all(source[key] == expected[key] for key in expected)
        path = P / source['file']
        assert digest(path) == source['sha256']
        data = json.loads(path.read_text())
        page = data['stats']['pageInfo']
        entries = data['stats']['content']
        assert page['page'] == 0 and page['numPages'] == 1 and page['numEntries'] == len(entries) == 20
        assert len({int(row['owner']['id']) for row in entries}) == 20
        expected_teams = set(totals.loc[totals.season.eq(source['season']), 'primary_team_id'])
        assert {int(row['owner']['id']) for row in entries} == expected_teams
        for row in entries:
            assert row['name'] == 'outfielder_block'
            assert integer(row['value'])
            source_totals.append(dict(season=source['season'], primary_team_id=int(row['owner']['id']),
                                      season_total=int(row['value'])))
    season_values = pd.DataFrame(source_totals).set_index(['season', 'primary_team_id']).season_total.to_dict()
    groups, proved = [], []
    for key, group in totals.groupby(['season', 'primary_team_id'], sort=True):
        group = group.sort_values('fixture')
        values, reason = exhaust(season_values.get(key), group.outfielder_block.tolist(), group.fixture.tolist())
        groups.append(dict(season=key[0], primary_team_id=int(key[1]), fixtures=len(group),
            explicit_season_total=season_values.get(key), known_match_sum=group.outfielder_block.sum(min_count=1),
            omitted_match_totals=int(group.outfielder_block.isna().sum()), qualified=values is not None, reason=reason))
        if values is None:
            continue
        for (_, row), value in zip(group.iterrows(), values):
            proved.append(dict(season=row.season, fixture=int(row.fixture), side=row.side,
                primary_team_id=int(row.primary_team_id), date=row.date, home=row.home, away=row.away,
                home_score=int(row.home_score), away_score=int(row.away_score),
                explicit_match_total=row.outfielder_block, block_total=value,
                proof='explicit_match_total' if pd.notna(row.outfielder_block) else 'exact_season_exhaustion'))
    save(pd.DataFrame(groups), 'season_conservation.csv')
    proved = pd.DataFrame(proved)
    save(proved, 'team_gates.csv')
    native = pd.read_csv(R / 'training_dataset/scoring/results/historical_inventory.csv.xz',
                         usecols=K + ['was_home', 'historical_team', 'team_h_score', 'team_a_score', 'kickoff_time'],
                         low_memory=False)
    native = native[native.season.isin(totals.season)]
    assert native.was_home.isin([True, False]).all()
    native['side'] = native.was_home.map({True: 'home', False: 'away'})
    joined = native.merge(proved, on=['season', 'fixture', 'side'], validate='many_to_one')
    assert joined.historical_team.eq(joined.home.where(joined.side.eq('home'), joined.away)).all()
    assert joined.team_h_score.eq(joined.home_score).all() and joined.team_a_score.eq(joined.away_score).all()
    assert joined.kickoff_time.str[:10].eq(joined.date).all()
    pred = joined[joined.block_total.eq(0)][K + ['side', 'primary_team_id', 'explicit_match_total', 'block_total', 'proof']].copy()
    pred['value'] = 0
    pred['inventory_proof'] = 'whole_team_zero_blocks_with_explicit_season_exhaustion'
    pred = pred.sort_values(K)
    assert not pred.duplicated(K).any()
    save(pred, 'predictions.csv.gz')
    files = [P / 'inputs/manifest.json', Path(__file__).resolve(), P / 'predictions.csv.gz',
             P / 'season_conservation.csv', P / 'team_gates.csv']
    freeze = {'files': {str(x.relative_to(R)): digest(x) for x in files},
              'closed_goal_line_outcomes_read_by_prediction': False}
    path = P / 'prediction_freeze.json'
    payload = (json.dumps(freeze, indent=2) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == payload
    path.write_bytes(payload)
    print({'complete_season_team_groups': sum(x['qualified'] for x in groups),
           'zero_team_matches': int(proved.block_total.eq(0).sum()), 'native_zero_predictions': len(pred)})

if __name__ == '__main__':
    main()
