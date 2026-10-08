"""Six bounded public source requests with retained bytes and no access bypass."""
from pathlib import Path
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request

P = Path(__file__).resolve().parent
SEASONS = {'2019-20': 274, '2020-21': 363, '2021-22': 418,
           '2022-23': 489, '2023-24': 578, '2024-25': 719}

def main():
    inp = P / 'inputs'
    inp.mkdir(exist_ok=True)
    parent = P.parent.parent / 'CURRENT.json'
    frozen_parent = inp / 'parent_CURRENT.json'
    if not frozen_parent.exists():
        frozen_parent.write_bytes(parent.read_bytes())
    plan = [dict(season=season, comp_season=cid,
                 url=f'https://footballapi.pulselive.com/football/stats/ranked/teams/outfielder_block?comps=1&compSeasons={cid}&page=0&pageSize=100&altIds=true',
                 file=f'inputs/{season}.json') for season, cid in SEASONS.items()]
    plan_path = P / 'plan.json'
    payload = (json.dumps(plan, indent=2) + '\n').encode()
    if plan_path.exists():
        assert plan_path.read_bytes() == payload
    plan_path.write_bytes(payload)
    rows = []
    pilot = '--pilot' in sys.argv
    for row in plan[:1] if pilot else plan:
        path = P / row['file']
        if not path.exists():
            req = urllib.request.Request(row['url'], headers={
                'Origin': 'https://www.premierleague.com', 'User-Agent': 'FPL-research/1.0'})
            try:
                data = urllib.request.urlopen(req, timeout=40).read()
            except urllib.error.HTTPError as exc:
                (inp / 'error.json').write_text(json.dumps(dict(season=row['season'], status=exc.code,
                    url=row['url'], action='Stop; no bypass or new request after access/rate denial.'), indent=2))
                raise
            json.loads(data)
            path.write_bytes(data)
            time.sleep(.51)
        raw = path.read_bytes()
        obj = json.loads(raw)
        rows.append({**row, 'sha256': hashlib.sha256(raw).hexdigest()})
        print(row['season'], 'bytes', len(raw), 'keys', list(obj), flush=True)
    (inp / ('pilot_sources.json' if pilot else 'sources.json')).write_text(json.dumps(rows, indent=2) + '\n')

if __name__ == '__main__':
    main()
