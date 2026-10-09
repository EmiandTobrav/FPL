"""Validate frozen zero bounds before factual application."""
import json
import pandas as pd
from predict import P,B,K,digest,save

def main():
    for n,h in json.loads((P/'prediction_freeze.json').read_text()).items():assert digest(P/n)==h,n
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());assert digest(B/parent['requirements'])==parent['requirements_sha256']
    req=pd.read_csv(B/parent['requirements'],low_memory=False);bounds=pd.read_csv(P/'all_counter_bounds.csv.gz')
    controls=bounds.merge(req[~req.is_open][K+['value']],on=K,validate='one_to_one',suffixes=('','_known'))
    controls['agrees']=controls.value.eq(controls.value_known)
    g=json.loads((P/'plan.json').read_text())['gate'];errors=int((~controls.agrees).sum());fixtures=len(controls[K[:2]].drop_duplicates())
    qualified=len(controls)>=g['minimum_zero_bound_controls'] and fixtures>=g['minimum_fixtures'] and errors==g['maximum_bound_errors']
    out=P/'results';out.mkdir(exist_ok=True);save(controls,out/'closed_counter_controls.csv.gz')
    pred=pd.read_csv(P/'predictions.csv.gz');overlay=pred if qualified else pred.iloc[:0];save(overlay,out/'overlay.csv.gz')
    report=dict(qualified=qualified,zero_bound_controls=len(controls),fixtures=fixtures,errors=errors,new_fields=len(overlay),qualified_fields=sorted(overlay.field.unique()),limits='Exact official season/match conservation and compatible known-counter regression; shared upstream evidence, not independent holdout or full scoring qualification.')
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
