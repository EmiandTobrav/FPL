"""Decode explicitly present markers using a pinned published parser dictionary."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'assist_rules'))
from extract import extract,qualifiers,inside_box

TOUCH_TYPES={'383':'control','384':'pass','385':'clearance'}

def touch_type(q):
    if q is None:return None
    present=[v for k,v in TOUCH_TYPES.items() if k in q]
    return present[0] if len(present)==1 else None

def enrich(events,case):
    facts,diagnostics,seq=extract(events,case)
    c=seq[seq.event_id.eq(case['candidate_event_id'])].iloc[0]
    g=seq[seq.event_id.eq(case['goal_event_id'])].iloc[0]
    q=qualifiers(c.qualifier_json);gq=qualifiers(g.qualifier_json)
    evidence=[]
    subtype=touch_type(q)
    if c.type_id in (7,8) and subtype is not None:
        facts['route']='pass' if subtype=='pass' else 'touch'
        evidence.append(dict(field='route',value=facts['route'],event_id=int(c.event_id),basis='explicit_touch_subtype',qualifiers=[k for k in TOUCH_TYPES if k in q]))
    scorer_actions=seq[seq.player_id.eq(g.player_id)&seq.type_id.isin([1,2,3,9,13,14,15,16,49,50,61])]
    first_clock=scorer_actions.clock.min()
    defenders=seq[seq.team_id.ne(g.team_id)&seq.clock.gt(diagnostics['candidate_time'])&seq.clock.lt(first_clock)]
    for e in defenders.to_dict('records'):
        eq=qualifiers(e['qualifier_json'])
        if e['type_id'] in (7,8) and touch_type(eq)=='pass':
            facts['defensive_touch_is_pass']=True
            evidence.append(dict(field='defensive_touch_is_pass',value=True,event_id=int(e['event_id']),basis='explicit_touch_subtype',qualifiers=['384']))
    earlier=scorer_actions[scorer_actions.event_id.ne(g.event_id)]
    if gq is not None and '328' in gq and earlier.empty:
        loc=inside_box(float(g.x),float(g.y))
        if loc is not None:
            facts['received_inside_box']=loc
            evidence.append(dict(field='received_inside_box',value=loc,event_id=int(g.event_id),basis='first_touch_shot_marker_and_shot_coordinates',qualifiers=['328']))
    diagnostics['schema_enrichment']=evidence
    diagnostics['q384_interpretation']='explicit pass subtype, decoded using the pinned published parser in schema.json; absence remains unknown'
    diagnostics['schema_authority']='published_parser_dictionary_plus_official_scenario_crosschecks'
    diagnostics['absence_is_not_false']=True
    return facts,diagnostics,seq
