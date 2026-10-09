"""Apply qualified factual counters, keeping all other authoritative cells."""
import gzip,json,lzma
import pandas as pd
from prepare import P,B,K,digest

OUT=P/'results'
PK=K[:3]

def save(frame,name):
    raw=frame.to_csv(index=False).encode()
    if name.endswith('.xz'):raw=lzma.compress(raw,preset=6)
    elif name.endswith('.gz'):raw=gzip.compress(raw,mtime=0)
    (OUT/name).write_bytes(raw)

def main():
    frozen=json.loads((P/'prediction_freeze.json').read_text())
    for n,h in frozen.items():assert digest(P/n)==h,n
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text())
    assert digest(B/parent['requirements'])==parent['requirements_sha256']
    before=pd.read_csv(B/parent['requirements'],low_memory=False)
    overlay=pd.read_csv(OUT/'overlay.csv.gz');validation=json.loads((OUT/'validation.json').read_text())
    assert set(overlay.field)<=set(validation['qualified_fields'])
    assert len(overlay)==validation['new_fields'] and not overlay.duplicated(K).any()
    application={n:digest(P/n) for n in ['validate.py','build.py','results/overlay.csv.gz','results/validation.json','results/closed_counter_controls.csv.gz','results/zero_total_net_controls.csv.gz']}
    freeze=P/'application_freeze.json'
    if freeze.exists():assert json.loads(freeze.read_text())==application
    freeze.write_text(json.dumps(application,indent=2)+'\n')
    req=before.copy();keys=pd.MultiIndex.from_frame(req[K]);values=overlay.set_index(K)
    mask=keys.isin(values.index)
    assert mask.sum()==len(overlay)
    assert before.loc[mask,'is_open'].all() and before.loc[mask,'status'].eq('missing_data').all() and before.loc[mask,'value'].isna().all()
    req.loc[mask,'value']=values.value.reindex(pd.MultiIndex.from_frame(req.loc[mask,K])).to_numpy()
    req.loc[mask,'status']='documented_source_reconciliation'
    req.loc[mask,'provenance']='followup_2026_10_08/tackle_subset_bounds/results/overlay.csv.gz + explicit_approved_zero_total_subset'
    req.loc[mask,'quality_status']='Opta_nonnegative_won_subset_approved_total_checked;collective_quality_pending'
    req.loc[mask,'needs_external_quality_review']=True
    req.loc[mask,'is_open']=False;req.loc[mask,'is_zero']=req.loc[mask,'value'].eq(0)
    pd.testing.assert_frame_equal(req.loc[~mask],before.loc[~mask])
    preserved=[c for c in before if c not in ['value','status','provenance','quality_status','needs_external_quality_review','is_open','is_zero']]
    pd.testing.assert_frame_equal(req[preserved],before[preserved])
    save(req,'requirements.csv.xz');pending=req[req.is_open];save(pending,'remaining_fields.csv.xz')
    fields=req.groupby('field').agg(required=('field','size'),open_cells=('is_open','sum'),external_quality_cells=('needs_external_quality_review','sum')).reset_index();save(fields,'field_summary.csv')
    pm=req.groupby(PK).agg(open_fields=('is_open','sum'),quality_fields=('needs_external_quality_review','sum')).reset_index();pm['inputs_available']=pm.open_fields.eq(0);pm['scoring_qualified']=False;save(pm,'player_match_readiness.csv.xz')
    matches=pm.groupby(PK[:2]).agg(player_matches=('code','size'),open_fields=('open_fields','sum'),quality_fields=('quality_fields','sum')).reset_index();matches['inputs_available']=matches.open_fields.eq(0);matches['bonus_ready']=False;save(matches,'match_readiness.csv')
    oldpm=pd.read_csv(B/parent['player_match_readiness']);oldmatches=pd.read_csv(B/parent['match_readiness'])
    newpm=pm[pm.inputs_available].merge(oldpm[PK+['inputs_available']],on=PK,validate='one_to_one',suffixes=('','_old'))
    newmatches=matches[matches.inputs_available].merge(oldmatches[PK[:2]+['inputs_available']],on=PK[:2],validate='one_to_one',suffixes=('','_old'))
    summary=dict(old_open_fields=int(before.is_open.sum()),new_fields=len(overlay),open_fields=int(req.is_open.sum()),unique_affected_player_matches=len(pending[PK].drop_duplicates()),complete_player_matches=int(pm.inputs_available.sum()),complete_matches=int(matches.inputs_available.sum()),new_complete_player_matches=int((~newpm.inputs_available_old).sum()),new_complete_matches=int((~newmatches.inputs_available_old).sum()),zero_values=int(overlay.value.eq(0).sum()),positive_values=int(overlay.value.gt(0).sum()),new_fields_by_season=overlay.groupby('season').size().to_dict(),unchanged_ledger_rows=len(before)-len(overlay),raw_fpl_preserved=True,scoring_qualified=False,validation=validation)
    assert summary['old_open_fields']-summary['open_fields']==summary['new_fields']
    (OUT/'findings.json').write_text(json.dumps(summary,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps({p.name:digest(p) for p in sorted(OUT.iterdir()) if p.name!='manifest.json'},indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
