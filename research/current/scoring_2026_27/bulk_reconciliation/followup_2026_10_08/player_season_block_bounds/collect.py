"""Small new player-season source route; require exact league conservation."""
import hashlib
import json
import urllib.request
from pathlib import Path

P = Path(__file__).resolve().parent
B = P.parents[1]
SEASONS = {'2019-20': 274, '2020-21': 363, '2021-22': 418, '2024-25': 719}
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, indent=2) + '\n')

def prepare():
    parent = json.loads((B / 'CURRENT.json').read_text())
    write(P / 'inputs/parent_CURRENT.json', parent)
    team_files = {s: 'followup_2026_10_08/goal_line_season_blocks/inputs/' + s + '.json' for s in SEASONS}
    write(P / 'plan.json', dict(
        seasons=SEASONS, team_files=team_files,
        team_sha256={s: digest(B / f) for s, f in team_files.items()},
        target='missing goal_line_clearances for outfield native FPL players only',
        proof='Full ranked player block sum exactly exhausts explicit whole-league team block sum; unlisted active outfield players then have zero season blocks, bounding goal-line clearances to zero in every match.',
        controls='All closed historical goal-line values in certified outfield zero-block player-seasons; all explicit positive archive line-clearance counters must remain outside predictions.',
        gates=dict(min_controls=1000, max_errors=0, max_positive_contradictions=0),
        no_omitted_zero_without_exact_conservation=True,
        source_trial_stop='Stop on incomplete ranking, missing team totals, positive residual or invalid/duplicate identity/counter.',
        scoring_allowed=False, features_allowed=False,
    ))
    write(P / 'selection_freeze.json', {name: digest(P / name) for name in ['plan.json', 'inputs/parent_CURRENT.json']})

def collect():
    plan = json.loads((P / 'plan.json').read_text())
    for name, sha in json.loads((P / 'selection_freeze.json').read_text()).items():
        assert digest(P / name) == sha
    sources = []
    for season, cid in plan['seasons'].items():
        url = f'https://footballapi.pulselive.com/football/stats/ranked/players/outfielder_block?comps=1&compSeasons={cid}&page=0&pageSize=1000&altIds=true'
        path = P / 'inputs' / (season + '.json')
        assert not path.exists(), 'Preserve raw inputs'
        request = urllib.request.Request(url, headers={'Origin': 'https://www.premierleague.com', 'User-Agent': 'FPL-research/1.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
        path.write_bytes(raw)
        sources.append(dict(season=season, url=url, file=str(path.relative_to(P)), sha256=digest(path)))
        write(P / 'sources.json', sources)
        body = json.loads(raw)
        team = json.loads((B / plan['team_files'][season]).read_text())
        assert digest(B / plan['team_files'][season]) == plan['team_sha256'][season]
        print(season, 'schema', list(body), flush=True)
        assert body['stats']['pageInfo']['numPages'] == 1
        psum = sum(x['value'] for x in body['stats']['content'])
        tsum = sum(x['value'] for x in team['stats']['content'])
        print(season, 'player sum', psum, 'team sum', tsum, flush=True)
        assert psum == tsum, 'No exact league conservation; stop route'

if __name__ == '__main__':
    import sys
    {'prepare': prepare, 'collect': collect}[sys.argv[1]]()
