"""Verify result-bound saved evidence, including Git's compact round archive.

This checks stored bytes, not the excluded raw inputs or a fresh rules replay.
"""
import hashlib
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def verify():
    result = json.loads((HERE / 'result.json').read_text())
    packed = {}
    archive = HERE / 'round_evidence.tar.gz'
    if archive.exists():
        with tarfile.open(archive, 'r:gz') as tar:
            for member in tar:
                if not member.isfile() or not member.name.startswith('runs/') or '..' in Path(member.name).parts:
                    raise ValueError('Unexpected round archive member')
                key = str(HERE.relative_to(ROOT) / member.name)
                if key in packed: raise ValueError('Duplicate archive member')
                packed[key] = hashlib.sha256(tar.extractfile(member).read()).hexdigest()
    for name, expected in result['evidence_hashes'].items():
        p = (ROOT / name).resolve()
        if not p.is_relative_to(ROOT): raise ValueError('Evidence outside project')
        actual = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else packed.get(name)
        if actual != expected: raise ValueError('Missing or changed saved evidence: ' + name)
    if packed.keys() - result['evidence_hashes'].keys():
        raise ValueError('Unbound archived evidence')
    return len(result['evidence_hashes'])


if __name__ == '__main__':
    print(f'Verified {verify()} result-bound files; no fresh input/rules replay.')
