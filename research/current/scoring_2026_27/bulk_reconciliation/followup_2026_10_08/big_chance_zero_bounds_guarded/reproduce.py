"""Reproduce the factual counter batch offline in an isolated tree."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
from prepare import P,R,digest

def main():
    generated=['source_guards.csv.gz','guard_event_evidence.csv.gz','all_counter_bounds.csv.gz','predictions.csv.gz','prediction_freeze.json','application_freeze.json']
    generated += [str(p.relative_to(P)) for p in sorted((P/'results').iterdir())]
    expected={n:digest(P/n) for n in generated}
    with tempfile.TemporaryDirectory(prefix='fpl-guarded-big-chance-replay-') as temp:
        target=Path(temp)/'current';stage=target/P.relative_to(R)
        shutil.copytree(P,stage,ignore=shutil.ignore_patterns('results','__pycache__'))
        for n in generated:
            dest=stage/n
            if dest.exists():dest.unlink()
        dependencies=json.loads((P/'dependencies.json').read_text())
        original=P.parent/'big_chance_zero_bounds'
        for n,h in json.loads((original/'prediction_freeze.json').read_text()).items():dependencies[str((original/n).relative_to(R))]=h
        old_controls=original/'results/closed_counter_controls.csv.gz'
        dependencies[str(old_controls.relative_to(R))]=digest(old_controls)
        for n,h in dependencies.items():
            source=R/n;assert digest(source)==h,n
            dest=target/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
        for script in ['predict.py','validate.py','build.py']:
            subprocess.run([sys.executable,str(stage/script)],check=True,capture_output=True,text=True)
        assert {n:digest(stage/n) for n in generated}==expected
    (P/'replay_report.json').write_text(json.dumps(dict(byte_identical_files=len(expected),files=expected,network=False),indent=2)+'\n')
    print(f'{len(expected)} generated files reproduced byte-identically offline')
if __name__=='__main__':main()
