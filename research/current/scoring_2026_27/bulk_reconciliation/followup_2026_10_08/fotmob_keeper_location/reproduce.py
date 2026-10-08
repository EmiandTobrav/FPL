"""Replay the direct keeper-location batch offline in an isolated directory."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

P = Path(__file__).resolve().parent
S = P.parent.parent.parent.parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    lock = json.loads((P/'freeze.json').read_text())
    assert all(digest(P/name)==sha for name,sha in lock['file_sha256'].items())
    manifest = json.loads((P/'results/manifest.json').read_text())
    stage = P.relative_to(S)
    with tempfile.TemporaryDirectory(prefix='fpl_shot_replay_') as tmp:
        root = Path(tmp)/'research/current'
        for name,sha in manifest['input_sha256'].items():
            source = S/name
            assert digest(source)==sha
            target = root/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
        target_stage = root/stage
        shutil.copy2(P/'build.py',target_stage/'build.py')
        shutil.copytree(P/'inputs/raw',target_stage/'inputs/raw')
        run = subprocess.run([sys.executable,str(target_stage/'build.py')],capture_output=True,text=True)
        if run.returncode:
            raise RuntimeError(run.stdout+run.stderr)
        expected = manifest['outputs_sha256']
        assert all(digest(target_stage/'results'/name)==sha for name,sha in expected.items())
        assert digest(target_stage/'results/manifest.json')==digest(P/'results/manifest.json')
    report = dict(offline=True,isolated_copy=True,identical=True,checked_outputs=len(expected)+1)
    (P/'reproduction_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report)

if __name__=='__main__':
    main()
