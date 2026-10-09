"""Apply qualified goal decisions and close only newly complete empty assist targets."""
from pathlib import Path
import ast,gzip,json,lzma
import pandas as pd
from prepare import P,S,B,R,K,digest,freeze_write
OUT=P/'results'
def save(frame,name):
    raw=frame.to_csv(index=False).encode()
    if name.endswith('.gz'):raw=gzip.compress(raw,mtime=0)
    elif name.endswith('.xz'):raw=lzma.compress(raw,preset=6)
    (OUT/name).write_bytes(raw)
def aggregate_functions():
    source=S/'assist_intentional_pass/baseline/build.py'
    tree=ast.parse(source.read_text())
    nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ['aggregate','contribution']]
    assert {node.name for node in nodes}=={'aggregate','contribution'}
    namespace={}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),namespace)
    return namespace['aggregate']
def main():
    for name,h in json.loads((P/'dependencies.json').read_text()).items():assert digest(R/name)==h,name
    frozen=json.loads((P/'prediction_freeze.json').read_text())
    for name,h in frozen['files'].items():assert digest(P/name)==h,name
    freeze_write(P/'application_freeze.json',(json.dumps({n:digest(P/n) for n in ['build.py','protocol.json','prediction_freeze.json','dependencies.json']},indent=2)+'\n').encode())
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());assert digest(B/parent['requirements'])==parent['requirements_sha256']
    OUT.mkdir(exist_ok=True)
    before=pd.read_csv(B/parent['requirements'],low_memory=False)
    old_goals=pd.read_csv(B/parent['assist_goal_decisions']);additions=pd.read_csv(P/'goal_inventory.csv.gz')
    assert additions.status.eq('unresolved').all() and additions.event_id.lt(0).all()
    goals=pd.concat([old_goals,additions],ignore_index=True);assert goals.event_id.is_unique
    pd.testing.assert_frame_equal(old_goals,goals.iloc[:len(old_goals)].reset_index(drop=True))
    people=pd.read_csv(P/'participants.csv.gz');coverage=pd.read_csv(P/'team_goal_coverage.csv.gz')
    cover=pd.read_csv(S/'assist_intentional_pass/results/team_coverage.csv').set_index(['match_id','team_id']).coverage_ok.to_dict()
    prior_coverage=pd.read_csv(B/parent['assist_team_coverage_supplement'])
    cover.update(prior_coverage.set_index(['match_id','team_id']).coverage_ok.to_dict())
    combined_coverage=pd.concat([prior_coverage,coverage],ignore_index=True);assert not combined_coverage.duplicated(['match_id','team_id']).any();save(combined_coverage,'team_coverage_supplement.csv.gz')
    prior_inventory=pd.read_csv(B/parent['assist_goal_inventory']);combined_inventory=pd.concat([prior_inventory,additions],ignore_index=True);assert combined_inventory.event_id.is_unique;save(combined_inventory,'source_goal_inventories.csv.gz')
    cover.update(coverage.set_index(['match_id','team_id']).coverage_ok.to_dict())
    save(goals,'goal_decisions.csv.gz')
    classification=pd.read_csv(B/parent['assist_goal_classification'])
    classes=additions[['match_id','event_id']].copy();classes['group']='new_goal_inventory_facts_pending'
    classification=pd.concat([classification,classes],ignore_index=True);assert not classification.duplicated(['match_id','event_id']).any()
    save(classification,'goal_group_classification.csv.gz')
    exclusions=pd.read_csv(S/'assist_touch_bounds/results/candidate_exclusions.csv.gz')
    denied={(int(row.event_id),row.player_id) for row in exclusions.itertuples()}
    denied.update((int(row['goal_event_id']),row['candidate_player_id']) for row in json.loads((S/'assist_intentional_pass/inputs/official_cases.json').read_text()) if not row['expected_award'])
    baseline=pd.read_csv(S/'assist_intentional_pass/baseline/fpl_baseline.csv.gz',usecols=K+['assists'])
    people=people.merge(baseline,on=K,validate='one_to_one')
    by_team={key:g.to_dict('records') for key,g in goals.groupby(['match_id','scoring_team_id'])}
    aggregate=aggregate_functions();rows=[]
    for row in people.to_dict('records'):
        key=(row['match_id'],row['team_id'])
        value=dict(value=row['assists'],reason='authoritative_fpl') if row['season']=='2025-26' else aggregate(by_team.get(key,[]),row['player_id'],row['own_team_goals'],cover.get(key,False),denied)
        rows.append({**{k:row[k] for k in K+['name','match_id','team_id','player_id']},'historical_fpl_assists':row['assists'],**value})
    totals=pd.DataFrame(rows);save(totals,'player_match_totals.csv.gz')
    prior_totals=pd.read_csv(B/parent['assist_totals'],low_memory=False)
    known=prior_totals[prior_totals.value.notna()][K+['value']].merge(totals[K+['value']],on=K,validate='one_to_one',suffixes=('_approved','_new'))
    assert known.value_approved.eq(known.value_new).all(), 'Previously known assist totals changed'
    pending=before[before.is_open&before.field.eq('assists_2026_27')&before.status.isin(['missing_data','rule_recalculation'])&before.value.isna()]
    overlay=pending[K+['field']].merge(totals,on=K,validate='one_to_one').dropna(subset=['value'])
    save(overlay,'overlay.csv.gz');req=before.copy();values=overlay.set_index(K)
    keys=pd.MultiIndex.from_frame(req[K]);mask=req.field.eq('assists_2026_27')&req.is_open&req.value.isna()&req.status.isin(['missing_data','rule_recalculation'])&keys.isin(values.index)
    assert int(mask.sum())==len(overlay)
    subkeys=pd.MultiIndex.from_frame(req.loc[mask,K])
    req.loc[mask,'value']=values.value.reindex(subkeys).to_numpy()
    req.loc[mask,'status']='documented_assist_reconstruction'
    req.loc[mask,'is_open']=False;req.loc[mask,'is_zero']=req.loc[mask,'value'].eq(0)
    req.loc[mask,'needs_external_quality_review']=True
    req.loc[mask,'quality_status']='qualified_goal_inventory_existing_scorer_exclusion_complete_player_goal_sum;collective_quality_pending'
    req.loc[mask,'provenance']='followup_2026_10_08/espn_last_inventory/results/overlay.csv.gz + goal_decisions.csv.gz'
    # Filled target totals and factual inventory improvements are separate counts.
    acquired=before[K].merge(pd.read_csv(P/'inputs/plan.csv.gz')[K[:2]],on=K[:2],how='left',indicator=True)._merge.eq('both')
    reclassified=~mask & acquired & before.is_open & before.field.eq('assists_2026_27') & before.status.eq('missing_data') & before.value.isna()
    req.loc[reclassified,'status']='rule_recalculation'
    req.loc[reclassified,'quality_status']='complete_ESPN_goal_inventory_causal_assist_facts_pending'
    req.loc[reclassified,'provenance']='followup_2026_10_08/espn_last_inventory/goal_inventory.csv.gz + team_goal_coverage.csv.gz'
    pd.testing.assert_frame_equal(req.loc[~(mask|reclassified)],before.loc[~(mask|reclassified)])
    source_columns=[col for col in before if col not in ['value','status','is_open','is_zero','needs_external_quality_review','quality_status','provenance']]
    pd.testing.assert_frame_equal(req[source_columns],before[source_columns])
    save(req,'requirements.csv.xz');pending=req[req.is_open];save(pending,'remaining_fields.csv.xz')
    fields=req.groupby('field').agg(required=('field','size'),open_cells=('is_open','sum'),external_quality_cells=('needs_external_quality_review','sum')).reset_index();save(fields,'field_summary.csv')
    pm=req.groupby(K).agg(open_fields=('is_open','sum'),quality_fields=('needs_external_quality_review','sum')).reset_index();pm['inputs_available']=pm.open_fields.eq(0);pm['scoring_qualified']=False;save(pm,'player_match_readiness.csv.xz')
    matches=pm.groupby(K[:2]).agg(player_matches=('code','size'),open_fields=('open_fields','sum'),quality_fields=('quality_fields','sum')).reset_index();matches['inputs_available']=matches.open_fields.eq(0);matches['bonus_ready']=False;save(matches,'match_readiness.csv')
    old_pm=pd.read_csv(B/parent['player_match_readiness']);old_matches=pd.read_csv(B/parent['match_readiness'])
    complete_pm=pm[pm.inputs_available].merge(old_pm[K+['inputs_available']],on=K,validate='one_to_one',suffixes=('','_old'))
    complete_matches=matches[matches.inputs_available].merge(old_matches[K[:2]+['inputs_available']],on=K[:2],validate='one_to_one',suffixes=('','_old'))
    summary=dict(old_open_fields=int(before.is_open.sum()),new_fields=len(overlay),open_fields=int(req.is_open.sum()),
        unique_affected_player_matches=len(pending[K].drop_duplicates()),complete_player_matches=int(pm.inputs_available.sum()),complete_matches=int(matches.inputs_available.sum()),
        new_complete_player_matches=int((~complete_pm.inputs_available_old).sum()),new_complete_matches=int((~complete_matches.inputs_available_old).sum()),
        new_goal_inventory_rows=len(additions),new_goal_decisions=0,acquired_fixture_inventories=len(coverage[K[:2]].drop_duplicates()),acquired_team_inventories=len(coverage),inventory_requirements_now_rule_pending=int(reclassified.sum()),
        new_fields_by_season=overlay.season.value_counts().sort_index().to_dict(),zero_values=int(overlay.value.eq(0).sum()),positive_values=int(overlay.value.gt(0).sum()),
        remaining_assists=int(pending.field.eq('assists_2026_27').sum()),previously_complete_assist_totals_preserved=len(known),
        unchanged_ledger_rows=len(before)-len(overlay)-int(reclassified.sum()),raw_fpl_preserved=True,old_scoring_labels_preserved=True,scoring_qualified=False,validation={'reused_published_source_controls':True,'new_assist_rule':False,'prior_goal_decisions_preserved':len(old_goals),'source_goal_vectors_complete':True})
    assert summary['old_open_fields']-summary['open_fields']==len(overlay)
    (OUT/'findings.json').write_text(json.dumps(summary,indent=2)+'\n')
    outputs=sorted(path for path in OUT.iterdir() if path.name!='manifest.json')
    (OUT/'manifest.json').write_text(json.dumps({path.name:digest(path) for path in outputs},indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
