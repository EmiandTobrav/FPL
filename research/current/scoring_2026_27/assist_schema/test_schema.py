import json,unittest
from pathlib import Path
import pandas as pd
from qualifiers import touch_type,enrich
from rules import evaluate
P=Path(__file__).resolve().parent;S=P.parent

class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=json.loads((S/'assist_rules/inputs/cases.json').read_text())
        cls.events=pd.concat([pd.read_csv(S/'bps_recovery/inputs/official_assist_match_events.csv.gz'),pd.read_csv(S/'assist_rules/inputs/challenge_match_events.csv.gz')],ignore_index=True)
    def case(self,name,season='2024-25'):
        return next(c for c in self.cases if c['name']==name and c['season']==season)
    def test_missing_and_conflicting_subtypes_are_unknown(self):
        for q in [None,{}, {'384':None,'385':None}]:self.assertIsNone(touch_type(q))
    def test_explicit_three_way_subtype(self):
        for code,label in [('383','control'),('384','pass'),('385','clearance')]:self.assertEqual(touch_type({code:None}),label)
    def test_jensen_defender_pass_rejects(self):
        f,_,_=enrich(self.events,self.case('Jensen','2025-26'))
        self.assertTrue(f['defensive_touch_is_pass']);self.assertFalse(evaluate(f).awarded)
    def test_gross_subtype_does_not_invent_sequence_completeness(self):
        f,_,_=enrich(self.events,self.case('Gross','2025-26'))
        self.assertEqual(f['route'],'pass');self.assertIsNone(evaluate(f).awarded)
    def test_first_touch_receipt_and_counterexample(self):
        for name in ['Marmoush','Pedro Porro']:
            f,_,_=enrich(self.events,self.case(name));self.assertTrue(f['received_inside_box']);self.assertIsNone(evaluate(f).awarded)
        f,_,_=enrich(self.events,self.case('B.Fernandes'));self.assertIsNone(f['received_inside_box'])
    def test_prior_attempt_prevents_first_touch_receipt_inference(self):
        c=self.case('Marmoush','2025-26');events=self.events.copy();i=events[events.event_id.eq(c['goal_event_id'])].index[0]
        q=json.loads(events.loc[i,'qualifier_json']);q['328']=None;events.loc[i,'qualifier_json']=json.dumps(q)
        f,_,_=enrich(events,c);self.assertIsNone(f['received_inside_box']);self.assertTrue(f['scorer_own_rebound'])
    def test_missing_marker_not_read_as_false(self):
        f,_,_=enrich(self.events,self.case('Scott'));self.assertIsNone(f['defensive_touch_is_pass']);self.assertIsNone(f['intended_for_scorer'])
    def test_no_unsupported_positive_decisions(self):
        answers=[evaluate(enrich(self.events,c)[0]).awarded for c in self.cases]
        self.assertEqual(sum(x is False for x in answers),4);self.assertEqual(sum(x is None for x in answers),6);self.assertNotIn(True,answers)
if __name__=='__main__':unittest.main()
