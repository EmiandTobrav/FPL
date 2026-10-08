"""Offline, isolated replay from committed files; no collection or training."""
from pathlib import Path
import tempfile,shutil,json,subprocess,sys,hashlib
P=Path(__file__).resolve().parent;S=P.parent
STAGES=['primary_gap_recovery','assist_possession_bounds','penalty_foul_recovery','bulk_batch2']
EXTRA=['assist_intentional_pass/baseline/build.py','assist_intentional_pass/rules.py','assist_intentional_pass/baseline/fpl_baseline.csv.gz','assist_intentional_pass/inputs/official_cases.json','assist_intentional_pass/results/team_coverage.csv','assist_actor_bounds/results/goal_decisions.csv.gz','assist_actor_bounds/results/candidate_exclusions.csv.gz','assist_actor_bounds/results/player_match_totals.csv.gz','assist_actor_bounds/results/applied_bounds.csv','assist_certificate_expansion/bound_control_plan.csv','assist_candidate_bounds/validate.py','component_conservation/inputs/archive_projection.csv.gz']
def run():
 inputs=set(EXTRA)
 for stage in STAGES[:-1]:inputs.update(json.loads((S/stage/'freeze.json').read_text())['inputs'])
 files=set(inputs)
 for stage in STAGES:
  files.update(str(p.relative_to(S)) for p in (S/stage).rglob('*') if p.is_file() and 'inputs' not in p.relative_to(S/stage).parts and '__pycache__' not in p.parts and p.name not in ['replay_verification.json','publication_manifest.json'])
 checks=[x for x in files if x.startswith('bulk_batch2/results/') or x.startswith('assist_possession_bounds/results/') or x in ['primary_gap_recovery/predictions.csv.gz','primary_gap_recovery/conservation.csv','primary_gap_recovery/qualified_components.csv.gz','primary_gap_recovery/overlay.csv.gz','primary_gap_recovery/control_comparisons.csv','primary_gap_recovery/control_summary.csv','primary_gap_recovery/explicit_component_controls.csv','primary_gap_recovery/validation_summary.json','assist_possession_bounds/predictions.csv.gz','assist_possession_bounds/vector_controls.csv','assist_possession_bounds/single_goal_controls.csv','assist_possession_bounds/protected_conflicts.csv','assist_possession_bounds/positive_bound_conflicts.csv','assist_possession_bounds/validation_summary.json','penalty_foul_recovery/predictions.csv.gz','penalty_foul_recovery/validation_comparisons.csv','penalty_foul_recovery/protected_conflicts.csv','penalty_foul_recovery/validation_summary.json']]
 expected={x:hashlib.sha256((S/x).read_bytes()).hexdigest() for x in checks}
 with tempfile.TemporaryDirectory(prefix='batch2_replay_',dir=S) as tmp:
  root=Path(tmp)
  for name in files:
   dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/name,dest)
  for stage in STAGES:(root/stage/'results').mkdir(exist_ok=True)
  # Remove generated outputs to ensure commands really regenerate them.
  for name in checks:(root/name).unlink()
  commands=['primary_gap_recovery/bootstrap.py','primary_gap_recovery/verify_sources.py','primary_gap_recovery/predict.py','primary_gap_recovery/validate.py','assist_possession_bounds/predict.py','assist_possession_bounds/validate.py','assist_possession_bounds/build.py','penalty_foul_recovery/predict.py','penalty_foul_recovery/validate.py','bulk_batch2/build.py']
  for cmd in commands:
   print('Offline replay:',cmd,flush=True);subprocess.run([sys.executable,str(root/cmd)],cwd=root,check=True)
  mismatches=[x for x,h in expected.items() if hashlib.sha256((root/x).read_bytes()).hexdigest()!=h];assert not mismatches,mismatches
 result=dict(offline=True,separate_copy=True,checked_outputs=len(checks),identical=True,primary_player_responses=685,fixture_responses=24,python=sys.version.split()[0],output_sha256=expected);(P/'replay_verification.json').write_text(json.dumps(result,indent=2)+'\n');print('Identical replay outputs:',len(checks))
if __name__=='__main__':run()
