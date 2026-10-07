"""Build an auditable full-season queue from the committed active source rows.

Example: python prepare_manifest.py --season 2024-25 --output queue.csv
Optional --fixtures restricts an explicitly labelled diagnostic collection.
Requires the parent's committed data partitions and project/data/*.csv.gz.
"""
from pathlib import Path
import argparse
import hashlib
import json
import urllib.request
import pandas as pd

P = Path(__file__).resolve().parent
SEASONS = {'2019-20':274, '2020-21':363, '2021-22':418, '2022-23':489,
           '2023-24':578, '2024-25':719, '2025-26':777}


def build(season, fixtures=None):
    root = P.parent.parent / 'project/data'
    fixture_path = root / f'{season}_fixtures.csv.gz'
    player_path = root / f'{season}_players.csv.gz'
    files = sorted((P.parent / 'data' / season).glob('part-*.csv'))
    if not files:
        raise ValueError('missing source partitions')
    source = pd.concat(pd.read_csv(path) for path in files)
    assert source.season.eq(season).all()
    assert not source.duplicated(['fixture','code']).any()
    if fixtures is not None:
        source = source[source.fixture.isin(fixtures)].copy()
    f, players = pd.read_csv(fixture_path), pd.read_csv(player_path)
    if f.id.duplicated().any() or players.code.duplicated().any():
        raise ValueError('ambiguous fixture/player crosswalk')
    cache = P / 'raw' / f'players_{season}.json'
    url = ('https://footballapi.pulselive.com/football/stats/ranked/players/appearances'
           f'?comps=1&compSeasons={SEASONS[season]}&page=0&pageSize=1000&altIds=true')
    if not cache.exists():
        cache.parent.mkdir(exist_ok=True)
        # No retry on access denials or rate limits.
        cache.write_bytes(urllib.request.urlopen(url, timeout=30).read())
    ranked = json.loads(cache.read_text())
    assert ranked['stats']['pageInfo']['numPages'] == 1
    ids = {}
    for item in ranked['stats']['content']:
        owner = item['owner']
        opta = owner.get('altIds', {}).get('opta')
        if opta:
            code, pid = int(opta.lstrip('p')), int(owner['id'])
            if code in ids and ids[code] != pid:
                raise ValueError('conflicting primary identity')
            ids[code] = pid
    rows = source[['season','fixture','code','name','goalkeeper']].copy()
    rows['pl_player_id'] = rows.code.map(ids)
    rows['pulse_id'] = rows.fixture.map(f.set_index('id').pulse_id)
    rows['element'] = rows.code.map(players.set_index('code').id)
    if rows[['pl_player_id','pulse_id','element']].isna().any().any() or rows.pulse_id.le(0).any():
        raise ValueError('unresolved identities: do not silently shrink the queue')
    for col in ['fixture','code','pl_player_id','pulse_id','element']:
        rows[col] = rows[col].astype(int)
    provenance = dict(season=season, rows=len(rows), matches=int(rows.fixture.nunique()),
                      fixture_filter=fixtures, primary_directory_url=url,
                      input_sha256={str(path.relative_to(P.parents[3])):hashlib.sha256(path.read_bytes()).hexdigest()
                                    for path in [*files, fixture_path, player_path, cache]})
    return rows, provenance


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--season', action='append', required=True, choices=list(SEASONS))
    parser.add_argument('--fixtures', nargs='+', type=int)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if len(set(args.season)) != len(args.season):
        parser.error('duplicate seasons')
    results = [build(season, args.fixtures) for season in args.season]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([r[0] for r in results]).to_csv(args.output, index=False)
    args.output.with_suffix('.provenance.json').write_text(json.dumps([r[1] for r in results], indent=2)+'\n')
    print(dict(rows=sum(len(r[0]) for r in results), manifest=str(args.output)))
