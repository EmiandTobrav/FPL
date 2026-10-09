"""Offline replay of a completed zero-candidate source-compatibility track."""
import tempfile,json,shutil,subprocess,sys
from pathlib import Path
from predict import P,R,digest,write

def main():
 generated=['season_groups.csv','predictions.csv.gz','dependencies.json','prediction_freeze.json','complete_controls.csv','partial_groups.csv','validation.json','remaining_target_sources.csv','findings.json'];expected={n:digest(P/n) for n in generated}
 with tempfile.TemporaryDirectory(prefix='fpl-positive-gl-replay-') as temp:
  root=Path(temp).resolve()/'current';stage=root/P.relative_to(R);shutil.copytree(P,stage,ignore=shutil.ignore_patterns('__pycache__'))
  for n,h in json.loads((P/'dependencies.json').read_text()).items():
   source=R/n;assert digest(source)==h,n;dest=root/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
  for n in generated:(stage/n).unlink(missing_ok=True)
  for script in ['predict.py','validate.py','finalize.py']:
   result=subprocess.run([sys.executable,str(stage/script)],capture_output=True,text=True);assert result.returncode==0,result.stderr
  assert {n:digest(stage/n) for n in generated}==expected
 write(P/'replay_report.json',dict(byte_identical_files=len(expected),files=expected,network=False))
 print(len(expected),'files reproduced byte-identically offline')
if __name__=='__main__':main()
