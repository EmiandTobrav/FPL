"""Isolated offline replay from local source bytes, preserving cumulative predecessors."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
from prepare import P,R,digest

def main():
    generated=['goal_inventory.csv.gz','participants.csv.gz','identity_bridge.csv.gz','team_goal_coverage.csv.gz','prediction_freeze.json','application_freeze.json']
    generated += ['source_projection/'+n for n in ['players.csv.gz','goal_events.csv.gz','fixture_gates.csv','predictions.csv.gz','prediction_freeze.json']]
    generated += [str(f.relative_to(P)) for f in sorted((P/'results').iterdir())]
    expected={n:digest(P/n) for n in generated};deps=json.loads((P/'dependencies.json').read_text())
    with tempfile.TemporaryDirectory(prefix='fpl-last-inventory-') as temp:
        root=Path(temp)/'current';stage=root/P.relative_to(R)
        shutil.copytree(P,stage,ignore=shutil.ignore_patterns('results','__pycache__'))
        for n in generated:(stage/n).unlink(missing_ok=True)
        for name,h in deps.items():
            assert digest(R/name)==h
            if (R/name).is_relative_to(P):continue
            f=root/name;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,f)
        for script in ['source_projection/predict.py','predict.py','build.py']:
            subprocess.run([sys.executable,str(stage/script)],check=True,capture_output=True,text=True)
        assert {n:digest(stage/n) for n in generated}==expected
    (P/'replay_report.json').write_text(json.dumps(dict(byte_identical_files=len(expected),files=expected,network=False),indent=2)+'\n');print(f'{len(expected)} cumulative inventory outputs reproduced byte-identically offline')
if __name__=='__main__':main()
