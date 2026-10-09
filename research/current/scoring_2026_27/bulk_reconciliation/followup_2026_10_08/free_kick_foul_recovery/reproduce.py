"""Reproduce the frozen failed pilot from versioned dependencies, offline."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
from prepare import P,R,digest

def main():
    dependencies=json.loads((P/'inputs/manifest.json').read_text())['files']
    generated=['plan.csv.gz','predictions.csv.gz','prediction_freeze.json','inputs/manifest.json']
    generated += [str(f.relative_to(P)) for f in sorted((P/'results').iterdir())]
    expected={n:digest(P/n) for n in generated}
    with tempfile.TemporaryDirectory(prefix='fpl-fk-foul-replay-') as temp:
        target=Path(temp).resolve()/'current';stage=target/P.relative_to(R)
        shutil.copytree(P,stage,ignore=shutil.ignore_patterns('__pycache__','results'))
        for name,sha in dependencies.items():
            source=R/name;assert digest(source)==sha,name
            dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
        for name in generated:(stage/name).unlink(missing_ok=True)
        for script in ['prepare.py','validate.py','finalize.py']:
            result=subprocess.run([sys.executable,str(stage/script)],capture_output=True,text=True)
            assert result.returncode==0,result.stderr
        assert {n:digest(stage/n) for n in generated}==expected
    (P/'replay_report.json').write_text(json.dumps(dict(byte_identical_files=len(expected),files=expected,network=False),indent=2)+'\n')
    print(len(expected),'files reproduced byte-identically offline')
if __name__=='__main__':main()
