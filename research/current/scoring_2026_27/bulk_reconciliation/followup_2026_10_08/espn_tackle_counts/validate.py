import json
import pandas as pd
from prepare import P,B,R,K,digest,save

def main():
    out=P/'results';out.mkdir(exist_ok=True)
    frozen=json.loads((P/'prediction_freeze.json').read_text())
    for n,h in frozen['files'].items():assert digest(P/n)==h,n
    for s in frozen['sources']:assert digest(P/s['file'])==s['sha256']
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());assert digest(B/parent['requirements'])==parent['requirements_sha256']
    req=pd.read_csv(B/parent['requirements'],low_memory=False);pred=pd.read_csv(P/'predictions.csv.gz')
    fields=['total_tackles','won_tackles','legacy_net_tackles']
    refs=req[~req.is_open & req.field.isin(fields)][K+['value']].copy();refs['reference']='closed_approved_ledger'
    archive=R/'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz'
    selection=json.loads((P/'selection_freeze.json').read_text());assert digest(archive)==selection['source_inputs'][str(archive.relative_to(R))]
    a=pd.read_csv(archive);a=a[a.mapping_status.eq('matched')];assert not a.duplicated(K[:3]).any()
    explicit=[]
    for field,col in [('total_tackles','totalTackle'),('won_tackles','wonTackle')]:
        x=a.dropna(subset=[col])[K[:3]+[col]].rename(columns={col:'value'});x['field']=field;x['reference']='explicit_archive_'+col;explicit.append(x)
    native=pd.read_csv(P/'inputs/native_players.csv.gz');x=native[native.season.eq('2025-26')].dropna(subset=['tackles'])[K[:3]+['tackles']].rename(columns={'tackles':'value'});x['field']='total_tackles';x['reference']='native_2025_FPL_tackles';explicit.append(x)
    refs=pd.concat([refs,*explicit],ignore_index=True);checks=pred.merge(refs,on=K,validate='one_to_many',suffixes=('_pred','_known'));checks['correct']=checks.value_pred.eq(checks.value_known);save(checks,out/'control_comparisons.csv.gz')
    summaries={};qualified=[]
    for field in fields:
        allchecks=checks[checks.field.eq(field)];control=allchecks[allchecks.scope.eq('control')].drop_duplicates(K)
        report=dict(control_values=len(control),control_fixtures=len(control[K[:2]].drop_duplicates()),nonzero_control_values=int(control.value_known.ne(0).sum()),errors=int((~allchecks.correct).sum()),all_comparisons=len(allchecks),control_values_by_season=control.groupby('season').size().to_dict(),reference_counts=allchecks.reference.value_counts().to_dict())
        report['qualified']=bool(report['control_values']>=100 and report['control_fixtures']>=20 and report['nonzero_control_values']>=20 and report['errors']==0);summaries[field]=report
        if report['qualified']:qualified.append(field)
    if not {'total_tackles','won_tackles'}<=set(qualified) and 'legacy_net_tackles' in qualified:qualified.remove('legacy_net_tackles');summaries['legacy_net_tackles']['qualified']=False;summaries['legacy_net_tackles']['dependency_gate']='explicit tackle mappings not both qualified'
    pending=req[req.is_open&req.status.eq('missing_data')&req.value.isna()]
    overlay=pred[pred.scope.eq('target')&pred.field.isin(qualified)].merge(pending[K],on=K,validate='one_to_one');save(overlay,out/'overlay.csv.gz')
    report=dict(fields=summaries,qualified_fields=qualified,new_fields=len(overlay),by_field=overlay.field.value_counts().to_dict(),limits='Source/closed-value regression with possible common upstream Opta lineage and previously observed references; no independent holdout, BPS clipping, scoring or final source-quality qualification.')
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
