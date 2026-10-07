"""FPL-authoritative baseline and season-specific delta-rescoring requirements.

External disagreements never invalidate an available compatible FPL value.
This builds an input/work ledger, not a new set of scoring labels.
"""
from pathlib import Path
import hashlib
import json
import pandas as pd

P=Path(__file__).resolve().parent
S=P.parent
R=S.parent
KEY=['season','fixture','code']
SOURCES=['fpl','fotmob','archive','primary','primary_followup','reconstruction','primary_acquisition']
FPL_FIELDS={'minutes':'minutes','goals':'goals_scored','assists':'assists','own_goals':'own_goals',
 'clean_sheets':'clean_sheets','goals_conceded':'goals_conceded','saves':'saves',
 'penalties_saved':'penalties_saved','penalties_missed':'penalties_missed',
 'yellow_cards':'yellow_cards','red_cards':'red_cards','clearances_blocks_interceptions':'clearances_blocks_interceptions',
 'recoveries':'recoveries','total_tackles':'tackles','defensive_contribution':'defensive_contribution',
 'historical_bps':'bps','historical_bonus':'bonus','historical_total_points':'total_points'}
OPEN={'missing_data','external_conflict','rule_recalculation','fpl_extract_exception'}
HASHES={}


def read(path):
    HASHES[str(path.relative_to(R))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path,low_memory=False)


def save(frame,name):
    frame.to_csv(P/name,index=False,compression={'method':'gzip','mtime':0} if name.endswith('.gz') else None)


def fpl_rows(meta):
    parts=[];logs=[]
    for season in sorted(meta.index.get_level_values('season').unique()):
        gw=read(R/f'project/data/{season}_gw.csv.gz').drop_duplicates()
        players=read(R/f'project/data/{season}_players.csv.gz')
        fixtures=read(R/f'project/data/{season}_fixtures.csv.gz').set_index('id')
        dup=gw.duplicated(['element','fixture'],keep=False);keep=~dup
        for (element,fixture),g in gw[dup].groupby(['element','fixture']):
            official=fixtures.loc[fixture]
            valid=g.GW.eq(official.event)&pd.to_datetime(g.kickoff_time,utc=True).eq(pd.to_datetime(official.kickoff_time,utc=True))
            if valid.sum()!=1:raise ValueError('Ambiguous FPL snapshot')
            keep.loc[g.index]=valid
            logs.append(dict(season=season,element=element,fixture=fixture,discarded=int((~valid).sum())))
        gw=gw[keep].merge(players[['id','code']],left_on='element',right_on='id',validate='many_to_one')
        gw['season']=season;parts.append(gw)
    all_rows=pd.concat(parts,ignore_index=True).set_index(KEY)
    if not all_rows.index.is_unique:raise ValueError('Duplicate FPL identity')
    if not all_rows[all_rows.minutes.gt(0)].index.isin(meta.index).all():raise ValueError('Active FPL population omitted')
    result=all_rows.reindex(meta.index)
    if result.minutes.isna().any():raise ValueError('Missing FPL baseline')
    save(pd.DataFrame(logs),'fpl_duplicate_resolution.csv')
    return result


def choose(evidence,approved=None):
    """Explicit FPL > approved evidence > concordant external evidence > abstain."""
    external=evidence.drop(columns=['fpl'])
    disagreement=evidence.nunique(axis=1,dropna=True).gt(1)
    value=external.bfill(axis=1).iloc[:,0]
    status=pd.Series('external_available',index=evidence.index)
    provenance=pd.Series('compatible_external_sources',index=evidence.index)
    status.loc[value.isna()]='missing_data'
    conflict=external.nunique(axis=1,dropna=True).gt(1)
    status.loc[conflict]='external_conflict';value.loc[conflict]=float('nan')
    if approved is not None:
        yes=approved.notna();value.loc[yes]=approved[yes];status.loc[yes]='approved_reconstruction';provenance.loc[yes]='approved_keeper_evidence'
    has=evidence.fpl.notna();value.loc[has]=evidence.loc[has,'fpl'];status.loc[has]='fpl_authoritative';provenance.loc[has]='historical_fpl'
    return value,status,provenance,disagreement


def required_fields(season,position,goals):
    """Changed BPS components + new basic-point inputs, unioned once per field."""
    fields={'clearances_blocks_interceptions','times_tackled','historical_bps'}
    if season<'2025-26':
        fields.update(['won_tackles','legacy_net_tackles','goal_line_clearances'])
        if position!='GK':fields.add('total_tackles')
        if position in ['MID','FWD']:fields.add('recoveries')
        if position in ['MID','FWD'] and (pd.isna(goals) or goals>0):fields.add('penalty_goals')
    else:
        if position!='GK':fields.add('defensive_contribution')
    if season<'2024-25':
        fields.update(['fouls_won','shots_on_target'])
        if position in ['GK','DEF']:fields.add('goals_conceded')
    if position=='GK':
        fields.update(['saves','saves_inside_box','big_chance_saves','penalties_saved'])
        if season=='2025-26':fields.add('saves_outside_box')
    fields.add('assists_2026_27')
    return fields


def main():
    HASHES.clear()
    meta=read(S/'remaining_ledger/player_matches.csv.gz').set_index(KEY)
    fpl=fpl_rows(meta)
    ledger=read(S/'remaining_ledger/field_ledger.csv.gz')
    original={name:g.set_index(KEY) for name,g in ledger.groupby('field',sort=False)}
    keeper=read(S/'keeper_recovery/keeper_counts.csv.gz').set_index(KEY).reindex(meta.index)
    corrections=read(S/'official_revision/counter_supplement.csv')
    primary=read(S/'bps_recovery/inputs/primary_controls.csv.gz').set_index(KEY).reindex(meta.index)
    follow=read(S/'keeper_recovery/followup/primary_verified/observations.csv').set_index(KEY).reindex(meta.index)
    more=read(S/'acquisition_followup/collection/observations.csv').set_index(KEY).reindex(meta.index)
    # Freeze a faithful FPL view. These baseline totals are NOT target labels.
    columns=[c for c in dict.fromkeys(FPL_FIELDS.values()) if c in fpl]
    save(fpl[columns].join(meta[['name','position','date','home','away']]).reset_index(),'fpl_baseline.csv.gz')
    groups={};disagreements=[]
    fields=list(dict.fromkeys(list(original)+list(FPL_FIELDS)+['times_tackled','legacy_net_tackles','saves_outside_box']))
    for field in fields:
        e=pd.DataFrame(float('nan'),index=meta.index,columns=SOURCES)
        if field in original:e=original[field].reindex(index=meta.index,columns=SOURCES).copy()
        if field in FPL_FIELDS:e['fpl']=fpl[FPL_FIELDS[field]]
        # Previously derived values based on source voting are not baseline authority.
        if field in ['penalty_goals','winning_goal']:e['reconstruction']=float('nan')
        if field in ['times_tackled','saves_outside_box']:
            alias='pl_times_tackled' if field=='times_tackled' else 'pl_saved_obox'
            for label,frame in [('primary',primary),('primary_followup',follow),('primary_acquisition',more)]:
                if alias in frame:e[label]=frame[alias]
        approved=keeper.big_chance_saves.where(keeper.status.eq('reconstructed')) if field=='big_chance_saves' else None
        value,status,provenance,disagree=choose(e,approved)
        g=e.copy();g['field']=field;g['value']=value;g['status']=status;g['provenance']=provenance
        g['source_disagreement']=disagree
        if field=='big_chance_saves':
            unresolved=keeper.status.eq('unresolved')
            g.loc[unresolved,['value','status','provenance']]=[float('nan'),'missing_data','existing_keeper_review_unresolved']
        for patch in corrections[corrections.field.eq(field)].itertuples():
            key=(patch.season,patch.fixture,patch.code)
            if g.loc[key,'fpl']!=patch.historical_fpl_value:raise ValueError('Revision baseline mismatch')
            g.loc[key,['value','status','provenance']]=[patch.revised_value,'official_revision',patch.source_url]
        groups[field]=g
        mismatched=g[g.fpl.notna()&disagree]
        if len(mismatched):disagreements.append(mismatched.reset_index())
    goals=groups['goals'].value
    zero_goals=goals.eq(0)
    for field in ['penalty_goals','winning_goal']:
        g=groups[field];external=g[SOURCES[1:]]
        bound=zero_goals & ~external.gt(0).any(axis=1)
        g.loc[bound,['value','status','provenance']]=[0,'documented_zero','authoritative_zero_goals_bound']
    assist=groups['assists_2026_27']
    current=meta.index.get_level_values('season')=='2025-26'
    assist.loc[current,['value','status','provenance']]=pd.DataFrame({'value':fpl.loc[current,'assists'],'status':'fpl_authoritative','provenance':'same_assist_rules_2025_26'},index=meta.index[current])
    old=~current
    zero=old&meta.own_team_goals.eq(0)
    assist.loc[zero,['value','status','provenance']]=[0,'documented_zero','official_team_score_zero']
    assist.loc[old&~zero,['value','status','provenance']]=[float('nan'),'rule_recalculation','historical_assists_retained_but_target_rules_require_event_review']
    # Rebuild from canonical evidence, never replay old conflict queues or minute patches.
    requirements=[]
    for key,row in meta.iterrows():
        for field in sorted(required_fields(key[0],row.position,goals.loc[key])):
            requirements.append((*key,field))
    req=pd.DataFrame(requirements,columns=KEY+['field'])
    evidence=pd.concat([g.reset_index() for g in groups.values()],ignore_index=True)
    req=req.merge(evidence,on=KEY+['field'],validate='one_to_one')
    req=req.merge(meta.reset_index()[KEY+['name','position','date','home','away','match_id','player_id']],on=KEY,validate='many_to_one')
    # Explicit known extraction anomaly does not authorize overwriting FPL with a provider integer.
    anomaly=req.season.eq('2024-25')&req.fixture.eq(239)&req.code.eq(487117)&req.field.eq('historical_bps')
    req.loc[anomaly,['status','provenance']]=['fpl_extract_exception','Ferguson_participation_proven_but_FPL_baseline_requires_repair_review']
    req['is_zero']=req.value.eq(0)&~req.status.isin(OPEN)
    req['needs_external_quality_review']=req.status.eq('external_available')
    req['is_open']=req.status.isin(OPEN)
    req=req.sort_values(KEY+['field']).reset_index(drop=True)
    save(req,'requirements.csv.gz')
    save(req[req.is_open],'remaining_fields.csv.gz')
    save(req[req.needs_external_quality_review],'external_quality_queue.csv.gz')
    save(pd.concat(disagreements,ignore_index=True),'fpl_external_differences_not_blockers.csv.gz')
    save(evidence[evidence.field.isin(FPL_FIELDS)],'authoritative_values.csv.gz')
    summary=[]
    for (season,field),g in req.groupby(['season','field'],sort=True):
        summary.append(dict(season=season,field=field,required=len(g),fpl_authoritative=int(g.status.eq('fpl_authoritative').sum()),
            documented_zero=int(g.is_zero.sum()),external_available=int(g.needs_external_quality_review.sum()),
            approved_reconstruction=int(g.status.eq('approved_reconstruction').sum()),missing_data=int(g.status.eq('missing_data').sum()),
            external_conflict=int(g.status.eq('external_conflict').sum()),rule_recalculation=int(g.status.eq('rule_recalculation').sum()),
            fpl_extract_exception=int(g.status.eq('fpl_extract_exception').sum()),open_cells=int(g.is_open.sum()),
            unique_affected_player_matches=len(g.loc[g.is_open,KEY].drop_duplicates())))
    summary=pd.DataFrame(summary);save(summary,'field_summary_by_season.csv')
    save(summary.drop(columns='season').groupby('field',sort=True).sum().reset_index(),'field_summary.csv')
    pending=req[req.is_open]
    players=pending.groupby(KEY,sort=True).agg(name=('name','first'),date=('date','first'),home=('home','first'),away=('away','first'),
        open_fields=('field','size'),fields=('field',lambda x:'|'.join(sorted(x)))).reset_index()
    save(players,'remaining_player_matches.csv.gz')
    save(pending.groupby(['season','fixture'],sort=True).agg(date=('date','first'),home=('home','first'),away=('away','first'),
        open_fields=('field','size'),unique_affected_player_matches=('code','nunique')).reset_index(),'match_summary.csv')
    save(players.groupby(['season','code'],sort=True).agg(name=('name','first'),unique_affected_player_matches=('fixture','size'),open_fields=('open_fields','sum')).reset_index(),'player_summary.csv')
    quality=req[req.needs_external_quality_review]
    # Preserve event-specific gates separately; they are not twelve new missing totals.
    deps=read(S/'official_revision/event_dependencies.csv')
    save(deps,'official_event_review.csv')
    old_queue=read(S/'bps_minute_qualification/resolution_queue.csv.gz')
    old_open=old_queue[~old_queue.scoring_requirement_discharged].copy()
    bridge=old_open[KEY+['field']].merge(req[KEY+['field','status','is_open']],on=KEY+['field'],how='outer',indicator=True,validate='one_to_one')
    bridge['transition']='closed_or_not_required_before'
    bridge.loc[bridge._merge.eq('left_only'),'transition']='removed_unchanged_component_or_outside_season_scope'
    bridge.loc[bridge._merge.eq('both')&bridge.is_open.eq(True),'transition']='still_open'
    bridge.loc[bridge._merge.eq('both')&bridge.is_open.eq(False),'transition']='no_longer_open_under_fpl_authority'
    bridge.loc[bridge._merge.eq('right_only')&bridge.is_open.eq(True),'transition']='newly_identified_delta_requirement'
    save(bridge.groupby(['field','transition'],sort=True).size().rename('cells').reset_index(),'reclassification_summary.csv')
    work=req[req.is_open|req.needs_external_quality_review]
    save(work.groupby(KEY,sort=True).agg(name=('name','first'),open_fields=('is_open','sum'),external_quality_fields=('needs_external_quality_review','sum')).reset_index(),'all_work_player_matches.csv.gz')
    findings=dict(population=len(meta),required_cells=len(req),status_counts=req.status.value_counts().to_dict(),
        open_cells=len(pending),unique_affected_player_matches=len(players),
        external_quality_review_cells=len(quality),external_quality_unique_player_matches=len(quality[KEY].drop_duplicates()),
        unique_open_or_external_quality_player_matches=len(req.loc[req.is_open|req.needs_external_quality_review,KEY].drop_duplicates()),
        required_minute_cells=int(req.field.eq('minutes').sum()),
        previous_364_minute_rule_cases_are_not_delta_requirements=True,
        fpl_provider_disagreements_are_not_fpl_errors=True,
        approved_keeper_values=int(keeper.status.eq('reconstructed').sum()),unresolved_keeper_values=int(keeper.status.eq('unresolved').sum()),
        official_goal_revision_cells=len(corrections),baseline_values_modified=False,full_target_labels_produced=0,
        delta_engine_qualified=False,full_historical_harmonization_complete=False,cost_nok=0)
    (P/'findings.json').write_text(json.dumps(findings,indent=2)+'\n')
    for path in [P/'build.py',P/'policy.json',P/'rule_dependencies.json',S/'rules_2026_27.json']:
        HASHES[str(path.relative_to(R))]=hashlib.sha256(path.read_bytes()).hexdigest()
    (P/'manifest.json').write_text(json.dumps(dict(inputs=HASHES),indent=2,sort_keys=True)+'\n')
    print(json.dumps(findings,indent=2))


if __name__=='__main__':main()
