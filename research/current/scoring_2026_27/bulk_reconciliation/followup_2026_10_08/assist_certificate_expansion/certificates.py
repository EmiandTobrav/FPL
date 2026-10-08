"""Positive source certificates; unresolved recipients are never awarded by bounds."""
import json
import pandas as pd
ADMIN={20,51,58,83};PHYSICAL={1,2,3,4,7,8,10,11,12,13,14,15,16,41,52,54,61,74}
ACTION_TYPES={'ATTEMPT_SAVED':{15},'BLOCKED_SHOT':{15},'POST':{14},'PASS_LOST':{1},'OWN_GOAL':{1,13,14,15,61}}
def q(v):return json.loads(v) if isinstance(v,str) and v.strip() else {}
def pass_marker(s):
    qs=q(s);return '210' in qs and qs['210'] in [None,'16',16]
def clean_tail(mid,team,scorer,own):
    non=mid[~mid.type_id.isin(ADMIN)]
    if non[['type_id','team_id','player_id']].isna().any().any():return False
    allowed=set() if own else {scorer}
    return not (non.team_id.eq(team)&~non.player_id.isin(allowed)).any()
def classify(goal,events,teams,mapping,identities):
    qs=q(goal['qualifier_json']);own='28' in qs
    if len(teams)!=2 or goal['team_id'] not in teams:return []
    team=next(t for t in teams if t!=goal['team_id']) if own else goal['team_id']
    ep=events[events.period_id.eq(goal['period_id'])];out=[]
    if not set(qs)&{'9','26','28'} and {'29','55'}<=set(qs):
        ps=ep[ep.team_id.eq(team)&ep.type_id.eq(1)&ep.outcome.eq(1)&ep.player_id.ne(goal['player_id'])&ep.clock.between(goal['clock']-20,goal['clock'],inclusive='left')]
        ps=ps[ps.qualifier_json.map(pass_marker)]
        if len(ps)==1:
            c=ps.iloc[0];mid=ep[ep.clock.between(c.clock,goal['clock'])&~ep.event_id.isin([c.event_id,goal['event_id']])]
            if identities.get((goal['match_id'],team,c.player_id),0)==1 and clean_tail(mid,team,goal['player_id'],False):
                safe=mid.type_id.isin(ADMIN)|(mid.player_id.eq(goal['player_id'])&mid.type_id.isin([3,61]))
                ambiguous=mid.clock.isin([c.clock,goal['clock']])&mid.type_id.isin(PHYSICAL)
                award=bool(safe.all() and not ambiguous.any())
                out.append(dict(kind='pass210_flag',candidate_player_id=c.player_id,anchor_event_id=int(c.event_id),award=award,scoring_team_id=team))
    kind=qs.get('280');linked=qs.get('281');rawteam=qs.get('282')
    mapped=mapping.get((goal['season'],int(rawteam))) if isinstance(rawteam,str) and rawteam.isdigit() else rawteam
    if kind in ACTION_TYPES and linked and mapped==team and identities.get((goal['match_id'],team,linked),0)==1 and (own or linked!=goal['player_id']):
        # Direct set pieces use their own causal rules, not the general bound.
        if set(qs)&{'9','26'}:return out
        candidates=ep[ep.team_id.eq(team)&ep.player_id.eq(linked)&ep.type_id.isin(ACTION_TYPES[kind])&ep.clock.between(goal['clock']-20,goal['clock'],inclusive='left')]
        if len(candidates):
            latest=candidates.clock.max();cs=candidates[candidates.clock.eq(latest)]
            if len(cs)==1:
                c=cs.iloc[0];mid=ep[ep.clock.between(c.clock,goal['clock'])&~ep.event_id.isin([c.event_id,goal['event_id']])]
                if clean_tail(mid,team,goal['player_id'],own):out.append(dict(kind='linked_'+kind,candidate_player_id=linked,anchor_event_id=int(c.event_id),award=False,scoring_team_id=team))
    if len({r['candidate_player_id'] for r in out})>1:return []
    return out
