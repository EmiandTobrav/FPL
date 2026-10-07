"""Preserve official match totals for the remaining keeper investigation."""
import csv
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    unresolved = list(csv.DictReader((ROOT.parent / 'unresolved_keepers.csv').open()))
    keys = {(r['season'], r['fixture']) for r in unresolved}
    if (ROOT / 'sources.json').exists():
        keys.update((s['season'], str(s['fixture']))
                    for s in json.loads((ROOT / 'sources.json').read_text()))
    manifest = list(csv.DictReader((ROOT.parent / 'followup/primary_manifest.csv').open()))
    jobs = {(r['season'], r['fixture']): r for r in manifest if (r['season'], r['fixture']) in keys}
    sources = []
    for key, row in sorted(jobs.items()):
        mid = int(row['pulse_id'])
        url = f'https://footballapi.pulselive.com/football/stats/match/{mid}'
        path = ROOT / 'raw' / f'match_{mid}.json'
        if not path.exists():
            time.sleep(.75)
            raw = urllib.request.urlopen(url, timeout=30).read()
            payload = json.loads(raw)
            assert int(payload['entity']['id']) == mid
            path.write_bytes(raw)
        raw = path.read_bytes()
        payload = json.loads(raw)
        assert int(payload['entity']['id']) == mid
        sources.append(dict(season=key[0], fixture=int(key[1]), pulse_id=mid,
                            url=url, file=str(path.relative_to(ROOT)),
                            sha256=hashlib.sha256(raw).hexdigest()))
        (ROOT / 'sources.json').write_text(json.dumps(sources, indent=2) + '\n')
        print(key, 'saved', flush=True)


if __name__ == '__main__':
    main()
