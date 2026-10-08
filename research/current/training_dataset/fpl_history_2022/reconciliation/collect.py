"""Acquire one fixed old weekly snapshot for exact chronology verification."""
import json
import urllib.request
import csv
import io

from plan import P, R, digest


def check_plan():
    lock = json.loads((P / 'plan_lock.json').read_text())
    if digest(P / 'plan.py') != lock['code_sha256']:
        raise ValueError('Reconciliation plan code changed')
    for name, sha in lock['input_sha256'].items():
        if digest(R / name) != sha:
            raise ValueError('Reconciliation frozen input changed: ' + name)


def main():
    check_plan()
    meta = json.loads((P / 'source_metadata.json').read_text())
    url = f"https://raw.githubusercontent.com/{meta['repository']}/{meta['gw16_commit']}/data/2022-23/gws/gw16.csv"
    path = P / 'gw16_2022_11_23.csv'
    if not path.exists():
        raw = urllib.request.urlopen(urllib.request.Request(url,
            headers={'User-Agent':'FPL-research/1.0'}), timeout=40).read()
        data = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        if not data or any(int(x['round']) != 16 for x in data):
            raise ValueError('Unexpected weekly snapshot scope')
        path.write_bytes(raw)
    result = dict(url=url, sha256=digest(path), bytes=path.stat().st_size,
        code_sha256=digest(P / 'collect.py'), plan_lock_sha256=digest(P / 'plan_lock.json'))
    (P / 'weekly_source.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result)


if __name__ == '__main__':
    main()
