"""Verify saved result bytes, including compressed Git episode evidence.

This does not replace full replay against excluded historical input archives.
"""
import hashlib
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def verify():
    result = json.loads((HERE/'result.json').read_text()); packed = {}
    for filename, prefix in [('episode_evidence.tar.gz', 'episodes/'), ('training_evidence.tar.gz', 'training/')]:
        archive = HERE/filename
        if not archive.exists(): continue
        with tarfile.open(archive, 'r:gz') as tar:
            for member in tar:
                if not member.isfile() or not member.name.startswith(prefix) or '..' in Path(member.name).parts:
                    raise ValueError('Unexpected archived evidence')
                key = str(HERE.relative_to(ROOT)/member.name)
                if key in packed: raise ValueError('Duplicate archived evidence')
                packed[key] = hashlib.sha256(tar.extractfile(member).read()).hexdigest()
    for name, expected in result['evidence_hashes'].items():
        p = (ROOT/name).resolve()
        if not p.is_relative_to(ROOT): raise ValueError('Evidence outside project')
        actual = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else packed.get(name)
        if actual != expected: raise ValueError('Saved evidence missing/changed: '+name)
    if packed.keys()-result['evidence_hashes'].keys(): raise ValueError('Unbound archived member')
    return len(result['evidence_hashes'])


if __name__ == '__main__':
    print(f'Verified {verify()} saved result files; no full input replay.')
