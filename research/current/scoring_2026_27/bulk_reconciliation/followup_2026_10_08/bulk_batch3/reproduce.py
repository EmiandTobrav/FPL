"""Reproduce this batch from committed inputs in an isolated copy, offline."""
from pathlib import Path
import json,shutil,tempfile,hashlib,subprocess,sys
P=Path(__file__).resolve().parent;S=P.parent
STAGES=['assist_pass_boundary','assist_attacking_touch_bounds','assist_failed_pass_bounds','assist_touch_bounds']
EXTRA=['bulk_batch2/results/requirements.csv.xz','assist_intentional_pass/baseline/build.py','assist_intentional_pass/rules.py','assist_intentional_pass/baseline/fpl_baseline.csv.gz','assist_intentional_pass/inputs/official_cases.json','assist_intentional_pass/results/team_coverage.csv','assist_possession_bounds/results/goal_decisions.csv.gz','assist_possession_bounds/results/candidate_exclusions.csv.gz','assist_possession_bounds/results/player_match_totals.csv.gz','assist_actor_bounds/results/applied_bounds.csv','assist_certificate_expansion/bound_control_plan.csv','assist_candidate_bounds/validate.py']
def main():
 files=set(EXTRA)
 for stage in STAGES:files.update(json.loads((S/stage/'freeze.json').read_text())['inputs'])
 files.update(json.loads((P/'joint_freeze.json').read_text())['inputs'])
 for stage in STAGES+['bulk_batch3']:
  files.update(str(p.relative_to(S)) for p in (S/stage).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['replay_verification.json','publication_manifest.json'])
 checks=[]
 for stage in STAGES:
  checks += [str(p.relative_to(S)) for p in (S/stage/'results').glob('*') if p.is_file()]
  checks += [stage+'/'+n for n in ['predictions.csv.gz','vector_controls.csv','single_goal_controls.csv','protected_conflicts.csv','positive_bound_conflicts.csv','validation_summary.json']]
 checks += [str(p.relative_to(S)) for p in (P/'results').glob('*') if p.is_file()]+['bulk_batch3/joint_predictions.csv.gz','bulk_batch3/joint_comparisons.csv','bulk_batch3/joint_validation_summary.json']
 expected={n:hashlib.sha256((S/n).read_bytes()).hexdigest() for n in checks}
 with tempfile.TemporaryDirectory(prefix='batch3_replay_',dir=S) as tmp:
  root=Path(tmp)
  for name in files:
   dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/name,dest)
  for name in checks:(root/name).unlink()
  commands=[stage+'/'+cmd+'.py' for stage in STAGES for cmd in ['predict','validate','build']]+['bulk_batch3/joint_predict.py','bulk_batch3/joint_validate.py','bulk_batch3/build.py']
  for cmd in commands:
   print('Offline replay:',cmd,flush=True);subprocess.run([sys.executable,str(root/cmd)],cwd=root,check=True)
  mismatches=[n for n,h in expected.items() if hashlib.sha256((root/n).read_bytes()).hexdigest()!=h];assert not mismatches,mismatches
 r=dict(offline=True,separate_copy=True,checked_outputs=len(expected),identical=True,python=sys.version.split()[0],output_sha256=expected);(P/'replay_verification.json').write_text(json.dumps(r,indent=2)+'\n');print('Identical outputs:',len(expected))
if __name__=='__main__':main()
