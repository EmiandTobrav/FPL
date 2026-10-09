"""Restore shared source bytes and replay whole inventories in an isolated offline tree."""
import io,json,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path
from prepare import P,S,R,digest

def main():
    generated=['goal_inventory.csv.gz','participants.csv.gz','identity_bridge.csv.gz','team_goal_coverage.csv.gz','prediction_freeze.json','application_freeze.json']+[str(f.relative_to(P)) for f in sorted((P/'results').iterdir())]
    expected={n:digest(P/n) for n in generated};deps=json.loads((P/'dependencies.json').read_text())
    with tempfile.TemporaryDirectory(prefix='fpl-goal-inventory-replay-') as temp:
        root=Path(temp)/'current';stage=root/P.relative_to(R)
        shutil.copytree(P,stage,ignore=shutil.ignore_patterns('results','__pycache__'))
        for name in generated:(stage/name).unlink(missing_ok=True)
        for name,h in deps.items():
            assert digest(R/name)==h
            f=root/name;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,f)
        old=root/(S/'espn_gap_acquisition').relative_to(R);identity=root/(S/'espn_primary_identity').relative_to(R)
        manifest=json.loads((old/'raw_manifest.json').read_text());assert digest(old/'raw_inputs.tar.gz')==manifest['archive_sha256']
        with tarfile.open(old/'raw_inputs.tar.gz','r:gz') as archive:
            assert {m.name for m in archive.getmembers()}==set(manifest['files'])
            for member in archive.getmembers():
                assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
                b=archive.extractfile(member).read();f=identity/member.name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);assert digest(f)==manifest['files'][member.name]
        for script in ['predict.py','build.py']:
            subprocess.run([sys.executable,str(stage/script)],check=True,capture_output=True,text=True)
        assert {n:digest(stage/n) for n in generated}==expected
    (P/'replay_report.json').write_text(json.dumps(dict(byte_identical_files=len(expected),files=expected,network=False),indent=2)+'\n');print(f'{len(expected)} goal-inventory outputs reproduced byte-identically offline')
if __name__=='__main__':main()
