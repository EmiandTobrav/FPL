"""Reproduce the active extended canonical view from immutable producer files."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

P = Path(__file__).resolve().parent
R = P.parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest = json.loads((P/'results/manifest.json').read_text())
    inputs = {**manifest['input_sha256'],**manifest['code_sha256']}
    with tempfile.TemporaryDirectory(prefix='fpl_canonical_extension_') as tmp:
        root = Path(tmp)/'research/current'
        for name, expected in inputs.items():
            if sha(R/name) != expected:
                raise ValueError(f'Frozen canonical input changed: {name}')
            target = root/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(R/name,target)
        stage = root/'training_dataset/canonical_extension'
        run = subprocess.run([sys.executable,str(stage/'build.py')],capture_output=True,text=True)
        if run.returncode:
            raise RuntimeError(run.stdout+run.stderr)
        for name, expected in manifest['output_sha256'].items():
            if sha(stage/'results'/name) != expected:
                raise ValueError(f'Reproduced canonical bytes differ: {name}')
        assert sha(stage/'results/manifest.json') == sha(P/'results/manifest.json')
    report = dict(offline=True,isolated_copy=True,identical=True,checked_outputs=len(manifest['output_sha256'])+1)
    (P/'reproduction_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report)

if __name__ == '__main__':
    main()
