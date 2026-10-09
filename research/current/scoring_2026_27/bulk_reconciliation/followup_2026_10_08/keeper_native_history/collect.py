"""Bounded native FPL source-version check; never applies corrections."""
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path
import pandas as pd

P = Path(__file__).resolve().parent
R = P.parents[3]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def prepare():
    controls = P.parent / 'fotmob_keeper_cbi/results/control_comparisons.csv'
    roster = R / 'project/data/2025-26_players.csv.gz'
    c = pd.read_csv(controls)
    bad = c.loc[~c.agrees]
    assert len(bad) == 6 and bad.season.eq('2025-26').all()
    players = pd.read_csv(roster)
    selection = players.loc[players.code.isin(bad.code), ['code', 'id', 'first_name', 'second_name']]
    assert len(selection) == 5 and selection.code.is_unique
    plan = {
        'season': '2025-26', 'scope': 'five keepers in all six frozen native CBI vetoes',
        'hypothesis': 'Complete native player histories may document revisions relative to weekly FPL snapshots.',
        'stop_condition': 'No native CBI revision at the six vetoes means this route cannot qualify keeper CBI.',
        'source': 'vaastav/Fantasy-Premier-League mirror of native FPL',
        'native_source_authority': 'FPL; external majority agreement never replaces native values',
        'application_allowed': False, 'scoring_allowed': False,
        'controls_file': str(controls.relative_to(R)), 'controls_sha256': sha(controls),
        'roster_file': str(roster.relative_to(R)), 'roster_sha256': sha(roster),
        'vetoes': bad.to_dict('records'), 'players': selection.to_dict('records'),
        'prepared_at_utc': '2026-10-09 08:48:38 UTC',
    }
    dump(P / 'plan.json', plan)
    dump(P / 'plan_freeze.json', {'plan_sha256': sha(P / 'plan.json')})

def collect():
    plan = json.loads((P / 'plan.json').read_text())
    assert sha(P / 'plan.json') == json.loads((P / 'plan_freeze.json').read_text())['plan_sha256']
    sources = []
    def fetch(name, url):
        path = P / 'inputs' / name
        assert not path.exists(), 'Existing raw input must be preserved'
        req = urllib.request.Request(url, headers={'User-Agent': 'FPL-source-version-research'})
        with urllib.request.urlopen(req, timeout=40) as response:
            body = response.read()
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(body)
        sources.append({'file': str(path.relative_to(P)), 'url': url, 'sha256': sha(path)})
        dump(P / 'inputs/sources.json', sources)
        return body
    api = 'https://api.github.com/repos/vaastav/Fantasy-Premier-League'
    commit = json.loads(fetch('commit.json', api + '/commits?path=data/2025-26/players&per_page=1'))[0]['sha']
    dirs = json.loads(fetch('directories.json', api + '/contents/data/2025-26/players?ref=' + commit))
    root = 'https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/' + commit + '/data/2025-26/'
    fetch('players_raw.csv', root + 'players_raw.csv')
    for player in plan['players']:
        matches = [d for d in dirs if d['type'] == 'dir' and d['name'].endswith('_' + str(player['id']))]
        assert len(matches) == 1, (player, matches)
        fetch(str(player['code']) + '_history.csv', root + 'players/' + urllib.parse.quote(matches[0]['name']) + '/gw.csv')
    dump(P / 'inputs/source_freeze.json', {'commit': commit, 'sources_sha256': sha(P / 'inputs/sources.json')})
    print('Collected five complete native player histories at pinned commit', commit)

if __name__ == '__main__':
    import sys
    {'prepare': prepare, 'collect': collect}[sys.argv[1]]()
