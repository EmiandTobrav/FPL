"""Freeze target predictions using only approved counters and exact subset bounds."""
import json,math
import pandas as pd
from prepare import P,B,K,digest,save

def nonnegative(v):
    return pd.notna(v) and isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 and v==int(v)

def main():
    for name,h in json.loads((P/'selection_freeze.json').read_text()).items():assert digest(P/name)==h,name
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());assert digest(B/parent['requirements'])==parent['requirements_sha256']
    req=pd.read_csv(B/parent['requirements'],low_memory=False);pk=K[:3]
    assert not req.duplicated(K).any()
    pending=req[req.is_open&req.status.eq('missing_data')&req.value.isna()&req.field.isin(['won_tackles','legacy_net_tackles'])]
    approved=req[~req.is_open & req.field.isin(['total_tackles','won_tackles'])].pivot(index=pk,columns='field',values='value')
    rows=[];evidence=[]
    for r in pending.itertuples():
        key=(r.season,r.fixture,r.code)
        if key not in approved.index:continue
        total=approved.loc[key,'total_tackles'];won=approved.loc[key,'won_tackles']
        if not nonnegative(total):continue
        inferred=False
        if pd.isna(won) and total==0:won=0;inferred=True
        if not nonnegative(won) or won>total:continue
        if r.field=='won_tackles' and not inferred:continue
        value=int(won) if r.field=='won_tackles' else int(2*won-total)
        rows.append(dict(season=r.season,fixture=r.fixture,code=r.code,field=r.field,value=value,approved_total_tackles=int(total),won_tackles=int(won),won_from_zero_subset=inferred))
        e=req[(req.season==r.season)&(req.fixture==r.fixture)&(req.code==r.code)&req.field.eq('total_tackles')].iloc[0]
        evidence.append(dict(season=r.season,fixture=r.fixture,code=r.code,field=r.field,source_field='total_tackles',source_value=e.value,source_status=e.status,source_provenance=e.provenance))
    save(pd.DataFrame(rows),P/'predictions.csv.gz');save(pd.DataFrame(evidence),P/'input_evidence.csv.gz')
    record={n:digest(P/n) for n in ['predict.py','prepare.py','selection_freeze.json','protocol.json','dependencies.json','predictions.csv.gz','input_evidence.csv.gz']}
    f=P/'prediction_freeze.json'
    if f.exists():assert json.loads(f.read_text())==record
    f.write_text(json.dumps(record,indent=2)+'\n');print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':main()
