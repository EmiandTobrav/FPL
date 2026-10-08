from pathlib import Path
import json,hashlib,zipfile,shutil
P=Path(__file__).resolve().parent;S=P.parent
files=set()
for folder in ['bulk_followup','match_inventory_recovery','assist_null_pass_recovery','assist_actor_bounds']:
 for p in (S/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.name not in ['package_manifest.json']:files.add(p)
for folder in ['match_inventory_recovery','assist_null_pass_recovery','assist_actor_bounds']:
 f=json.loads((S/folder/'freeze.json').read_text());inputs=f.get('inputs',f)
 for n in inputs:files.add(S/n)
extras=['assist_certificate_expansion/certificates.py','assist_certificate_expansion/predict.py','assist_certificate_expansion/protocol.json','assist_certificate_expansion/direct_control_plan.csv','assist_certificate_expansion/bound_control_plan.csv','assist_certificate_expansion/results/candidate_exclusions.csv.gz','assist_intentional_pass/inputs/official_cases.json','assist_intentional_pass/baseline/fpl_baseline.csv.gz','assist_intentional_pass/baseline/build.py','assist_intentional_pass/rules.py','assist_intentional_pass/results/team_coverage.csv','assist_candidate_bounds/validate.py','component_conservation/inputs/archive_projection.csv.gz','tackle_event_recovery_v2/results/requirements.csv.gz','tackle_event_recovery_v2/pairing.py','tackle_event_recovery_v2/predict.py','tackle_event_recovery_v2/protocol.json','tackle_event_recovery_v2/README.md','tackle_event_recovery_v2/validation_summary.json']
files.update(S/n for n in extras)
manifest={str(p.relative_to(S)):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted(files)};(P/'package_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');files.add(P/'package_manifest.json')
replay=S/'bulk_followup_replay';replay.mkdir(exist_ok=True)
for p in files:
 target=replay/p.relative_to(S);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
path=S/'fpl_bulk_followup_2026-10-08.zip'
with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(files):z.write(p,p.relative_to(S))
print('Files',len(files),'ZIP bytes',path.stat().st_size)
