import json
import unittest
from pathlib import Path
import pandas as pd
from rules import evaluate
from extract import extract,episode,inside_box,qualifiers
P=Path(__file__).resolve().parent

class RulesTests(unittest.TestCase):
    def setUp(self):
        self.f=dict(route='pass',own_goal=False,candidate_is_scorer=False,scorer_own_rebound=False,scorer_lost_and_regained=False,candidate_last_attacking_touch=True,sequence_verified=True,defensive_touches_min=1,defensive_touches_max=1,defensive_touch_is_pass=False,received_inside_box=True)
    def test_unknown_is_not_zero(self):
        f={**self.f,'defensive_touches_max':None}
        self.assertIsNone(evaluate(f).awarded)
    def test_upper_bound_can_suffice(self):
        self.assertTrue(evaluate({**self.f,'defensive_touches_min':0}).awarded)
    def test_defender_pass_overrides_inside_box(self):
        self.assertFalse(evaluate({**self.f,'defensive_touch_is_pass':True}).awarded)
    def test_outside_requires_verified_intention(self):
        f={**self.f,'received_inside_box':False}
        self.assertIsNone(evaluate(f).awarded)
        self.assertFalse(evaluate({**f,'intended_for_scorer':False}).awarded)
        self.assertTrue(evaluate({**f,'intended_for_scorer':True}).awarded)
    def test_two_touch_lower_bound_can_reject_without_upper_bound(self):
        self.assertFalse(evaluate(dict(route='pass',defensive_touches_min=2)).awarded)
    def test_inadvertent_touch_has_no_deflection_allowance(self):
        self.assertFalse(evaluate({**self.f,'route':'touch'}).awarded)
    def test_self_rebound_cancels_prior_candidate(self):
        self.assertFalse(evaluate({**self.f,'scorer_own_rebound':True}).awarded)
    def test_handball_needs_direct_causal_evidence(self):
        f={**self.f,'route':'handball','conversion_direct':True}
        self.assertIsNone(evaluate(f).awarded)
        self.assertTrue(evaluate({**f,'action_directly_caused_handball':True}).awarded)
    def test_bounds_and_unsupported_own_goal(self):
        with self.assertRaises(ValueError):evaluate({**self.f,'defensive_touches_min':2})
        self.assertIsNone(evaluate({**self.f,'own_goal':True}).awarded)

class EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=json.loads((P/'inputs/cases.json').read_text())
        cls.events=pd.concat([pd.read_csv(P.parent/'bps_recovery/inputs/official_assist_match_events.csv.gz'),pd.read_csv(P/'inputs/challenge_match_events.csv.gz')],ignore_index=True)
    def case(self,name,season='2024-25'):
        return next(c for c in self.cases if c['name']==name and c['season']==season)
    def test_shot_location_never_becomes_receiving_location(self):
        f,d,_=extract(self.events,self.case('B.Fernandes'))
        self.assertTrue(d['shot_inside_box_proxy']);self.assertFalse(d['clearance_end_inside_box_proxy'])
        self.assertIsNone(f['received_inside_box'])
    def test_aerial_and_error_rows_not_extra_contacts(self):
        f,d,_=extract(self.events,self.case('Pedro Porro'))
        self.assertEqual(f['defensive_touches_min'],1);self.assertIsNone(f['defensive_touches_max'])
        f,d,_=extract(self.events,self.case('Cunha'))
        self.assertEqual(f['defensive_touches_min'],2)
    def test_stoppage_time_does_not_mix_halves(self):
        c,g,s=episode(self.events,self.case('Cunha'))
        self.assertEqual(g.period_id,1);self.assertEqual(set(s.period_id),{1})
        self.assertFalse(s.event_id.eq(2767518817).any())
    def test_rebound_not_ordered_by_global_event_id(self):
        c=self.case('Marmoush','2025-26')
        f,_,_=extract(self.events,c);self.assertTrue(f['scorer_own_rebound'])
        shuffled=self.events.sample(frac=1,random_state=15)
        self.assertEqual(extract(shuffled,c)[0],f)
    def test_numeric_touch_type_not_silently_decoded(self):
        f,d,_=extract(self.events,self.case('Gross','2025-26'))
        self.assertTrue(d['q384_event_ids']);self.assertIsNone(f['route'])
    def test_pickford_var_delay_retains_original_incident(self):
        f,d,_=extract(self.events,self.case('Pickford'))
        self.assertEqual(f['route'],'handball');self.assertGreater(d['goal_time']-d['candidate_time'],240)
        self.assertEqual(len(d['handball_foul_event_ids']),1)
        self.assertIsNone(f['action_directly_caused_handball'])
    def test_missing_qualifiers_and_optapitch_boundary(self):
        self.assertIsNone(qualifiers(float('nan')))
        self.assertTrue(inside_box(83,21.1));self.assertFalse(inside_box(82.9,50))
        self.assertIsNone(inside_box(101,50))
    def test_duplicate_event_and_wrong_candidate_rejected(self):
        c=self.case('Scott')
        with self.assertRaises(ValueError):episode(self.events,{**c,'candidate_player_id':'wrong'})
        duplicate=pd.concat([self.events,self.events[self.events.event_id.eq(c['goal_event_id'])]])
        with self.assertRaises(ValueError):episode(duplicate,c)

if __name__=='__main__':unittest.main()
