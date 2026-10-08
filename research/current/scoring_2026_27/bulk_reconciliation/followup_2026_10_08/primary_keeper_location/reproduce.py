"""Rebuild the frozen primary location batch in an isolated offline checkout."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

P = Path(__file__).resolve().parent
R = P.parents[3]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest = json.loads((P/'results/manifest.json').read_text())
    stage = P.relative_to(R)
    with tempfile.TemporaryDirectory(prefix='fpl_primary_location_') as tmp:
        root = Path(tmp)/'research/current'
        for name, sha in manifest['input_sha256'].items():
            source = R/name
            assert digest(source) == sha
            target = root/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
        target_stage = root/stage
        run = subprocess.run([sys.executable,str(target_stage/'build.py')],capture_output=True,text=True)
        if run.returncode:
            raise RuntimeError(run.stdout+run.stderr)
        for name, sha in manifest['outputs_sha256'].items():
            assert digest(target_stage/'results'/name) == sha
        assert digest(target_stage/'results/manifest.json') == digest(P/'results/manifest.json')
    report = dict(offline=True,isolated_copy=True,identical=True,checked_outputs=len(manifest['outputs_sha256'])+1)
    (P/'reproduction_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report)

if __name__ == '__main__':
    main()
