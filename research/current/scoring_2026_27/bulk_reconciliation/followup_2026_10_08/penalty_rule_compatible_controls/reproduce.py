"""Replay the complete batch in an isolated offline temporary tree."""
from pathlib import Path
import json,shutil,subprocess,sys,tempfile
from prepare import P,S,B,R,digest

def main():
    inputs=json.loads((P/'inputs/manifest.json').read_text())
    expected=json.loads((P/'results/manifest.json').read_text())
    publication=json.loads((P/'publication_manifest.json').read_text())
    for name,sha in publication.items():assert digest(P/name)==sha,name
    with tempfile.TemporaryDirectory(prefix='fpl-penalty-compatible-replay-') as temporary:
        root=(Path(temporary)/'research/current').resolve()
        files={R/name for name in inputs['files']}
        files.update(x for x in P.rglob('*') if x.is_file() and '__pycache__' not in x.parts and 'results' not in x.parts)
        files.add(P/'results/validation.json')
        for source in files:
            target=root/source.relative_to(R);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        stage=root/P.relative_to(R)
        for script in ['prepare.py','validate.py','build.py']:
            subprocess.run([sys.executable,str(stage/script)],check=True,stdout=subprocess.DEVNULL)
        actual=json.loads((stage/'results/manifest.json').read_text());assert actual==expected
        for name,sha in expected.items():assert digest(stage/'results'/name)==sha,name
        for name in ['prediction_freeze.json','application_freeze.json','plan.csv.gz','predictions.csv.gz']:
            assert digest(stage/name)==digest(P/name),name
    report={'offline':True,'isolated':True,'byte_identical_results':len(expected),'frozen_prediction_and_application_identical':True,'output_sha256':expected}
    (P/'reproduction_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print({key:value for key,value in report.items() if key!='output_sha256'})
if __name__=='__main__':main()
