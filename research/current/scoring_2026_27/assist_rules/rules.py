"""Partial, three-valued FPL assist rules. None always means unresolved.

Inputs describe verified facts about one goal/candidate pair. This module does
not infer receiving location, intentions or complete touches from event rows.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Decision:
    awarded: bool | None
    reason: str
    missing: tuple[str,...] = ()

def evaluate(f):
    low,high=f.get('defensive_touches_min'),f.get('defensive_touches_max')
    for v in (low,high):
        if v is not None and (type(v) is not int or v<0):raise ValueError('Invalid touch bound')
    if low is not None and high is not None and low>high:raise ValueError('Inconsistent touch bounds')
    if f.get('own_goal') is True:return Decision(None,'own_goal_route_not_implemented',('own_goal_adjudication',))
    for field,reason in [('candidate_is_scorer','self_assist'),('scorer_own_rebound','scorer_converts_own_rebound'),('scorer_lost_and_regained','scorer_lost_and_regained')]:
        if f.get(field) is True:return Decision(False,reason)
    if f.get('candidate_last_attacking_touch') is False:return Decision(False,'another_attacker_intervened')
    route=f.get('route')
    if route in ('pass','touch'):
        if low is not None and low>=2:return Decision(False,'at_least_two_defensive_touches')
        if f.get('defensive_touch_is_pass') is True:return Decision(False,'defender_pass')
        if route=='touch' and low is not None and low>=1:return Decision(False,'inadvertent_touch_not_direct')
        if route=='pass' and low is not None and low>=1 and f.get('received_inside_box') is False and f.get('intended_for_scorer') is False:
            return Decision(False,'outside_box_unintended_recipient')
    if route=='handball' and f.get('action_directly_caused_handball') is False:
        return Decision(False,'handball_not_directly_caused')
    if route in ('handball','foul') and f.get('conversion_direct') is False:
        return Decision(False,'set_piece_not_scored_directly')
    if route not in ('pass','touch','handball','foul'):
        return Decision(None,'route_not_implemented_or_unknown',('route',))
    missing=[]
    for field,wanted in [('own_goal',False),('candidate_is_scorer',False),('scorer_own_rebound',False),('scorer_lost_and_regained',False),('candidate_last_attacking_touch',True),('sequence_verified',True)]:
        if f.get(field) is not wanted:missing.append(field)
    if route in ('pass','touch'):
        if high is None or high>1:missing.append('defensive_touch_upper_bound_at_most_one')
        if high is None or high>0:
            if f.get('defensive_touch_is_pass') is not False:missing.append('defensive_touch_is_pass')
        if route=='pass' and high!=0:
            if not (f.get('received_inside_box') is True or f.get('intended_for_scorer') is True):
                missing.append('received_inside_box_or_intended_for_scorer')
        if route=='touch' and high!=0:missing.append('direct_to_scorer')
    else:
        if f.get('conversion_direct') is not True:missing.append('conversion_direct')
        field='action_directly_caused_handball' if route=='handball' else 'candidate_won_foul'
        if f.get(field) is not True:missing.append(field)
    if missing:return Decision(None,'insufficient_verified_facts',tuple(missing))
    return Decision(True,'verified_'+route+'_criteria')
