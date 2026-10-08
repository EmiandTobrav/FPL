import unittest
import pandas as pd
from certificates import classify
class Bounds(unittest.TestCase):
 def setUp(self):
  self.goal=dict(season='2020-21',match_id='m',event_id=9,team_id='A',player_id='s',period_id=1,clock=50,qualifier_json='{}')
  self.rows=[dict(event_id=1,team_id='B',player_id='x',type_id=1,outcome=1,clock=10,period_id=1),dict(event_id=2,team_id='B',player_id='y',type_id=1,outcome=1,clock=20,period_id=1),dict(event_id=3,team_id='A',player_id='a',type_id=1,outcome=1,clock=30,period_id=1)]
 def runrule(self):return classify(self.goal,pd.DataFrame(self.rows),['A','B'],{}, {('m','A','a'):1,('m','A','s'):1})
 def test_bound(self):self.assertEqual(self.runrule()[0]['candidates'],['a'])
 def test_scorer_excluded(self):self.rows[2]['player_id']='s';self.assertEqual(self.runrule()[0]['candidates'],[])
 def test_one_pass_abstains(self):self.rows.pop(0);self.assertEqual(self.runrule(),[])
 def test_unknown_actor_abstains(self):self.rows[2]['player_id']=None;self.assertEqual(self.runrule(),[])
 def test_duplicate_identity_abstains(self):self.rows[2]['player_id']='unknown';self.assertEqual(self.runrule(),[])
 def test_attacker_between_passes_abstains(self):self.rows[2]['clock']=15;self.assertEqual(self.runrule(),[])
 def test_same_time_boundary_actor_kept(self):self.rows.append(dict(self.rows[2],event_id=4,clock=20));self.assertEqual(self.runrule(),[]) # attacker at boundary invalidates two-pass uninterrupted possession
 def test_deletion_abstains(self):self.rows[2]['type_id']=43;self.assertEqual(self.runrule(),[])
 def test_foul_abstains(self):self.rows[2]['type_id']=4;self.assertEqual(self.runrule(),[])
 def test_penalty_abstains(self):self.goal['qualifier_json']='{"9":null}';self.assertEqual(self.runrule(),[])
 def test_own_goal_abstains(self):self.goal['qualifier_json']='{"28":null}';self.assertEqual(self.runrule(),[])
 def test_different_period_abstains(self):self.rows[0]['period_id']=2;self.assertEqual(self.runrule(),[])
if __name__=='__main__':unittest.main()
