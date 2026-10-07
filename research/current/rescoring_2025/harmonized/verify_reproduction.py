"""Verify frozen plaintext partitions reconstruct identical counts and labels."""
import hashlib,json
from pathlib import Path
from package_data import restore
from build_labels import run,P,O,SEASONS
paths=[O/f'{s}_{kind}.csv' for s in SEASONS for kind in ['counts','labels']]
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
reports={p:p.read_bytes() for p in O.iterdir() if p.is_file() and p.suffix in ['.csv','.json'] and p not in paths}
restore()
restored={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
assert restored==before,'Partition restoration changed serialized observations/labels'
# Older-version comparisons require prior labels. This verification needs only
# frozen observations and official input snapshots; it does not regenerate comparisons.
run(compare_prior=False)
rebuilt={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
assert rebuilt==before,'Label reconstruction changed serialized results'
for p,b in reports.items():p.write_bytes(b)
report=dict(verified_files=len(paths),restored_byte_identical=True,rebuilt_byte_identical=True,sha256=before)
(O/'reproduction_check.json').write_text(json.dumps(report,indent=2)+'\n')
print('Restored and rebuilt byte-identical',len(paths),'season files')
