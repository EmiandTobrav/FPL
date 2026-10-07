"""Reconcile threshold-sensitive minutes using corroborated match-clock evidence.

This does not infer that Opta's rounded minsPlayed and FPL completed minutes
are interchangeable, nor infer BPS rounding for durations inside minute 61.
"""
from pathlib import Path
import hashlib
import json
import pandas as pd

P=Path(__file__).resolve().parent
S=P.parent
KEY=['season','fixture','code']
HASHES={}


def read(path):
    HASHES[str(path.relative_to(S.parent))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path,low_memory=False)


def save(data,name):
    data.to_csv(P/name,index=False,compression={'method':'gzip','mtime':0} if name.endswith('.gz') else None)


def setup(qualifiers):
    q=json.loads(qualifiers)
    players=[x.strip() for x in q['30'].split(',')]
    positions=[int(x) for x in q['44'].split(',')]
    slots=[int(x) for x in q['131'].split(',')]
    if not len(players)==len(positions)==len(slots) or len(set(players))!=len(players):
        raise ValueError('lineup_length_or_identity')
    starters={p for p,pos,slot in zip(players,positions,slots) if pos in [1,2,3,4] and slot in range(1,12)}
    if len(starters)!=11 or sorted(slot for slot in slots if slot>0)!=list(range(1,12)):
        raise ValueError('lineup_starter_slots')
    if any((pos==5)!=(slot==0) for pos,slot in zip(positions,slots)):
        raise ValueError('lineup_position_slot_disagreement')
    return starters


def clock_components(seconds):
    """Only certify BPS when both plausible whole-minute/clock readings agree."""
    if seconds<=0 or seconds>5400:
        raise ValueError('invalid_regulation_duration')
    base=2 if seconds>=3600 else 1
    if seconds<3600:
        return base,3
    if seconds==3600:
        return base,3
    if seconds>=3660:
        return base,6
    return base,None


def adjudicate(target,events,fpl_minutes):
    result=dict(status='unresolved',reason='',event_id=None,elapsed_regulation_seconds=None,
                corroborated_completed_minutes=None,base_minute_points=None,bps_minute_points=None,
                scoring_requirement_discharged=False)
    def reject(reason):
        result['reason']=reason
        return result
    if pd.isna(target.match_id): return reject('missing_archive_match')
    if events.empty: return reject('missing_clock_events')
    if events.duplicated(['match_id','event_id']).any(): return reject('duplicate_event_identity')
    if events.type_id.isin([76,79]).any(): return reject('early_end_or_coverage_interruption')
    # Explicit period boundary events guard the 45-minute reset convention.
    for typ,period in [(32,1),(32,2),(30,1),(30,2)]:
        anchor=events[events.type_id.eq(typ)&events.period_id.eq(period)]
        if anchor.empty: return reject('missing_period_anchor')
    starts=events[events.type_id.eq(32)]
    if not (starts[starts.period_id.eq(1)].minute.eq(0).all() and
            starts[starts.period_id.eq(2)].minute.eq(45).all()):
        return reject('unsupported_clock_convention')
    lineup=events[events.type_id.eq(34)&events.team_id.eq(target.team_id)]
    if len(lineup)!=1: return reject('missing_or_ambiguous_lineup')
    try: starters=setup(lineup.iloc[0].qualifier_json)
    except (ValueError,KeyError,TypeError): return reject('invalid_lineup')
    player=events[events.player_id.eq(target.player_id)]
    if target.player_id not in starters: return reject('substitute_interval_requires_reconstruction')
    if player.type_id.isin([19,20,21]).any(): return reject('noncontinuous_participation')
    cards=player[player.type_id.eq(17)]
    if any(set(json.loads(x))&{'32','33'} for x in cards.qualifier_json):
        return reject('dismissal_requires_separate_clock_review')
    off=player[player.type_id.eq(18)]
    if len(off)!=1: return reject('missing_or_ambiguous_off_event')
    off=off.iloc[0]
    result['event_id']=int(off.event_id)
    if off.period_id!=2 or not 45<=off.minute<90 or not 0<=off.second<60:
        return reject('unsupported_off_clock')
    if off.team_id!=target.team_id: return reject('off_team_mismatch')
    # Multiple substitutions may share a timestamp; validate pair counts, not
    # a fabricated one-to-one replacement link across missing local event IDs.
    simultaneous=events[events.team_id.eq(off.team_id)&events.period_id.eq(off.period_id)&
                        events.minute.eq(off.minute)&events.second.eq(off.second)]
    if simultaneous.type_id.eq(18).sum()!=simultaneous.type_id.eq(19).sum():
        return reject('unbalanced_substitution_timestamp')
    seconds=int(off.minute*60+off.second)
    result['elapsed_regulation_seconds']=seconds
    if fpl_minutes!=seconds//60:
        return reject('clock_disagrees_with_completed_fpl_minutes')
    result['corroborated_completed_minutes']=seconds//60
    base,bps=clock_components(seconds)
    result.update(base_minute_points=base,bps_minute_points=bps)
    if bps is None:
        result.update(status='base_component_proven_bps_rule_open',reason='bps_rounding_at_60_plus_seconds_unqualified')
    else:
        result.update(status='minute_components_proven',reason='starter_paired_exit_clock_and_fpl_corroboration',scoring_requirement_discharged=True)
    return result


def main():
    HASHES.clear()
    targets=read(P/'inputs/targets.csv')
    events=read(P/'inputs/clock_events.csv.gz')
    ledger=read(S/'remaining_ledger/field_ledger.csv.gz')
    minutes=ledger[ledger.field.eq('minutes')].set_index(KEY)
    queue=read(S/'official_revision/resolution_queue.csv.gz')
    queue['previous_status']=queue.status
    grouped={k:g for k,g in events.groupby('match_id')}
    rows=[]
    for target in targets.itertuples(index=False):
        key=tuple(getattr(target,k) for k in KEY)
        source=minutes.loc[key]
        result=adjudicate(target,grouped.get(target.match_id,events.iloc[:0]),source.fpl)
        rows.append(dict(zip(KEY,key),name=target.name,date=target.date,home=target.home,away=target.away,
                         match_id=target.match_id,player_id=target.player_id,fpl_minutes=source.fpl,
                         archive_minutes=source.archive,fotmob_minutes=source.fotmob,**result))
    decisions=pd.DataFrame(rows)
    if len(decisions)!=710 or decisions.duplicated(KEY).any(): raise ValueError('target_population_changed')
    for row in decisions[decisions.scoring_requirement_discharged].itertuples():
        hit=queue.season.eq(row.season)&queue.fixture.eq(row.fixture)&queue.code.eq(row.code)&queue.field.eq('minutes')
        if hit.sum()!=1 or queue.loc[hit,'scoring_requirement_discharged'].any(): raise ValueError('invalid_queue_overlay')
        queue.loc[hit,['scoring_requirement_discharged','action','tier','scoring_scope']]=[True,'apply_clock_minute_components',0,'minute_components_proven_raw_convention_open']
        # Raw rounded-source discrepancies remain visible until source semantics
        # are normalized; this supplement discharges only the scoring component.
    for row in decisions[decisions.status.eq('base_component_proven_bps_rule_open')].itertuples():
        hit=queue.season.eq(row.season)&queue.fixture.eq(row.fixture)&queue.code.eq(row.code)&queue.field.eq('minutes')
        queue.loc[hit,['status','action','scoring_scope']]=['rule_unresolved','qualify_bps_minute_rounding','base_component_proven_bps_minute_rule_open']
    save(decisions,'decisions.csv')
    save(decisions[decisions.scoring_requirement_discharged],'minute_component_supplement.csv')
    save(decisions[~decisions.scoring_requirement_discharged],'remaining_sensitive_minutes.csv')
    save(queue,'resolution_queue.csv.gz')
    pending=queue[~queue.scoring_requirement_discharged]
    summary=[]
    for field in sorted(ledger.loc[ledger.required_for_scoring,'field'].unique()):
        g=queue[queue.field.eq(field)]; open_g=g[~g.scoring_requirement_discharged]
        summary.append(dict(field=field,remaining_scoring_cells=len(open_g),remaining_raw_or_rule_cells=int(g.raw_stat_still_unresolved.sum()),
            unique_affected_player_matches=len(open_g[KEY].drop_duplicates()),missing_data=int(open_g.status.eq('missing_data').sum()),
            source_conflict=int(open_g.status.eq('source_conflict').sum()),rule_unresolved=int(open_g.status.eq('rule_unresolved').sum())))
    save(pd.DataFrame(summary),'field_summary.csv')
    save(pending.groupby(KEY,sort=True).agg(name=('name','first'),date=('date','first'),home=('home','first'),away=('away','first'),
        remaining_scoring_fields=('field','size'),fields=('field',lambda x:'|'.join(sorted(x)))).reset_index(),'remaining_player_matches.csv.gz')
    save(pending.groupby(['season','fixture'],sort=True).agg(date=('date','first'),home=('home','first'),away=('away','first'),
        remaining_scoring_fields=('field','size'),unique_affected_player_matches=('code','nunique')).reset_index(),'match_summary.csv')
    findings=dict(target_player_matches=len(decisions),status_counts=decisions.status.value_counts().to_dict(),
        reason_counts=decisions.reason.value_counts().to_dict(),new_discharged_minute_requirements=int(decisions.scoring_requirement_discharged.sum()),
        remaining_sensitive_minute_requirements=int((~decisions.scoring_requirement_discharged).sum()),
        remaining_scoring_requirement_cells=len(pending),remaining_raw_stat_or_rule_cells=int(queue.raw_stat_still_unresolved.sum()),
        remaining_unique_player_matches=len(pending[KEY].drop_duplicates()),raw_minute_counters_overwritten=0,
        full_bps_or_bonus_labels_produced=0,keeper_values_modified=False,locked_labels_modified=False,cost_nok=0)
    for path in [P/'build.py',P/'prepare_inputs.py',P/'inputs/provenance.json',S/'rules_2026_27.json',S/'keeper_recovery/keeper_counts.csv.gz']:
        HASHES[str(path.relative_to(S.parent))]=hashlib.sha256(path.read_bytes()).hexdigest()
    (P/'manifest.json').write_text(json.dumps(dict(inputs=HASHES),indent=2,sort_keys=True)+'\n')
    (P/'findings.json').write_text(json.dumps(findings,indent=2)+'\n')
    print(json.dumps(findings,indent=2))


if __name__=='__main__': main()
