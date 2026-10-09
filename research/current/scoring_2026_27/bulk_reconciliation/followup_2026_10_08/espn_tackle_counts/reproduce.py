"""Repeat the failed fixed mapping offline, without new collection or a ledger write."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
from prepare import P,R,digest

def main():
    generated=['inputs/player_bridge.csv','inputs/sources.json','player_gates.csv','predictions.csv.gz','prediction_freeze.json','results/control_comparisons.csv.gz','results/overlay.csv.gz','results/validation.json']
    expected={n:digest(P/n) for n in generated}
    deps=json.loads((P/'dependencies.json').read_text())
    with tempfile.TemporaryDirectory(prefix='fpl-tackle-replay-') as temp:
        root=Path(temp)/'current';stage=root/P.relative_to(R)
        shutil.copytree(P,stage,ignore=shutil.ignore_patterns('raw','results','__pycache__'))
        for name in generated:
            f=stage/name
            if f.exists():f.unlink()
        for name,h in deps.items():
            assert digest(R/name)==h
            f=root/name;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,f)
        subprocess.run([sys.executable,str(stage/'bootstrap.py')],check=True,capture_output=True,text=True)
        code="import runpy,urllib.request; urllib.request.urlopen=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('network forbidden during replay')); runpy.run_path("+repr(str(stage/'collect.py'))+",run_name='__main__')"
        subprocess.run([sys.executable,'-c',"import sys;sys.path.insert(0,"+repr(str(stage))+');'+code],check=True,capture_output=True,text=True)
        for script in ['predict.py','validate.py']:
            subprocess.run([sys.executable,str(stage/script)],check=True,capture_output=True,text=True)
        actual={n:digest(stage/n) for n in generated};assert actual==expected,(actual,expected)
    (P/'replay_report.json').write_text(json.dumps(dict(byte_identical_files=len(expected),files=expected,network=False,new_fields=0),indent=2)+'\n')
    print(f'{len(expected)} failed-study outputs reproduced byte-identically offline')
if __name__=='__main__':main()
