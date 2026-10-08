"""Semantic safety cases shared by the new positive-event upper bounds."""
import unittest,importlib.util
from pathlib import Path
import pandas as pd
S=Path(__file__).resolve().parent.parent

def load(n):
 spec=importlib.util.spec_from_file_location(n,S/n/'certificates.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Boundaries(unittest.TestCase):
 def fixture(self,stage):
  defending=stage=='assist_pass_boundary';failed=stage=='assist_failed_pass_bounds';touch=stage=='assist_touch_bounds'
  goal=dict(season='2020-21',match_id='m',event_id=9,team_id='A',player_id='s',period_id=1,clock=50,qualifier_json='{}')
  rows=[dict(event_id=1,team_id='B' if defending else 'A',player_id='b' if defending else 'a',type_id=61 if touch else 1,outcome=0 if failed else 1,clock=20,period_id=1),dict(event_id=2,team_id='A',player_id='s',type_id=3,outcome=1,clock=40,period_id=1)]
  return goal,rows
 def classify(self,stage,goal,rows,ids=None):return load(stage).classify(goal,pd.DataFrame(rows),['A','B'],{},ids or {('m','A','a'):1,('m','A','s'):1,('m','A','c'):1})
 def test_positive_anchors(self):
  for stage in ['assist_pass_boundary','assist_attacking_touch_bounds','assist_failed_pass_bounds','assist_touch_bounds']:
   with self.subTest(stage=stage):
    g,r=self.fixture(stage);out=self.classify(stage,g,r);self.assertEqual(out[0]['candidates'],[] if stage=='assist_pass_boundary' else ['a'])
 def test_every_later_actor_is_retained(self):
  for stage in ['assist_pass_boundary','assist_attacking_touch_bounds','assist_failed_pass_bounds','assist_touch_bounds']:
   g,r=self.fixture(stage);r.append(dict(r[1],event_id=3,player_id='c',type_id=61,clock=45));self.assertIn('c',self.classify(stage,g,r)[0]['candidates'])
 def test_same_time_actor_retained(self):
  g,r=self.fixture('assist_attacking_touch_bounds');r.append(dict(r[1],event_id=3,player_id='c',clock=20));self.assertEqual(self.classify('assist_attacking_touch_bounds',g,r)[0]['candidates'],['a','c'])
 def test_scorer_does_not_replace_anchor(self):
  g,r=self.fixture('assist_attacking_touch_bounds');r[1]['type_id']=1;self.assertEqual(self.classify('assist_attacking_touch_bounds',g,r)[0]['candidates'],['a'])
 def test_later_anchor_does_replace_previous_actor(self):
  g,r=self.fixture('assist_attacking_touch_bounds');r.append(dict(r[0],event_id=3,player_id='c',clock=30));self.assertEqual(self.classify('assist_attacking_touch_bounds',g,r)[0]['candidates'],['c'])
 def test_ambiguous_boundary_abstains(self):
  g,r=self.fixture('assist_attacking_touch_bounds');r.append(dict(r[0],event_id=3,player_id='c'));self.assertEqual(self.classify('assist_attacking_touch_bounds',g,r),[])
 def test_own_pass_not_candidate(self):
  g,r=self.fixture('assist_attacking_touch_bounds');r[0]['player_id']='s';self.assertEqual(self.classify('assist_attacking_touch_bounds',g,r),[])
 def test_missing_actor_abstains(self):
  g,r=self.fixture('assist_failed_pass_bounds');r[1]['player_id']=None;self.assertEqual(self.classify('assist_failed_pass_bounds',g,r),[])
 def test_foreign_period_abstains(self):
  g,r=self.fixture('assist_attacking_touch_bounds');r[0]['period_id']=2;self.assertEqual(self.classify('assist_attacking_touch_bounds',g,r),[])
 def test_stale_boundary_abstains(self):
  g,r=self.fixture('assist_attacking_touch_bounds');r[0]['clock']=-11;self.assertEqual(self.classify('assist_attacking_touch_bounds',g,r),[])
 def test_no_source_marker_required(self):
  g,r=self.fixture('assist_attacking_touch_bounds');g['qualifier_json']='{"458":null}';self.assertEqual(self.classify('assist_attacking_touch_bounds',g,r)[0]['candidates'],['a'])
 def test_uncertain_sequences_abstain(self):
  for typ in [4,16,43,84,75,76]:
   with self.subTest(event_type=typ):
    g,r=self.fixture('assist_attacking_touch_bounds');r[1]['type_id']=typ;self.assertEqual(self.classify('assist_attacking_touch_bounds',g,r),[])
 def test_setpiece_and_own_goal_excluded(self):
  for qualifier in [9,26,28]:
   g,r=self.fixture('assist_attacking_touch_bounds');g['qualifier_json']='{"%d":null}'%qualifier;self.assertEqual(self.classify('assist_attacking_touch_bounds',g,r),[])
 def test_wrong_success_route_abstains(self):
  g,r=self.fixture('assist_attacking_touch_bounds');r[0]['outcome']=0;self.assertEqual(self.classify('assist_attacking_touch_bounds',g,r),[])
 def test_unidentified_candidate_abstains(self):
  g,r=self.fixture('assist_touch_bounds');r[0]['player_id']='unmapped';self.assertEqual(self.classify('assist_touch_bounds',g,r),[])
if __name__=='__main__':unittest.main()
