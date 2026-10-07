"""Automatic candidates with conservative, explicit source certificates.

A recorded assisted-goal/goal-creating-pass pair is positive evidence; an absent
assist marker is not a negative decision. Uncertified routes abstain.
"""
import json
import pandas as pd
from rules import evaluate

def certificate(route, **facts):
    base=dict(route=route,own_goal=False,candidate_is_scorer=False,sequence_verified=True,scorer_own_rebound=False,scorer_lost_and_regained=False,candidate_last_attacking_touch=True)
    return evaluate({**base,**facts}).awarded is True

PHYSICAL={1,2,3,4,7,8,10,11,12,13,14,15,16,41,52,54,61,74}
ADMIN={20,51,58,83}

def q(value):
    if not isinstance(value,str) or not value.strip():return {}
    result=json.loads(value)
    if not isinstance(result,dict):raise ValueError('Invalid qualifier object')
    return result

def classify(goal,events,teams):
    events=events[events.period_id.eq(goal['period_id'])]
    gq=q(goal['qualifier_json']);own='28' in gq
    scoring_team=next((t for t in teams if t!=goal['team_id']),None) if own else goal['team_id']
    out=dict(status='unresolved',recipient_player_id=None,scoring_team_id=scoring_team,scorer_player_id=goal['player_id'],own_goal=own,reason='insufficient_event_certificate',route='unknown',evidence_event_ids=str(int(goal['event_id'])),missing='sequence_or_target_rule_facts')
    if len(teams)!=2 or scoring_team is None:out.update(reason='team_identity_gap');return out,[]
    e=events[(events.period_id==goal['period_id'])&(events.clock<goal['clock'])].sort_values(['clock','event_id'])
    # Generate all attacking physical candidates in the frozen window, plus any explicit source recipient.
    a=e[e.team_id.eq(scoring_team)&e.player_id.notna()&e.type_id.isin(PHYSICAL)]
    candidates=a.groupby('player_id',sort=True).tail(1)
    candidate_rows=[dict(candidate_player_id=r.player_id,candidate_event_id=int(r.event_id),candidate_type=int(r.type_id),status='unresolved',reason='candidate_not_full_causal_proof') for r in candidates.itertuples()]
    linked=gq.get('281')
    if linked and linked not in set(candidates.player_id):candidate_rows.append(dict(candidate_player_id=linked,candidate_event_id=None,candidate_type=None,status='unresolved',reason='explicit_fantasy_recipient_marker'))
    # Own-goal, deflection, rebound and handball routes need episode-specific evidence.
    if own:out.update(reason='own_goal_action_and_contact_context',route='own_goal',missing='own_goal_action_type|defensive_contacts|continuity');return out,candidate_rows
    if '9' in gq or '26' in gq:
        out['route']='set_piece'
        if gq.get('280') in ['PENALTY_WON','FREE_KICK_WON'] and linked and gq.get('282')==scoring_team:
            if linked==goal['player_id']:
                out.update(status='no_assist',reason='scorer_is_explicit_foul_winner',route='self_foul',missing='')
            elif certificate('foul',conversion_direct=True,candidate_won_foul=True):
                out.update(status='awarded',recipient_player_id=linked,reason='explicit_goal_linked_foul_winner',route='foul',missing='')
        else:out.update(reason='set_piece_causality_unverified',missing='foul_winner_or_direct_handball_causality')
        return out,candidate_rows
    # Explicit own-rebound: scorer's shot followed immediately by a saved/post rebound.
    shots=e[e.player_id.eq(goal['player_id'])&e.type_id.isin([14,15])&e.clock.ge(goal['clock']-8)]
    if len(shots) and '458' in gq:
        shot=shots.iloc[-1];between=e[e.clock.gt(shot.clock)]
        allowed=between.type_id.isin(ADMIN|{10,11,41,61})
        attackers=between[between.team_id.eq(scoring_team)&between.player_id.ne(goal['player_id'])&between.type_id.isin(PHYSICAL)]
        same_clock=events[(events.clock==shot.clock)&events.event_id.ne(shot.event_id)&events.type_id.isin(PHYSICAL)]
        if allowed.all() and attackers.empty and same_clock.empty:
            out.update(status='no_assist',reason='explicit_scorer_own_rebound',route='self_rebound',missing='',evidence_event_ids=f"{int(shot.event_id)}|{int(goal['event_id'])}")
            return out,candidate_rows
    # Narrow direct-pass certificate: a successful intentional goal-creating pass and
    # an explicitly assisted intentional goal, without intervening rival actions or shots.
    passes=e[e.team_id.eq(scoring_team)&e.player_id.ne(goal['player_id'])&e.type_id.eq(1)&e.outcome.eq(1)&e.clock.ge(goal['clock']-20)]
    passes=passes[passes.qualifier_json.map(lambda s:'154' in q(s) and str(q(s).get('210'))=='16')]
    if len(passes)==1 and {'29','154','55'}<=set(gq):
        c=passes.iloc[0];middle=events[(events.clock>=c.clock)&(events.clock<=goal['clock'])&~events.event_id.isin([c.event_id,goal['event_id']])]
        scorer_ok=middle.player_id.eq(goal['player_id'])&middle.type_id.isin([3,61])
        # Even auxiliary rows at the boundary can conceal ordering; admin-only rows are ignored.
        safe=middle.type_id.isin(ADMIN)|scorer_ok
        ambiguous=middle.clock.isin([c.clock,goal['clock']])&middle.type_id.isin(PHYSICAL)
        if safe.all() and not ambiguous.any() and certificate('pass',defensive_touches_min=0,defensive_touches_max=0):
            out.update(status='awarded',recipient_player_id=c.player_id,reason='paired_intentional_direct_assist_markers',route='direct_pass',missing='',evidence_event_ids=f"{int(c.event_id)}|{int(goal['event_id'])}")
            return out,candidate_rows
    # Candidate-level facts may exclude one person; they do not settle the whole goal.
    for candidate in candidate_rows:
        if candidate['candidate_player_id']==goal['player_id']:candidate.update(status='denied',reason='self_assist')
    return out,candidate_rows
