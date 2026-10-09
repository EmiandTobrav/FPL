"""Replay frozen projections, controls and application in a fresh offline tree."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
from prepare import P,B,R,digest

def main():
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text())
    generated=['players.csv.gz','goal_events.csv.gz','fixture_gates.csv','predictions.csv.gz','prediction_freeze.json','application_freeze.json']
    generated += [str(p.relative_to(P)) for p in sorted((P/'results').iterdir())]
    expected={n:digest(P/n) for n in generated}
    with tempfile.TemporaryDirectory(prefix='fpl-espn-replay-') as temp:
        target=Path(temp)/'current';stage=target/P.relative_to(R)
        shutil.copytree(P,stage,ignore=shutil.ignore_patterns('raw','results','__pycache__'))
        for n in generated:
            dest=stage/n
            if dest.exists():dest.unlink()
        files=[P.parent/'espn_gap_acquisition/raw_manifest.json',P.parent/'espn_gap_acquisition/raw_inputs.tar.gz',R/'scoring_2026_27/keeper_recovery/recover.py',R/'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz']
        files += [B/parent[n] for n in ['requirements','player_match_readiness','match_readiness']]
        selection=json.loads((P/'selection_freeze.json').read_text())
        dependencies=json.loads((P/'dependencies.json').read_text())
        for source in files:
            key=str(source.relative_to(R))
            assert digest(source)==dependencies[key]
            if key in selection['source_inputs']:assert digest(source)==selection['source_inputs'][key]
            dest=target/source.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
        for script in ['bootstrap.py','predict.py','validate.py','build.py']:
            subprocess.run([sys.executable,str(stage/script)],check=True,capture_output=True,text=True)
        actual={n:digest(stage/n) for n in generated};assert actual==expected
    report=dict(byte_identical_files=len(expected),files=expected,network=False,bootstrap_external_archives=False)
    (P/'replay_report.json').write_text(json.dumps(report,indent=2)+'\n');print(f'{len(expected)} generated files reproduced byte-identically offline')

if __name__=='__main__':main()
