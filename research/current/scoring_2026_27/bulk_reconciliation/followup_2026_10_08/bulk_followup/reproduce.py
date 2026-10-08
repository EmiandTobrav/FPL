from pathlib import Path
import subprocess,sys,json,gzip,hashlib
P=Path(__file__).resolve().parent;S=P.parent
paths=list((P/'results').glob('*'))+list((S/'assist_null_pass_recovery/results').glob('*'))+list((S/'assist_actor_bounds/results').glob('*'))+[S/'match_inventory_recovery'/n for n in ['match_conservation.csv','predictions.csv.gz','validation_summary.json','overlay.csv.gz']]
def digest(p):return hashlib.sha256(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()).hexdigest()
expected={str(p.relative_to(S)):digest(p) for p in paths if p.is_file()};logs=[]
scripts=['match_inventory_recovery/predict.py','match_inventory_recovery/validate.py','assist_null_pass_recovery/prepare.py','assist_null_pass_recovery/validate.py','assist_null_pass_recovery/build.py','assist_actor_bounds/predict.py','assist_actor_bounds/validate.py','assist_actor_bounds/build.py','bulk_followup/build.py','bulk_followup/diagnose.py']
for script in scripts:
 r=subprocess.run([sys.executable,str(S/script)],text=True,capture_output=True,cwd=S);logs.append(dict(script=script,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,logs[-1];print('Replayed',script,flush=True)
for folder in ['match_inventory_recovery','assist_actor_bounds']:
 r=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(S/folder),'-p','test_*.py','-v'],text=True,capture_output=True,cwd=S);logs.append(dict(tests=folder,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,logs[-1]
for name,h in expected.items():assert digest(S/name)==h,name
(P/'replay_verification.json').write_text(json.dumps(dict(equal_outputs=len(expected),logs=logs),indent=2)+'\n');print('Identical outputs',len(expected))
