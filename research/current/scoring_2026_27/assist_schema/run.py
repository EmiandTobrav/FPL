from pathlib import Path
import sys,json,gzip
from dataclasses import asdict
import pandas as pd
from qualifiers import enrich
from rules import evaluate
P=Path(__file__).resolve().parent;S=P.parent

def main():
    cases=json.loads((S/'assist_rules/inputs/cases.json').read_text())
    events=pd.concat([pd.read_csv(S/'bps_recovery/inputs/official_assist_match_events.csv.gz'),pd.read_csv(S/'assist_rules/inputs/challenge_match_events.csv.gz')],ignore_index=True)
    baseline=pd.read_csv(S/'assist_rules/results.csv').set_index('case_id')
    rows=[];ev=[]
    for c in cases:
        f,d,seq=enrich(events,c);r=evaluate(f)
        rows.append(dict(case_id=c['case_id'],name=c['name'],season=c['season'],expected_award=c['expected_award'],baseline_raw_award=baseline.loc[c['case_id'],'raw_award'],schema_raw_award=r.awarded,reason=r.reason,missing=';'.join(r.missing),route=f['route'],received_inside_box=f['received_inside_box'],defensive_touch_is_pass=f['defensive_touch_is_pass'],new_evidence_fields=';'.join(sorted({x['field'] for x in d['schema_enrichment']}))))
        ev.append(dict(case_id=c['case_id'],facts=f,decision=asdict(r),diagnostics=d))
    out=pd.DataFrame(rows);out.to_csv(P/'results.csv',index=False)
    (P/'evidence.json').write_text(json.dumps(ev,indent=2,allow_nan=False)+'\n')
    findings=dict(controls=len(rows),baseline_raw_decisions=int(out.baseline_raw_award.notna().sum()),schema_raw_decisions=int(out.schema_raw_award.notna().sum()),schema_unresolved=int(out.schema_raw_award.isna().sum()),resolved_matching_official=int((out.schema_raw_award.notna()&out.schema_raw_award.eq(out.expected_award)).sum()),first_touch_receipt_fields=int(out.received_inside_box.notna().sum()),new_historical_assist_labels=0,independent_holdout=False,provider_certified_schema=False,locked_labels_modified=False,keeper_values_modified=False)
    (P/'findings.json').write_text(json.dumps(findings,indent=2)+'\n')
    print(out[['name','season','schema_raw_award','new_evidence_fields']].to_string(index=False));print(findings)
if __name__=='__main__':main()
