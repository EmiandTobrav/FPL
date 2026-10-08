"""Replay the failed keeper pilot offline without promoting its ledger."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile
P=Path(__file__).resolve().parent
S=P.parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    lock=json.loads((P/'input_lock.json').read_text())
    expected={p.name:sha(p) for p in (P/'results').iterdir() if p.is_file()}
    with tempfile.TemporaryDirectory(prefix='fpl_keeper_cbi_replay_') as tmp:
        current=Path(tmp)/'research/current'; target_s=current/'scoring_2026_27'
        for name,digest in lock['input_sha256'].items():
            source=(S.parent if name in lock['outside_root_inputs'] else S)/name
            target=(current if name in lock['outside_root_inputs'] else target_s)/name
            if sha(source)!=digest: raise ValueError('Frozen input changed')
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        target_p=target_s/P.relative_to(S)
        for name in ['input_lock.json','build.py']:
            target_p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(P/name,target_p/name)
        result=subprocess.run([sys.executable,str(target_p/'build.py')],capture_output=True,text=True)
        if result.returncode: raise RuntimeError(result.stdout+result.stderr)
        if any(sha(target_p/'results'/name)!=digest for name,digest in expected.items()):
            raise ValueError('Keeper pilot replay differs')
    report=dict(offline=True,isolated_copy=True,identical=True,checked_outputs=len(expected),
        output_sha256=expected,failed_native_gate_preserved=True)
    (P/'reproduction_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report|{'output_sha256':'recorded'})
if __name__=='__main__':main()
