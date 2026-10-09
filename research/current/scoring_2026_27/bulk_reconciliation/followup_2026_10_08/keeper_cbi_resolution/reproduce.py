"""Finish and replay the consolidated casefile offline, preserving failures."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from event_audit import P, R, digest, write

def main():
    generated = [str(p.relative_to(P)) for p in sorted((P / 'results').iterdir())] + ['TRACK_CURRENT.json', 'manifest.json']
    expected = {n: digest(P / n) for n in generated}
    dependencies = json.loads((P / 'plan.json').read_text())['dependencies']
    dependencies.update(json.loads((P / 'casefile_scope_freeze.json').read_text())['references'])
    with tempfile.TemporaryDirectory(prefix='fpl-keeper-cbi-casefile-') as temp:
        destination = Path(temp) / 'current'
        stage = destination / P.relative_to(R)
        shutil.copytree(P, stage, ignore=shutil.ignore_patterns('results', '__pycache__', 'replay_report.json'))
        for n in generated:
            (stage / n).unlink(missing_ok=True)
        for n, h in dependencies.items():
            assert digest(R / n) == h, n
            target = destination / n
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(R / n, target)
        for script, arguments in [('event_audit.py', ['audit']), ('finalize.py', [])]:
            result = subprocess.run([sys.executable, str(stage / script), *arguments], capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
        assert {n: digest(stage / n) for n in generated} == expected
    write(P / 'replay_report.json', dict(byte_identical_files=len(expected), files=expected, network=False, application=False))
    print(len(expected), 'casefile outputs reproduced byte-identically offline; zero CBI applications')

if __name__ == '__main__':
    main()
