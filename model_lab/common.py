"""Content-bound artifacts and explicit run ownership."""
from pathlib import Path
import hashlib
import json
import os
import platform
import importlib.metadata
import uuid

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    """Create immutable JSON without replacing any prior artifact."""
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.parent / ('.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('x') as f:
            json.dump(value, f, sort_keys=True, indent=2, allow_nan=False); f.write('\n')
            f.flush(); os.fsync(f.fileno())
        os.link(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def resolve(root, name):
    p = (Path(root) / name).resolve()
    if not p.is_relative_to(Path(root).resolve()) or not p.is_file():
        raise ValueError(f'Missing file or path outside root: {name}')
    return p


def verify_files(root, mapping):
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError('An explicit nonempty file hash map is required')
    for name, expected in mapping.items():
        if sha(resolve(root, name)) != expected:
            raise ValueError(f'Changed bound file: {name}')


def runtime():
    result = {'python': platform.python_version(), 'platform': platform.platform()}
    for name in ['numpy', 'pandas', 'scipy', 'scikit-learn', 'catboost', 'lightgbm']:
        try: result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: result[name] = None
    return result


def implementation():
    files = [p for p in (ROOT / 'model_lab').rglob('*.py') if 'tests' not in p.parts]
    files += list((ROOT / 'datasets/fpl_model_pipeline_v1').glob('*.py'))
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)}


def claim(directory, contract):
    """A started/failed run requires a new explicit attempt; never auto-retry."""
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    complete = directory / 'complete.json'
    if complete.exists():
        receipt = read(complete)
        if receipt['contract_hash'] != digest(contract): raise ValueError('Run contract differs')
        verify_files(directory, receipt['outputs'])
        return receipt
    atomic_json(directory / 'started.json', {'contract_hash': digest(contract), 'contract': contract})
    return None
