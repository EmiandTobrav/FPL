"""Minute-rule diagnostic and narrowly reviewed clock exceptions.

Candidate BPS fits use the existing labelled sparse-zero diagnostic only.
They are never treated as isolated component proofs or harmonized labels.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import pandas as pd

P=Path(__file__).resolve().parent
S=P.parent
KEY=['season','fixture','code']
HASHES={}


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


clock=module('clock_rules',S/'minute_reconciliation/build.py')
diag=module('bps_diagnostic',S/'validate_bps.py')


def read(path):
    HASHES[str(path.relative_to(S.parent))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path,low_memory=False)


def save(frame,name):
    frame.to_csv(P/name,index=False,compression={'method':'gzip','mtime':0} if name.endswith('.gz') else None)


def minute_candidate(fpl,primary,method):
    if pd.isna(fpl) or pd.isna(primary): raise ValueError('Missing minute evidence')
    if method=='fpl_strict': return 6 if fpl>60 else 3
    if method=='primary_strict': return 6 if primary>60 else 3
    if method=='fpl_inclusive': return 6 if fpl>=60 else 3
    raise ValueError(method)


# Inputs touched by the diagnostic, excluding official FPL scoring counters.
# A deliberately conservative isolation check; omissions are not certified zeros.
REQUIRED=['goals','att_pen_goal','total_clearance','outfielder_block','interception',
 'ball_recovery','accurate_cross_nocorner','big_chance_created','total_att_assist',
 'won_tackle','won_contest','winning_goal','clearance_off_line','was_fouled',
 'ontarget_scoring_att','total_pass','accurate_pass','penalty_conceded',
 'big_chance_missed','error_lead_to_goal','error_lead_to_shot','fouls','total_offside','shot_off_target']


def required_inputs(row):
    fields=REQUIRED.copy()
    if row.position=='GK': fields+=['saves','saved_ibox','big_chance_saves','penalty_save']
    # A split cannot affect goal BPS for GK/DEF under the target weights.
    if row.position in ['GK','DEF']: fields.remove('att_pen_goal')
    if pd.notna(row.get('pl_total_pass')) and row.pl_total_pass<30: fields.remove('accurate_pass')
    return fields


def remaining_component_isolated(row):
    return all(pd.notna(row.get('pl_'+x)) for x in required_inputs(row))


def check_starter(target,events):
    if events.empty or events.duplicated(['match_id','event_id']).any(): raise ValueError('Invalid match events')
    lineup=events[events.type_id.eq(34)&events.team_id.eq(target.team_id)]
    if len(lineup)!=1 or target.player_id not in clock.setup(lineup.iloc[0].qualifier_json):
        raise ValueError('Not a validated starter')
    for typ,period,expected in [(32,1,0),(32,2,45),(30,1,None),(30,2,None)]:
        e=events[events.type_id.eq(typ)&events.period_id.eq(period)]
        if e.empty or (expected is not None and not e.minute.eq(expected).all()):
            raise ValueError('Missing or incompatible period anchor')
    player=events[events.player_id.eq(target.player_id)]
    if player.type_id.isin([19,20,21]).any(): raise ValueError('Noncontinuous participation')
    return player


def review_exception(target,events,fpl_minutes,mode,fpl_red_cards):
    if mode not in ['second_yellow','one_second_pair','later_video_gap']: raise ValueError('Unknown review mode')
    player=check_starter(target,events)
    partner_id=None;delta=None
    if mode=='second_yellow':
        cards=player[player.type_id.eq(17)]
        reds=cards[cards.qualifier_json.map(lambda s:bool(set(json.loads(s))&{'32','33'}))]
        if len(reds)!=1 or '32' not in json.loads(reds.iloc[0].qualifier_json) or fpl_red_cards!=1:
            raise ValueError('Dismissal not corroborated by FPL and second-yellow event')
        end=reds.iloc[0]
        if not cards[(cards.minute*60+cards.second)<(end.minute*60+end.second)].qualifier_json.map(lambda s:'31' in json.loads(s)).any():
            raise ValueError('Missing first yellow')
        if player.type_id.eq(18).any(): raise ValueError('Ambiguous off and dismissal')
    else:
        off=player[player.type_id.eq(18)]
        if len(off)!=1 or fpl_red_cards!=0: raise ValueError('Expected one non-dismissal exit')
        end=off.iloc[0]
        seconds=end.minute*60+end.second
        same=events[events.team_id.eq(target.team_id)&events.period_id.eq(end.period_id)&events.type_id.isin([18,19])].copy()
        same['delta']=same.minute*60+same.second-seconds
        # A one-second interval is a reviewed tolerance, never a made-up precise
        # replacement link. Both recorded clocks must prove the same component.
        near=same[same.delta.abs().le(1 if mode=='one_second_pair' else 0)]
        if near.type_id.eq(18).sum()!=1 or near.type_id.eq(19).sum()!=1:
            raise ValueError('Ambiguous replacement interval')
        partner=near[near.type_id.eq(19)].iloc[0]
        partner_id=int(partner.event_id);delta=int(partner.delta)
        if mode=='one_second_pair' and abs(delta)!=1: raise ValueError('Not a one-second exception')
        if clock.clock_components(int(seconds))!=clock.clock_components(int(seconds+delta)):
            raise ValueError('Replacement interval crosses a rule boundary')
    seconds=int(end.minute*60+end.second)
    if end.team_id!=target.team_id or end.period_id!=2 or not 45<=end.minute<90 or not 0<=end.second<60:
        raise ValueError('Invalid reviewed exit clock')
    gaps=events[events.type_id.isin([76,79])]
    if mode=='later_video_gap':
        if gaps.empty or not gaps.type_id.eq(79).all() or not gaps.period_id.eq(2).all() or not (gaps.minute*60+gaps.second).gt(seconds).all():
            raise ValueError('Coverage gap not strictly after exit')
        if not gaps.qualifier_json.map(lambda s:'344' in json.loads(s)).all(): raise ValueError('Not video-only gap markers')
    elif not gaps.empty: raise ValueError('Unreviewed coverage gap')
    if fpl_minutes!=seconds//60: raise ValueError('FPL clock disagreement')
    base,bps=clock.clock_components(seconds)
    if bps is None: raise ValueError('BPS convention remains ambiguous')
    return dict(event_id=int(end.event_id),partner_event_id=partner_id,partner_seconds_delta=delta,
                elapsed_regulation_seconds=seconds,base_minute_points=base,bps_minute_points=bps)


def main():
    HASHES.clear()
    controls=read(S/'bps_recovery/inputs/primary_controls.csv.gz')
    controls=controls[controls.season.eq('2026-27')].copy()
    rows=[]
    for _,row in controls.iterrows():
        original=diag.calculate(row)
        candidates={m:original-minute_candidate(row.minutes,row.pl_mins_played,'fpl_strict')+
                      minute_candidate(row.minutes,row.pl_mins_played,m) for m in ['fpl_strict','primary_strict','fpl_inclusive']}
        missing=[x for x in required_inputs(row) if pd.isna(row.get('pl_'+x))]
        rows.append(dict(season=row.season,fixture=row.fixture,code=row.code,name=row['name'],position=row.position,
            fpl_minutes=row.minutes,primary_minutes=row.pl_mins_played,official_bps=row.bps,**candidates,
            nonminute_omissions=len(missing),missing_nonminute_fields='|'.join(missing),
            strict_component_isolated=remaining_component_isolated(row),scope='existing_development_sparse_zero_diagnostic_not_labels'))
    diagnostic=pd.DataFrame(rows)
    save(diagnostic,'current_diagnostic.csv')
    sensitive=diagnostic[diagnostic[['fpl_strict','primary_strict','fpl_inclusive']].nunique(axis=1)>1]
    save(sensitive,'current_discriminating_cases.csv')
    decisions=read(S/'minute_reconciliation/decisions.csv')
    targets=read(S/'minute_reconciliation/inputs/targets.csv').set_index(KEY)
    events=read(S/'minute_reconciliation/inputs/clock_events.csv.gz')
    ledger=read(S/'remaining_ledger/field_ledger.csv.gz')
    red=ledger[ledger.field.eq('red_cards')].set_index(KEY)
    queue=read(S/'minute_reconciliation/resolution_queue.csv.gz')
    cases=json.loads((P/'reviewed_cases.json').read_text())
    supplements=[]
    for case in cases:
        key=tuple(case[k] for k in KEY)
        target=targets.loc[key]
        d=decisions.set_index(KEY).loc[key]
        if d.status!='unresolved': raise ValueError('Already resolved or rule-gated case')
        evidence=review_exception(target,events[events.match_id.eq(target.match_id)],d.fpl_minutes,case['mode'],red.loc[key,'fpl'])
        supplements.append(dict(**{k:case[k] for k in KEY},name=d['name'],date=d.date,home=d.home,away=d.away,
            review_mode=case['mode'],previous_reason=d.reason,**evidence))
        hit=queue.season.eq(key[0])&queue.fixture.eq(key[1])&queue.code.eq(key[2])&queue.field.eq('minutes')
        if hit.sum()!=1 or queue.loc[hit,'scoring_requirement_discharged'].any():raise ValueError('Invalid queue overlay')
        queue.loc[hit,['scoring_requirement_discharged','action','tier','scoring_scope']]=[True,'apply_reviewed_clock_exception',0,'minute_components_proven_raw_convention_open']
    save(pd.DataFrame(supplements),'minute_component_supplement.csv')
    reviewed_keys={tuple(case[k] for k in KEY) for case in cases}
    sensitive_remaining=decisions[~decisions.scoring_requirement_discharged].copy()
    sensitive_remaining=sensitive_remaining[~sensitive_remaining.set_index(KEY).index.isin(reviewed_keys)]
    save(sensitive_remaining,'remaining_sensitive_minutes.csv')
    save(queue,'resolution_queue.csv.gz')
    pending=queue[~queue.scoring_requirement_discharged]
    summary=[]
    for field in sorted(ledger.loc[ledger.required_for_scoring,'field'].unique()):
        g=queue[queue.field.eq(field)];o=g[~g.scoring_requirement_discharged]
        summary.append(dict(field=field,remaining_scoring_cells=len(o),remaining_raw_or_rule_cells=int(g.raw_stat_still_unresolved.sum()),
            unique_affected_player_matches=len(o[KEY].drop_duplicates()),missing_data=int(o.status.eq('missing_data').sum()),
            source_conflict=int(o.status.eq('source_conflict').sum()),rule_unresolved=int(o.status.eq('rule_unresolved').sum())))
    save(pd.DataFrame(summary),'field_summary.csv')
    save(pending.groupby(KEY,sort=True).agg(name=('name','first'),date=('date','first'),home=('home','first'),away=('away','first'),
        remaining_scoring_fields=('field','size'),fields=('field',lambda x:'|'.join(sorted(x)))).reset_index(),'remaining_player_matches.csv.gz')
    save(pending.groupby(['season','fixture'],sort=True).agg(date=('date','first'),home=('home','first'),away=('away','first'),
        remaining_scoring_fields=('field','size'),unique_affected_player_matches=('code','nunique')).reset_index(),'match_summary.csv')
    findings=dict(current_controls=len(diagnostic),existing_development_not_holdout=True,
        candidate_exact_fits={m:int(diagnostic[m].eq(diagnostic.official_bps).sum()) for m in ['fpl_strict','primary_strict','fpl_inclusive']},
        discriminating_current_cases=len(sensitive),strictly_isolated_discriminating_cases=int(sensitive.strict_component_isolated.sum()),
        rule_qualified=False,rule_gated_cases_remaining=364,new_clock_exception_components=len(supplements),
        exceptional_clock_cases_remaining=26-len(supplements),remaining_sensitive_minute_requirements=390-len(supplements),
        remaining_scoring_requirement_cells=len(pending),remaining_raw_stat_or_rule_cells=int(queue.raw_stat_still_unresolved.sum()),
        remaining_unique_player_matches=len(pending[KEY].drop_duplicates()),full_bps_or_bonus_labels_produced=0,
        keeper_values_modified=False,locked_labels_modified=False,cost_nok=0)
    for path in [P/'build.py',P/'reviewed_cases.json',P/'evidence.json',S/'validate_bps.py',S/'minute_reconciliation/build.py',S/'rules_2026_27.json',S/'keeper_recovery/keeper_counts.csv.gz']:
        HASHES[str(path.relative_to(S.parent))]=hashlib.sha256(path.read_bytes()).hexdigest()
    (P/'manifest.json').write_text(json.dumps(dict(inputs=HASHES),indent=2,sort_keys=True)+'\n')
    (P/'findings.json').write_text(json.dumps(findings,indent=2)+'\n');print(json.dumps(findings,indent=2))


if __name__=='__main__':main()
