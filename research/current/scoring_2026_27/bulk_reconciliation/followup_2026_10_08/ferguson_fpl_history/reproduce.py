"""Isolated offline replay of native-FPL correction and one requirement closure."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
from prepare import P,R,digest

def main():
    generated=['application_freeze.json']+[str(f.relative_to(P)) for f in sorted((P/'results').iterdir())]
    expected={n:digest(P/n) for n in generated};deps=json.loads((P/'dependencies.json').read_text())
    with tempfile.TemporaryDirectory(prefix='fpl-ferguson-replay-') as temp:
        root=Path(temp)/'current';stage=root/P.relative_to(R)
        shutil.copytree(P,stage,ignore=shutil.ignore_patterns('results','__pycache__'))
        (stage/'application_freeze.json').unlink(missing_ok=True)
        for name,h in deps.items():
            assert digest(R/name)==h
            f=root/name;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,f)
        for script in ['validate.py','build.py']:
            subprocess.run([sys.executable,str(stage/script)],check=True,capture_output=True,text=True)
        assert {n:digest(stage/n) for n in generated}==expected
    (P/'replay_report.json').write_text(json.dumps(dict(byte_identical_files=len(expected),files=expected,network=False),indent=2)+'\n')
    print(f'{len(expected)} source-reconciliation outputs reproduced byte-identically offline')
if __name__=='__main__':main()
