"""Three-valued target assist rules; evidence omissions never imply False/zero."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Decision:
    awarded: bool|None
    reason: str
    missing: tuple=()

def evaluate(f):
    route=f.get('route');own=f.get('own_goal') is True
    low,high=f.get('defensive_touches_min'),f.get('defensive_touches_max')
    for n in [low,high]:
        if n is not None and (type(n) is not int or n<0):raise ValueError('Invalid physical touch bound')
    if low is not None and high is not None and low>high:raise ValueError('Inconsistent touch bounds')
    if f.get('candidate_is_scorer') is True:return Decision(False,'self_assist')
    if f.get('scorer_own_rebound') is True:return Decision(False,'scorer_own_rebound')
    if f.get('scorer_lost_and_regained') is True:return Decision(False,'scorer_lost_and_regained')
    if route=='direct_corner_or_throw':return Decision(False,'winning_corner_or_throw_not_assist')
    if f.get('candidate_last_attacking_touch') is False:return Decision(False,'another_attacker_intervened')
    if own and f.get('own_goal_action_is_pass') is True:return Decision(False,'own_goal_action_is_pass')
    if route in ['pass','touch']:
        if low is not None and low>=2:return Decision(False,'multiple_defensive_contacts')
        if f.get('defensive_touch_is_pass') is True:return Decision(False,'defensive_pass')
        if route=='touch' and low is not None and low>0:return Decision(False,'inadvertent_touch_not_direct')
        if not own and route=='pass' and low is not None and low>0 and f.get('received_inside_box') is False and f.get('intended_for_scorer') is False:return Decision(False,'outside_box_unintended')
    if route=='shot':
        if f.get('shot_intent') is False:return Decision(False,'obvious_cross_or_pass')
        if f.get('defensive_touch_after_rebound') is True:return Decision(False,'defensive_touch_after_rebound')
        if f.get('deflection_before_rebound') is True and f.get('remained_on_target') is False:return Decision(False,'deflected_off_target')
    if route in ['foul','handball'] and f.get('conversion_direct') is False:return Decision(False,'not_direct_conversion')
    if route=='handball':
        if f.get('action_directly_caused_handball') is False:return Decision(False,'indirect_handball')
        if f.get('handball_preceded_by_shot_deflection') is True and f.get('remained_on_target') is False:return Decision(False,'handball_shot_deflected_off_target')
    if route not in ['pass','touch','shot','foul','handball']:return Decision(None,'unknown_route',('route',))
    needed={'own_goal':own,'candidate_is_scorer':False,'sequence_verified':True,'scorer_own_rebound':False,'scorer_lost_and_regained':False,'candidate_last_attacking_touch':True}
    if own:needed['own_goal_action_is_pass']=False
    missing=[k for k,v in needed.items() if f.get(k) is not v]
    if route in ['pass','touch']:
        if high is None or high>1:missing.append('defensive_touch_upper_bound')
        if high!=0 and f.get('defensive_touch_is_pass') is not False:missing.append('defensive_touch_type')
        if route=='touch' and high!=0:missing.append('direct_touch')
        if route=='pass' and not own and high!=0 and not (f.get('received_inside_box') is True or f.get('intended_for_scorer') is True):missing.append('receiving_location_or_intention')
    if route=='shot':
        for k,v in [('shot_intent',True),('direct_rebound',True),('defensive_touch_after_rebound',False)]:
            if f.get(k) is not v:missing.append(k)
        if f.get('deflection_before_rebound') is None:missing.append('pre_rebound_deflection')
        elif f.get('deflection_before_rebound') is True and f.get('remained_on_target') is not True:missing.append('remained_on_target')
    if route in ['foul','handball']:
        if f.get('conversion_direct') is not True:missing.append('conversion_direct')
        k='candidate_won_foul' if route=='foul' else 'action_directly_caused_handball'
        if f.get(k) is not True:missing.append(k)
        if route=='handball' and f.get('handball_preceded_by_shot_deflection') is True and f.get('remained_on_target') is not True:missing.append('remained_on_target')
        if route=='handball' and f.get('handball_preceded_by_shot_deflection') is None:missing.append('handball_deflection_context')
    if missing:return Decision(None,'insufficient_evidence',tuple(sorted(set(missing))))
    return Decision(True,'verified_'+('own_goal_' if own else '')+route)
