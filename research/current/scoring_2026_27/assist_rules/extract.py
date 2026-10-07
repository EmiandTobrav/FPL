"""Conservative facts and useful proxies from a fixed candidate/goal episode.

Does not identify candidates automatically. It never treats a shot coordinate,
clearance endpoint or row count as a verified receiving position/touch total.
"""
import json
import math
import pandas as pd

PHYSICAL={1,2,3,7,8,10,11,12,13,14,15,16,41,52,54,61,74}
SCORER_ACTIONS={1,2,3,13,14,15,16,61}
AUXILIARY={44,45,49,50,51,58,83}

def qualifiers(value):
    if pd.isna(value):return None
    obj=json.loads(value)
    if not isinstance(obj,dict):raise ValueError('Expected qualifier object')
    return obj

def inside_box(x,y):
    # Opta's standardized non-metric geometry, not a 105 x 68 linear scaling.
    if x is None or y is None or not math.isfinite(x) or not math.isfinite(y):return None
    if not (0<=x<=100 and 0<=y<=100):return None
    return x>=83 and 21.1<=y<=78.9

def episode(events,case):
    match=events[events.match_id.eq(case['match_id'])].copy()
    goal=match[match.event_id.eq(case['goal_event_id'])]
    candidate=match[match.event_id.eq(case['candidate_event_id'])]
    if len(goal)!=1 or len(candidate)!=1:raise ValueError('Missing or duplicate event identity')
    g=goal.iloc[0];c=candidate.iloc[0]
    if c.period_id!=g.period_id:raise ValueError('Candidate and goal in different periods')
    if c.player_id!=case['candidate_player_id']:raise ValueError('Candidate player mismatch')
    if c.team_id!=g.team_id:raise ValueError('Candidate and scorer teams differ')
    if g.type_id!=16:raise ValueError('Target is not a goal event')
    start=c.minute*60+c.second;stop=g.minute*60+g.second
    if start>stop:raise ValueError('Candidate follows goal')
    match['clock']=match.minute*60+match.second
    seq=match[match.period_id.eq(g.period_id)&match.clock.between(start,stop)].copy()
    seq=seq.sort_values(['clock','event_id'])
    return c,g,seq

def extract(events,case):
    c,g,seq=episode(events,case)
    cq=qualifiers(c.qualifier_json);gq=qualifiers(g.qualifier_json)
    start=c.minute*60+c.second;stop=g.minute*60+g.second
    later=seq[seq.clock.gt(start)]
    scorer=later[later.player_id.eq(g.player_id)&later.type_id.isin(SCORER_ACTIONS)]
    first=scorer.iloc[0] if len(scorer) else g
    reception_limit=first.minute*60+first.second
    before_receipt=seq[seq.clock.gt(start)&seq.clock.lt(reception_limit)]
    defenders=before_receipt[before_receipt.team_id.ne(g.team_id)&before_receipt.type_id.isin(PHYSICAL)&before_receipt.player_id.notna()]
    # Distinct confirmed participants are a lower bound; repeated rows for a
    # single defender cannot establish an exact number of physical touches.
    lower=int(defenders.player_id.nunique())
    route='pass' if c.type_id==1 else ('touch' if c.type_id==61 else None)
    handballs=seq[seq.type_id.eq(4)&seq.team_id.ne(g.team_id)].copy()
    handballs=handballs.loc[handballs.qualifier_json.map(lambda v: '10' in (qualifiers(v) or {}) and '9' in (qualifiers(v) or {})).astype(bool)]
    if gq is not None and '9' in gq and len(handballs):route='handball'
    other_attackers=before_receipt[before_receipt.team_id.eq(g.team_id)&~before_receipt.player_id.isin([c.player_id,g.player_id])&before_receipt.type_id.isin(PHYSICAL)&before_receipt.player_id.notna()]
    own_rebound=None
    prior=seq[seq.player_id.eq(g.player_id)&seq.type_id.isin([14,15])&seq.clock.lt(stop)]
    if len(prior):
        shot=prior.iloc[-1]
        between=seq[seq.clock.gt(shot.clock)&seq.clock.lt(stop)]
        # Positive episode detection only: do not infer False when none found.
        safe=between.type_id.isin([10,11,41,51,58,61])
        no_other_attacker=~(between.team_id.eq(g.team_id)&between.player_id.ne(g.player_id)&between.type_id.isin(PHYSICAL))
        if stop-shot.clock<=8 and safe.all() and no_other_attacker.all():own_rebound=True
    facts=dict(route=route,own_goal=('28' in gq) if gq is not None else None,
      candidate_is_scorer=bool(c.player_id==g.player_id),scorer_own_rebound=own_rebound,
      scorer_lost_and_regained=None,candidate_last_attacking_touch=False if len(other_attackers) else None,
      sequence_verified=None,defensive_touches_min=lower,defensive_touches_max=None,
      defensive_touch_is_pass=True if defenders.type_id.isin([1,2]).any() else None,
      received_inside_box=None,intended_for_scorer=None,
      action_directly_caused_handball=None,conversion_direct=None)
    # Preserve markers and coordinate proxies for review, never as rule facts.
    clear=seq[seq.team_id.ne(g.team_id)&seq.type_id.eq(12)]
    clear_end=None
    if len(clear):
        q=qualifiers(clear.iloc[-1].qualifier_json)
        if q is not None and '140' in q and '141' in q:clear_end=[100-float(q['140']),100-float(q['141'])]
    markers=seq[seq.qualifier_json.map(lambda x:'384' in (qualifiers(x) or {}))]
    diagnostics=dict(candidate_type=int(c.type_id),candidate_time=start,goal_time=stop,period_id=int(g.period_id),
      source_rows=len(seq),auxiliary_rows=int(seq.type_id.isin(AUXILIARY).sum()),
      strict_defensive_contact_event_ids=[int(x) for x in defenders.event_id],
      distinct_defensive_contact_players=sorted(defenders.player_name.unique().tolist()),
      touch_count_is_lower_bound=True,unverified_same_second_order=bool(seq.clock.duplicated().any()),
      first_scorer_action_type=int(first.type_id),first_scorer_action_xy=[float(first.x),float(first.y)],
      shot_inside_box_proxy=inside_box(float(g.x),float(g.y)),
      clearance_end_xy_proxy=clear_end,
      clearance_end_inside_box_proxy=inside_box(*clear_end) if clear_end else None,
      q384_event_ids=[int(x) for x in markers.event_id],q384_interpretation='candidate pass-touch marker; not used as verified schema',
      handball_foul_event_ids=[int(x) for x in handballs.event_id],
      q281_player_id_value=(gq or {}).get('281'),q280_type_value=(gq or {}).get('280'))
    return facts,diagnostics,seq
