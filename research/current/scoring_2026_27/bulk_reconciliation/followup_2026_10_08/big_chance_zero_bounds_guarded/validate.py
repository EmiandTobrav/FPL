"""Every old control remains visible; source-level abstention is explicit."""
import json
import pandas as pd
from prepare import P,B,K,digest,save

def main():
    for n,h in json.loads((P/'prediction_freeze.json').read_text()).items():assert digest(P/n)==h,n
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());assert digest(B/parent['requirements'])==parent['requirements_sha256']
    req=pd.read_csv(B/parent['requirements'],low_memory=False);bounds=pd.read_csv(P/'all_counter_bounds.csv.gz')
    controls=bounds.merge(req[~req.is_open][K+['value']],on=K,validate='one_to_one',suffixes=('','_known'))
    old=pd.read_csv(P.parent/'big_chance_zero_bounds/results/closed_counter_controls.csv.gz')
    pd.testing.assert_frame_equal(controls[K].sort_values(K).reset_index(drop=True),old[K].sort_values(K).reset_index(drop=True))
    numeric=controls.emitted_value.notna();controls['numeric_agrees']=controls.emitted_value.eq(controls.value_known).where(numeric)
    errors=int((~controls.loc[numeric,'numeric_agrees'].astype(bool)).sum())
    source_guards=pd.read_csv(P/'source_guards.csv.gz');guarded=controls[controls.source_guarded];guards_positive=guarded.merge(source_guards,left_on=K[:3],right_on=['season','exception_fixture','exception_code'],validate='many_to_one')
    negative=int((guards_positive.emitted_value.isna() & guards_positive.value_known.eq(guards_positive.approved_big_chance_saves) & guards_positive.value_known.gt(0)).sum())
    violations=int(bounds.loc[bounds.source_guarded,'emitted_value'].notna().sum());fixtures=len(controls.loc[numeric,K[:2]].drop_duplicates())
    g=json.loads((P/'protocol.json').read_text())['gate'];qualified=int(numeric.sum())>=g['minimum_zero_bound_controls'] and fixtures>=g['minimum_fixtures'] and errors==g['maximum_bound_errors'] and violations==g['maximum_guard_violations'] and negative>=g['minimum_verified_negative_controls']
    pred=pd.read_csv(P/'predictions.csv.gz');assert not pred.source_guarded.any();out=P/'results';out.mkdir(exist_ok=True)
    save(controls,out/'closed_counter_controls.csv.gz');save(guards_positive,out/'guard_negative_controls.csv.gz');overlay=pred if qualified else pred.iloc[:0];save(overlay,out/'overlay.csv.gz')
    report=dict(qualified=qualified,all_original_controls=len(controls),numeric_zero_controls=int(numeric.sum()),fixtures=fixtures,errors=errors,guard_abstentions=len(guarded),guarded_source_rows=int(bounds.source_guarded.sum()),guarded_team_seasons=len(source_guards),guard_violations=violations,verified_negative_controls=negative,new_fields=len(overlay),qualified_fields=sorted(overlay.field.unique()),original_rule_remains_failed=True,limits='The entire source team-season is withheld for a pre-existing approved event exception. All old cases remain; abstentions are not claimed as numeric agreements. Shared upstream evidence, no new independent holdout or scoring qualification.')
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
