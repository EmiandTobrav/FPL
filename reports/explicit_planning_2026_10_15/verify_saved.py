"""Verify exact saved evidence, directly or in round_evidence.tar.gz.

This is an integrity check. Full outcome/rule replay requires the local inputs
and `python -m model_lab.planning_experiment audit` before archiving raw logs.
"""
from pathlib import Path
import hashlib
import json
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def verify():
    report = json.loads((HERE/'result.json').read_text())
    archive_path = HERE/'round_evidence.tar.gz'
    archive = tarfile.open(archive_path,'r:gz') if archive_path.exists() else None
    try:
        members = {} if archive is None else {m.name:m for m in archive.getmembers() if m.isfile()}
        count = 0
        for name, expected in report['evidence_hashes'].items():
            path = (ROOT/name).resolve()
            if not path.is_relative_to(ROOT): raise ValueError('Evidence outside workspace')
            if path.is_file():
                stream = path.open('rb')
            elif archive is not None and name in members:
                stream = archive.extractfile(members[name])
            else: raise ValueError(f'Missing evidence: {name}')
            h=hashlib.sha256()
            with stream:
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
            if h.hexdigest() != expected: raise ValueError(f'Changed evidence: {name}')
            count += 1
        print(f'Verified {count} saved evidence files. Full simulation replay not performed.')
    finally:
        if archive is not None: archive.close()


if __name__ == '__main__': verify()
