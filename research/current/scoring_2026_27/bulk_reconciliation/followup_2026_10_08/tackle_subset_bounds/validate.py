"""Audit the exact subset on all available closed compatible counters."""
import json
import pandas as pd
from prepare import P,B,K,digest,save

def main():
    for n,h in json.loads((P/'prediction_freeze.json').read_text()).items():assert digest(P/n)==h,n
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());assert digest(B/parent['requirements'])==parent['requirements_sha256']
    req=pd.read_csv(B/parent['requirements'],low_memory=False);closed=req[~req.is_open & req.field.isin(['total_tackles','won_tackles','legacy_net_tackles'])]
    controls=closed.pivot(index=K[:3],columns='field',values='value').reset_index();pairs=controls.dropna(subset=['total_tackles','won_tackles']).copy()
    pairs['subset_ok']=pairs.won_tackles.ge(0)&pairs.total_tackles.ge(0)&pairs.won_tackles.le(pairs.total_tackles)&pairs.won_tackles.mod(1).eq(0)&pairs.total_tackles.mod(1).eq(0)
    zeros=pairs[pairs.total_tackles.eq(0)];netzeros=controls[controls.total_tackles.eq(0)&controls.legacy_net_tackles.notna()]
    protocol=json.loads((P/'protocol.json').read_text());g=protocol['gate']
    report=dict(known_counter_pairs=len(pairs),fixtures=len(pairs[K[:2]].drop_duplicates()),positive_won_controls=int(pairs.won_tackles.gt(0).sum()),zero_total_controls=len(zeros),known_zero_total_net_controls=len(netzeros),subset_errors=int((~pairs.subset_ok).sum()),zero_bound_errors=int(zeros.won_tackles.ne(0).sum()),known_zero_net_errors=int(netzeros.legacy_net_tackles.ne(0).sum()),limits='Mathematical Opta subset and previously approved counter regression; shared upstream evidence, not an independent holdout. Does not qualify historical BPS clipping.')
    report['qualified']=report['known_counter_pairs']>=g['minimum_pairs'] and report['fixtures']>=g['minimum_fixtures'] and report['positive_won_controls']>=g['minimum_positive_won_controls'] and report['zero_total_controls']>=g['minimum_zero_total_controls'] and report['subset_errors']==g['maximum_subset_errors'] and report['zero_bound_errors']==g['maximum_zero_bound_errors'] and report['known_zero_net_errors']==g['maximum_known_zero_net_errors']
    out=P/'results';out.mkdir(exist_ok=True);save(pairs,out/'closed_counter_controls.csv.gz');save(netzeros,out/'zero_total_net_controls.csv.gz')
    pred=pd.read_csv(P/'predictions.csv.gz');overlay=pred if report['qualified'] else pred.iloc[:0];save(overlay,out/'overlay.csv.gz');report.update(qualified_fields=sorted(overlay.field.unique()),new_fields=len(overlay),by_field=overlay.field.value_counts().to_dict())
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
