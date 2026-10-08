"""Collect the locked full-fixture PL reference; resume, rate limit, stop refusal."""
from pathlib import Path
import sys
import json
import time
import tarfile
import urllib.request
import urllib.error

import pandas as pd

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P.parent))
from predict import R, digest


def check_plan():
    lock = json.loads((P / 'plan_lock.json').read_text())
    for name, sha in lock['input_sha256'].items():
        if digest(R / name) != sha:
            raise ValueError('Reference input changed: ' + name)
    for name, key in [('fixture_plan.csv', 'plan_sha256'), ('protocol.json', 'protocol_sha256'),
                      ('raw_schema_audit.csv', 'audit_sha256'), ('plan.py', 'plan_code_sha256')]:
        if digest(P / name) != lock[key]:
            raise ValueError('Reference plan changed: ' + name)
    if digest(P.parent / 'freeze_v2.json') != lock['predictor_freeze_sha256']:
        raise ValueError('Predictor freeze changed')


def main():
    check_plan()
    cache = P / 'raw'
    cache.mkdir(exist_ok=True)
    old = R / 'scoring_2026_27/bulk_reconciliation/followup_2026_10_08/primary_gap_recovery'
    manifest = json.loads((old / 'raw_manifest.json').read_text())
    assert digest(old / 'raw_inputs.tar.gz') == manifest['archive_sha256']
    expected = {x['file']: x['sha256'] for x in manifest['entries']}
    with tarfile.open(old / 'raw_inputs.tar.gz') as archive:
        for row in pd.read_csv(P / 'fixture_plan.csv').itertuples():
            name = f'inputs/fixture_{row.pulse_id}.json'
            if name in expected and not (cache / Path(name).name).exists():
                raw = archive.extractfile(name).read()
                import hashlib
                assert hashlib.sha256(raw).hexdigest() == expected[name]
                (cache / Path(name).name).write_bytes(raw)
    records = []
    for index, row in enumerate(pd.read_csv(P / 'fixture_plan.csv').itertuples(), 1):
        path = cache / f'fixture_{row.pulse_id}.json'
        url = f'https://footballapi.pulselive.com/football/fixtures/{row.pulse_id}?altIds=true'
        if not path.exists():
            time.sleep(.55)
            try:
                raw = urllib.request.urlopen(urllib.request.Request(url,
                    headers={'Origin': 'https://www.premierleague.com', 'User-Agent': 'FPL-research/1.0'}), timeout=40).read()
            except urllib.error.HTTPError as error:
                if error.code in [401, 403, 429]:
                    print('Stopped after access/rate refusal', error.code, flush=True)
                raise
            data = json.loads(raw)
            if data.get('id') != row.pulse_id or data.get('status') != 'C':
                raise ValueError('Unexpected fixture response')
            path.write_bytes(raw)
        records.append(dict(season=row.season, fixture=row.fixture, pulse_id=row.pulse_id,
            file=str(path.relative_to(P)), url=url, sha256=digest(path), bytes=path.stat().st_size))
        (P / 'sources.json').write_text(json.dumps(records, indent=2) + '\n')
        if index % 20 == 0 or index == 142:
            print('Verified fixture responses', index, 'of 142', flush=True)


if __name__ == '__main__':
    main()
