"""Preserve the bounded HTTP denial; never retry or apply values."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    for n, h in json.loads((P / 'plan_freeze.json').read_text()).items():
        assert digest(P / n) == h
    sources = json.loads((P / 'sources.json').read_text())
    plan = json.loads((P / 'plan.json').read_text())
    assert len(sources) == 1 and sources[0]['status'] == 403
    assert (sources[0]['season'], sources[0]['fixture']) == (plan['fixtures'][0]['season'], plan['fixtures'][0]['fixture'])
    for item in sources:
        assert digest(P / item['file']) == item['sha256']
    report = dict(requests=1, planned_requests=3, status=403, remaining_requests_not_attempted=2,
                  expected_values_collected=0, fields_closed=0, source_retry=False, ledger_modified=False)
    (P / 'findings.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
