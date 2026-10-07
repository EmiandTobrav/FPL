import unittest
import json
import pandas as pd
from rules import evaluate
from engine import classify

class RulesTests(unittest.TestCase):
 def setUp(self):
  self.base=dict(route='pass',own_goal=False,candidate_is_scorer=False,sequence_verified=True,scorer_own_rebound=False,scorer_lost_and_regained=False,candidate_last_attacking_touch=True,defensive_touches_min=0,defensive_touches_max=0)
 def test_direct_and_missing(self):
  self.assertTrue(evaluate(self.base).awarded)
  self.assertIsNone(evaluate({**self.base,'sequence_verified':None}).awarded)
 def test_unknown_touch_upper_bound(self):
  self.assertIsNone(evaluate({**self.base,'defensive_touches_max':None}).awarded)
 def test_two_contacts(self):
  self.assertFalse(evaluate({**self.base,'defensive_touches_min':2,'defensive_touches_max':None}).awarded)
 def test_box_or_intention(self):
  f={**self.base,'defensive_touches_min':1,'defensive_touches_max':1,'defensive_touch_is_pass':False,'received_inside_box':False}
  self.assertIsNone(evaluate(f).awarded)
  self.assertTrue(evaluate({**f,'intended_for_scorer':True}).awarded)
  self.assertFalse(evaluate({**f,'intended_for_scorer':False}).awarded)
 def test_inadvertent_touch(self):
  self.assertTrue(evaluate({**self.base,'route':'touch'}).awarded)
  self.assertFalse(evaluate({**self.base,'route':'touch','defensive_touches_min':1,'defensive_touches_max':1}).awarded)
 def test_own_goal_pass(self):
  self.assertTrue(evaluate({**self.base,'own_goal':True,'own_goal_action_is_pass':False}).awarded)
  self.assertFalse(evaluate({**self.base,'own_goal':True,'own_goal_action_is_pass':True}).awarded)
 def test_rebound(self):
  f={**self.base,'route':'shot','shot_intent':True,'direct_rebound':True,'defensive_touch_after_rebound':False,'deflection_before_rebound':False}
  self.assertTrue(evaluate(f).awarded)
  self.assertFalse(evaluate({**f,'defensive_touch_after_rebound':True}).awarded)
  self.assertIsNone(evaluate({**f,'deflection_before_rebound':True}).awarded)
  self.assertFalse(evaluate({**f,'deflection_before_rebound':True,'remained_on_target':False}).awarded)
 def test_foul_and_handball(self):
  f={**self.base,'route':'foul','conversion_direct':True,'candidate_won_foul':True}
  self.assertTrue(evaluate(f).awarded)
  self.assertFalse(evaluate({**f,'candidate_is_scorer':True}).awarded)
  h={**self.base,'route':'handball','conversion_direct':True,'action_directly_caused_handball':True,'handball_preceded_by_shot_deflection':False}
  self.assertTrue(evaluate(h).awarded)
  self.assertIsNone(evaluate({**h,'handball_preceded_by_shot_deflection':None}).awarded)
 def test_denials(self):
  for k in ['candidate_is_scorer','scorer_own_rebound','scorer_lost_and_regained']:
   self.assertFalse(evaluate({**self.base,k:True}).awarded)
  self.assertFalse(evaluate({**self.base,'route':'direct_corner_or_throw'}).awarded)
 def test_invalid_bounds(self):
  with self.assertRaises(ValueError):evaluate({**self.base,'defensive_touches_min':2})

class EngineTests(unittest.TestCase):
 def setUp(self):
  self.goal=dict(event_id=99,period_id=1,clock=100,team_id='a',player_id='scorer',type_id=16,outcome=1,qualifier_json=json.dumps({'29':'','154':'','55':'10'}))
  self.p=dict(event_id=9,period_id=1,clock=98,team_id='a',player_id='passer',type_id=1,outcome=1,qualifier_json=json.dumps({'154':'','210':'16'}))
 def run_goal(self,extra=(),goal=None):
  g=goal or self.goal
  return classify(g,pd.DataFrame([self.p,g,*extra]),['a','b'])[0]
 def test_direct_certificate(self):self.assertEqual(self.run_goal()['recipient_player_id'],'passer')
 def test_missing_assisted_marker(self):self.assertEqual(self.run_goal(goal={**self.goal,'qualifier_json':'{}'})['status'],'unresolved')
 def test_opponent_contact(self):
  self.assertEqual(self.run_goal([{**self.p,'event_id':10,'clock':99,'team_id':'b','type_id':7}])['status'],'unresolved')
 def test_same_second_order(self):
  self.assertEqual(self.run_goal([{**self.p,'event_id':10,'clock':98,'player_id':'scorer','type_id':61}])['status'],'unresolved')
 def test_other_period_ignored(self):
  self.assertEqual(self.run_goal([{**self.p,'event_id':10,'clock':99,'period_id':2,'team_id':'b','type_id':7}])['status'],'awarded')
 def test_own_goal_team(self):
  r=self.run_goal(goal={**self.goal,'qualifier_json':'{"28":""}'})
  self.assertEqual(r['scoring_team_id'],'b');self.assertEqual(r['status'],'unresolved')
 def test_foul_recipient(self):
  r=self.run_goal(goal={**self.goal,'qualifier_json':json.dumps({'9':'','280':'PENALTY_WON','281':'passer','282':'a'})})
  self.assertEqual(r['recipient_player_id'],'passer')
 def test_wrong_foul_team(self):
  r=self.run_goal(goal={**self.goal,'qualifier_json':json.dumps({'9':'','280':'PENALTY_WON','281':'passer','282':'b'})})
  self.assertEqual(r['status'],'unresolved')
 def test_candidate_denial_not_goal_zero(self):
  r=self.run_goal(goal={**self.goal,'qualifier_json':'{"458":""}'})
  self.assertEqual(r['status'],'unresolved')


class AggregationTests(unittest.TestCase):
 def setUp(self):
  from build import aggregate
  self.aggregate=aggregate
  self.known=dict(event_id=1,status='awarded',recipient_player_id='a',scorer_player_id='b',own_goal=False)
  self.unknown=dict(event_id=2,status='unresolved',recipient_player_id=None,scorer_player_id='b',own_goal=False)
 def test_partial_award_is_lower_bound(self):
  r=self.aggregate([self.known,self.unknown],'a',2,True)
  self.assertIsNone(r['value']);self.assertEqual(r['lower_bound'],1)
 def test_scorer_cannot_assist_own_goal(self):
  r=self.aggregate([self.unknown],'b',1,True)
  self.assertEqual(r['value'],0)
 def test_source_gap_never_zero(self):
  r=self.aggregate([],'a',1,False)
  self.assertIsNone(r['value']);self.assertIsNone(r['lower_bound'])
 def test_official_scoreless_team(self):self.assertEqual(self.aggregate([],'a',0,False)['value'],0)
 def test_whole_goal_no_assist(self):
  self.assertEqual(self.aggregate([{**self.unknown,'status':'no_assist'}],'a',1,True)['value'],0)
 def test_candidate_denial_only_that_candidate(self):
  ds={(2,'a')}
  self.assertEqual(self.aggregate([self.unknown],'a',1,True,ds)['value'],0)
  self.assertIsNone(self.aggregate([self.unknown],'c',1,True,ds)['value'])
 def test_count_mismatch_quarantines(self):self.assertIsNone(self.aggregate([self.known],'a',2,True)['value'])
 def test_identity_conflict_quarantines(self):self.assertIsNone(self.aggregate([self.known],'a',1,False)['value'])

class OutputTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from pathlib import Path
  cls.p=Path(__file__).resolve().parent
  cls.before=pd.read_csv(cls.p.parent/'delta_input_audit/requirements.csv.gz',low_memory=False)
  cls.after=pd.read_csv(cls.p/'requirements.csv.gz',low_memory=False)
  cls.totals=pd.read_csv(cls.p/'player_match_totals.csv.gz',low_memory=False)
 def test_non_assist_cells_identical(self):
  mask=self.before.field.ne('assists_2026_27')
  pd.testing.assert_frame_equal(self.before[mask],self.after.loc[mask,self.before.columns],check_dtype=False)
 def test_all_fpl_assists_preserved(self):
  m=self.totals.season.eq('2025-26')
  self.assertTrue(self.totals.loc[m,'value'].eq(self.totals.loc[m,'historical_fpl_assists']).all())
 def test_protected_assist_cells_unchanged(self):
  m=self.before.field.eq('assists_2026_27')&~self.before.is_open
  pd.testing.assert_frame_equal(self.before[m],self.after.loc[m,self.before.columns],check_dtype=False)
 def test_four_official_additions_complete(self):
  d=pd.read_csv(self.p/'resolved_assist_changes.csv')
  self.assertEqual(set(d.code),{438234,441164,503139,111234})
  self.assertTrue(d.assist_delta.eq(1).all())
 def test_unknown_totals_stay_missing(self):
  d=self.totals
  self.assertTrue(d.loc[d.unknown_goals.gt(0),'value'].isna().all())
 def test_deduplicated_union(self):
  key=['season','fixture','code'];d=self.after
  self.assertFalse(d.duplicated(key+['field']).any())
  result=json.loads((self.p/'findings.json').read_text())
  self.assertEqual(result['unique_affected_player_matches'],len(d.loc[d.is_open,key].drop_duplicates()))
  self.assertEqual(result['unique_open_or_external_quality_player_matches'],len(d.loc[d.is_open|d.needs_external_quality_review,key].drop_duplicates()))
 def test_no_goal_gap_mislabeled_conflict(self):
  d=pd.read_csv(self.p/'scorer_identity_audit.csv')
  self.assertTrue(d.loc[d.audit_status.eq('missing_goal_inventory'),'observed'].isna().all())
  f=json.loads((self.p/'findings.json').read_text())
  self.assertEqual(f['source_scorer_conflict_matches'],0)
  self.assertEqual(f['missing_archive_fixtures'],21);self.assertEqual(f['additional_event_gap_fixtures'],3)
 def test_frozen_prediction_unchanged(self):
  import hashlib
  f=json.loads((self.p/'prediction_freeze.json').read_text())
  for name,digest in f['inputs'].items():self.assertEqual(hashlib.sha256((self.p/name).read_bytes()).hexdigest(),digest)
  self.assertEqual(hashlib.sha256((self.p/'raw_goal_decisions.csv.gz').read_bytes()).hexdigest(),f['prediction_sha256'])
 def test_holdout_separate_from_development(self):
  plan=pd.read_csv(self.p/'validation_plan.csv')
  cases=json.loads((self.p.parent/'assist_rules/inputs/cases.json').read_text())
  used={(c['season'],c['fixture']) for c in cases}
  self.assertTrue(all((r.season,r.fixture) not in used for r in plan.itertuples()))
  self.assertTrue(plan.date.ge('2026-01-01').all())
 def test_unvalidated_route_not_auto_approved(self):
  d=pd.read_csv(self.p/'goal_decisions.csv.gz');v=json.loads((self.p/'validation_summary.json').read_text())
  automatic=d[d.status.ne('unresolved')&d.evidence_scope.eq('frozen_event_certificate_with_route_control')]
  self.assertTrue(automatic.route.isin(v['qualified_routes']).all())
 def test_goals_scored_not_sparse_zero_evidence(self):
  d=self.totals[(self.totals.season!='2025-26')&self.totals.reason.eq('goal_coverage_or_identity_gap')]
  self.assertTrue(d.value.isna().all())

if __name__=='__main__':unittest.main()
