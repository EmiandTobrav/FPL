import csv,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
sources=json.loads((P/'inputs/sources.json').read_text())
for s in sources:assert hashlib.sha256((P/s['file']).read_bytes()).hexdigest()==s['sha256']
plan=list(csv.DictReader((P/'keeper_veto_plan.csv').open()))[0]
f=json.loads((P/'keeper_findings.json').read_text())
for k in ['season','fixture','code']:assert str(f[k])==plan[k]
assert f['native_cbi']==int(plan['expected'])
d=json.loads((P/'inputs/keeper_veto_stats.json').read_text())
stats={s['name']:s['value'] for c in d['splits']['categories'] for s in c['stats']}
for k,v in f['components'].items():assert stats[k]==v
assert f['source_cbi']==sum(stats[k] for k in ['totalClearance','blockedShots','interceptions'])
assert f['source_cbi']!=f['native_cbi'] and not f['qualified'] and f['new_fields']==0
print('Six source hashes verified; native keeper veto confirmed; zero fills')
