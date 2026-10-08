"""Bounded acquisition of pinned FPL histories; resume and stop on access refusal."""
from pathlib import Path
import json
import csv
import io
import urllib.request
import urllib.error
import urllib.parse
import time
import threading
import concurrent.futures

from plan import P, R, digest


def check_plan():
    lock = json.loads((P / 'plan_lock.json').read_text())
    for name, sha in lock['input_sha256'].items():
        if digest(R / name) != sha:
            raise ValueError('FPL history source input changed: ' + name)
    if digest(P / 'plan.py') != lock['plan_code_sha256']:
        raise ValueError('FPL history plan code changed')


def main():
    check_plan()
    plan = json.loads((P / 'source_plan.json').read_text())
    cache = P / 'raw'
    cache.mkdir(exist_ok=True)
    mutex, stopped = threading.Lock(), threading.Event()
    next_start = 0.0
    def fetch(row):
        nonlocal next_start
        path = cache / f"player_{row['element']}.csv"
        url = 'https://raw.githubusercontent.com/' + plan['repository'] + '/' + plan['commit'] + '/' + urllib.parse.quote(row['path'], safe='/')
        if not path.exists():
            with mutex:
                if stopped.is_set():
                    raise RuntimeError('Collection stopped')
                now = time.monotonic()
                delay = max(0, next_start-now)
                next_start = max(now, next_start) + .3
            if delay:
                time.sleep(delay)
            if stopped.is_set():
                raise RuntimeError('Collection stopped')
            try:
                raw = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'FPL-research/1.0'}), timeout=40).read()
            except urllib.error.HTTPError as error:
                if error.code in [401,403,429]:
                    stopped.set()
                if error.code == 404:
                    return dict(**row, url=url, status='not_archived', http_status=404)
                raise
            reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
            if 'fixture' not in reader.fieldnames or 'element' not in reader.fieldnames:
                raise ValueError('Unexpected player history schema')
            if any(int(x['element']) != row['element'] for x in reader):
                raise ValueError('Player history element mismatch')
            path.write_bytes(raw)
        return dict(**row, url=url, file=str(path.relative_to(P)), status='archived',
            sha256=digest(path), bytes=path.stat().st_size)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(fetch, plan['players']):
            results.append(result)
            (P / 'sources.json').write_text(json.dumps(results, indent=2) + '\n')
            if len(results) % 80 == 0 or len(results) == len(plan['players']):
                print('Archived sources', len(results), 'of', len(plan['players']), flush=True)


if __name__ == '__main__':
    main()
