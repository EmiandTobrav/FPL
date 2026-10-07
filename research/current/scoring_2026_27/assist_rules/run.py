"""Replay fixed controls; raw and officially annotated evidence stay separate."""
from pathlib import Path
from dataclasses import asdict
import json,gzip,hashlib
import pandas as pd
from extract import extract
from rules import evaluate
P=Path(__file__).resolve().parent

def main():
    cases=json.loads((P/'inputs/cases.json').read_text())
    official=json.loads((P/'inputs/official_facts.json').read_text())
    events=pd.concat([pd.read_csv(P.parent/'bps_recovery/inputs/official_assist_match_events.csv.gz'),pd.read_csv(P/'inputs/challenge_match_events.csv.gz')],ignore_index=True)
    assert not events.duplicated(['match_id','event_id']).any()
    results=[];evidence=[];sequences=[];provenance=[]
    for c in cases:
        raw,diagnostics,seq=extract(events,c)
        raw_result=evaluate(raw)
        annotated={**raw,**official[c['case_id']]['facts']}
        # A known raw fact must not silently be overwritten by a contradictory
        # annotation. Lower bounds can be tightened, never weakened.
        for k,v in official[c['case_id']]['facts'].items():
            if raw.get(k) is not None and raw[k]!=v:
                if k=='defensive_touches_min':assert v>=raw[k]
                else:raise ValueError(f'Conflicting facts: {c["case_id"]}/{k}: {raw[k]} vs {v}')
            provenance.append(dict(case_id=c['case_id'],field=k,value=json.dumps(v),source='raw_and_official' if raw.get(k)==v else 'official_scenario_description',source_url=official[c['case_id']]['source_url']))
        assisted=evaluate(annotated)
        assert assisted.awarded==c['expected_award'],(c['name'],assisted)
        results.append(dict(case_id=c['case_id'],cohort=c['cohort'],name=c['name'],season=c['season'],fixture=c['fixture'],code=c['code'],goal_event_id=c['goal_event_id'],expected_award=c['expected_award'],raw_award=raw_result.awarded,raw_reason=raw_result.reason,raw_missing=';'.join(raw_result.missing),annotated_award=assisted.awarded,annotated_reason=assisted.reason,source_url=c['source_url']))
        evidence.append(dict(case_id=c['case_id'],raw_facts=raw,raw_decision=asdict(raw_result),officially_annotated_facts=annotated,diagnostics=diagnostics))
        seq=seq.copy();seq['case_id']=c['case_id'];sequences.append(seq)
    out=pd.DataFrame(results)
    out.to_csv(P/'results.csv',index=False)
    pd.DataFrame(provenance).to_csv(P/'fact_provenance.csv',index=False)
    (P/'evidence.json').write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
    (P/'episode_events.csv.gz').write_bytes(gzip.compress(pd.concat(sequences,ignore_index=True).to_csv(index=False).encode(),mtime=0))
    summary=dict(controls=len(out),original_controls=int(out.cohort.eq('six_development_examples').sum()),additional_cases=4,additional_matches=3,annotated_rule_consistency_correct=int(out.annotated_award.eq(out.expected_award).sum()),raw_decisions=int(out.raw_award.notna().sum()),raw_unresolved=int(out.raw_award.isna().sum()),raw_decisions_matching_official=int((out.raw_award.notna()&out.raw_award.eq(out.expected_award)).sum()),raw_positive_decisions=int(out.raw_award.eq(True).sum()),new_historical_assist_labels=0,existing_official_additions_preserved=4,independent_holdout=False,automatic_full_history_rescoring_ready=False,locked_labels_modified=False,keeper_values_modified=False)
    (P/'findings.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(out[['name','season','expected_award','raw_award','raw_reason','annotated_award']].to_string(index=False));print(summary)
if __name__=='__main__':main()
