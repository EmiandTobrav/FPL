"""Cache complete official text streams and specify the remaining data request.

This diagnostic never approves a big-chance label from descriptive language.
"""
import csv
import hashlib
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'remaining_audit'


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / 'raw').mkdir(exist_ok=True)
    remaining = list(csv.DictReader((ROOT / 'unresolved_keepers.csv').open()))
    primary = {(r['season'], r['fixture'], r['code']): r
               for r in csv.DictReader((ROOT / 'followup/primary_manifest.csv').open())}
    jobs = {(r['season'], r['fixture']): r for r in remaining}
    sources, summary, request = [], [], []
    for key, row in sorted(jobs.items()):
        mid = primary[(*key, row['code'])]['pulse_id']
        url = f'https://footballapi.pulselive.com/football/fixtures/{mid}/textstream/EN?pageSize=1000&sort=desc'
        path = OUT / 'raw' / f'textstream_{mid}.json'
        if not path.exists():
            time.sleep(.75)
            data = urllib.request.urlopen(url, timeout=30).read()
            payload = json.loads(data)
            if int(payload['fixture']['id']) != int(mid):
                raise ValueError('wrong match identity')
            path.write_bytes(data)
        data = path.read_bytes()
        payload = json.loads(data)
        assert int(payload['fixture']['id']) == int(mid)
        info = payload['events']['pageInfo']
        comments = payload['events']['content']
        assert info['numPages'] == 1 and len(comments) == info['numEntries']
        sources.append(dict(season=key[0], fixture=int(key[1]), pulse_id=int(mid),
                            url=url, file=str(path.relative_to(OUT)),
                            sha256=hashlib.sha256(data).hexdigest()))
        summary.append(dict(season=key[0], fixture=key[1], pulse_id=mid,
            comments=len(comments), event_types=sorted(set(c['type'] for c in comments)),
            event_keys=sorted(set(k for c in comments for k in c)),
            big_chance_marker_keys=sorted(set(k for c in comments for k in c
                                              if 'chance' in k.lower() or 'qualif' in k.lower()))))
        (OUT / 'sources.json').write_text(json.dumps(sources, indent=2) + '\n')
        print(key, len(comments), 'comments', flush=True)
    for row in remaining:
        p = primary[(row['season'], row['fixture'], row['code'])]
        request.append({k: row[k] for k in ['season', 'fixture', 'fixture_code', 'date', 'home', 'away', 'code', 'name', 'side']} |
            dict(pulse_id=p['pulse_id'], pl_player_id=p['pl_player_id'],
                 required='explicit keeper big-chance-save count OR complete shot/save events with big-chance and outfield-block qualifiers',
                 missing_policy='blank until source evidence; no xG threshold or omitted-as-zero'))
    with (OUT / 'required_observations.csv').open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(request[0]))
        writer.writeheader()
        writer.writerows(request)
    (OUT / 'commentary_audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    assert len(request) == 38 and len(summary) == 22
    print('All pages complete; counts unchanged. Inspect keys before asserting label coverage.')


if __name__ == '__main__':
    main()
