"""Read control outcomes only after verifying the frozen physical predictions."""
import json
import pandas as pd
from prepare import P,B,R,K,digest,save

def main():
    out=P/'results';out.mkdir(exist_ok=True)
    freeze=json.loads((P/'prediction_freeze.json').read_text())
    for n,h in freeze['files'].items():assert digest(P/n)==h,n
    for s in freeze['sources']:assert digest(P/s['file'])==s['sha256']
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());assert digest(B/parent['requirements'])==parent['requirements_sha256']
    req=pd.read_csv(B/parent['requirements'],low_memory=False)
    pred=pd.read_csv(P/'predictions.csv.gz');players=pd.read_csv(P/'players.csv.gz')
    archive_path=R/'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz'
    selection=json.loads((P/'selection_freeze.json').read_text())
    assert digest(archive_path)==selection['source_inputs'][str(archive_path.relative_to(R))]
    archive=pd.read_csv(archive_path);archive=archive[archive.mapping_status.eq('matched')]
    assert not archive.duplicated(K[:3]).any()
    refs=req[~req.is_open & req.field.isin(['penalty_goals','fouls_won'])][K+['value']].copy()
    refs['reference']='closed_ledger'
    zero=players[players.native_goals.eq(0)][K[:3]].copy();zero['field']='penalty_goals';zero['value']=0;zero['reference']='native_FPL_goal_zero_subset'
    explicit=[]
    for field,column in [('penalty_goals','attPenGoal'),('fouls_won','wasFouled')]:
        x=archive.dropna(subset=[column])[K[:3]+[column]].rename(columns={column:'value'});x['field']=field;x['reference']='explicit_archive_'+column;explicit.append(x)
    refs=pd.concat([refs,zero,*explicit],ignore_index=True)
    checks=pred.merge(refs,on=K,validate='one_to_many',suffixes=('_pred','_known'))
    checks['correct']=checks.value_pred.eq(checks.value_known)
    save(checks,out/'control_comparisons.csv.gz')
    unique=checks.drop_duplicates(K)
    actual=unique[unique.scope.eq('control')].merge(players[K[:3]+['position']],on=K[:3],validate='many_to_one')
    summaries={};qualified=[]
    protocol=json.loads((P/'protocol.json').read_text())
    for field in ['penalty_goals','fouls_won']:
        a=actual[actual.field.eq(field)];allchecks=checks[checks.field.eq(field)]
        limits=protocol['validation'][field]
        report=dict(control_values=len(a),control_fixtures=len(a[K[:2]].drop_duplicates()),positive_control_values=int(a.value_known.gt(0).sum()),goalkeeper_controls=int(a.position.eq('GK').sum()),all_reference_comparisons=len(allchecks),unique_checked_values=len(allchecks[K].drop_duplicates()),errors=int((~allchecks.correct).sum()),control_values_by_season=a.groupby('season').size().to_dict(),reference_counts=allchecks.reference.value_counts().to_dict())
        report['qualified']=bool(report['control_values']>=limits['minimum_control_values'] and report['control_fixtures']>=limits['minimum_control_fixtures'] and report['positive_control_values']>=limits['minimum_positive_control_values'] and report['goalkeeper_controls']>=limits.get('minimum_goalkeeper_controls',0) and report['errors']==0)
        summaries[field]=report
        if report['qualified']:qualified.append(field)
    pending=req[req.is_open&req.status.eq('missing_data')&req.value.isna()]
    overlay=pred[pred.scope.eq('target')&pred.field.isin(qualified)].merge(pending[K],on=K,validate='one_to_one')
    save(overlay,out/'overlay.csv.gz')
    report=dict(fields=summaries,qualified_fields=qualified,new_fields=len(overlay),by_field=overlay.field.value_counts().to_dict(),limits='Previously observed closed values/native source compatibility, with ESPN and archive possibly sharing upstream event data. Not independent holdout or final source/scoring qualification. All collected commentary remains evidence only; no target assists inferred.')
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
