import unittest,json
import pandas as pd
from certificates import classify,tail_candidates
class ActorTests(unittest.TestCase):
 def setup(self):
  g=dict(season='2020-21',match_id='m',team_id='a',player_id='scorer',period_id=1,clock=100,event_id=99,qualifier_json=json.dumps({'29':None,'55':'8'}))
  rows=[dict(event_id=1,type_id=1,team_id='a',player_id='passer',period_id=1,clock=90,outcome=1,qualifier_json=json.dumps({'210':16})),dict(event_id=2,type_id=3,team_id='a',player_id='other',period_id=1,clock=95,outcome=1,qualifier_json='{}')];ids={('m','a',p):1 for p in ['passer','other','scorer']};return g,pd.DataFrame(rows),ids
 def run_case(self,change=None):
  g,e,i=self.setup()
  if change:change(g,e,i)
  return classify(g,e,['a','b'],{},i)
 def test_union_includes_other_actor(self):self.assertEqual(self.run_case()[0]['candidates'],['other','passer'])
 def test_no_award(self):self.assertNotIn('award',self.run_case()[0])
 def test_opponent_not_candidate(self):self.assertEqual(self.run_case(lambda g,e,i:e.loc.__setitem__((1,'team_id'),'b')),[])
 def test_missing_player_blocks(self):self.assertEqual(self.run_case(lambda g,e,i:e.loc.__setitem__((1,'player_id'),None)),[])
 def test_missing_team_blocks(self):self.assertEqual(self.run_case(lambda g,e,i:e.loc.__setitem__((1,'team_id'),None)),[])
 def test_bad_identity_blocks(self):self.assertEqual(self.run_case(lambda g,e,i:i.__setitem__(('m','a','other'),2)),[])
 def test_absent_marker_blocks(self):self.assertEqual(self.run_case(lambda g,e,i:e.loc.__setitem__((0,'qualifier_json'),'{}')),[])
 def test_null_marker_positive(self):self.assertEqual(self.run_case(lambda g,e,i:e.loc.__setitem__((0,'qualifier_json'),'{"210":null}'))[0]['candidates'],['other','passer'])
 def test_non_goal_shot_marker_blocks(self):self.assertEqual(self.run_case(lambda g,e,i:e.loc.__setitem__((0,'qualifier_json'),'{"210":13}')),[])
 def test_period_isolation(self):self.assertEqual(self.run_case(lambda g,e,i:e.loc.__setitem__((0,'period_id'),2)),[])
 def test_window(self):self.assertEqual(self.run_case(lambda g,e,i:e.loc.__setitem__((0,'clock'),79)),[])
 def test_scorer_excluded(self):self.assertEqual(self.run_case(lambda g,e,i:e.loc.__setitem__((1,'player_id'),'scorer')),[])
 def test_direct_set_piece_blocked(self):self.assertEqual(self.run_case(lambda g,e,i:g.__setitem__('qualifier_json','{"9":null,"29":null,"55":"8"}')),[])
 def test_admin_does_not_add_actor(self):self.assertEqual(self.run_case(lambda g,e,i:e.loc.__setitem__((1,'type_id'),51)),[])
 def test_duplicate_pass_blocks(self):
  g,e,i=self.setup();extra=e.iloc[[0]].copy();extra['event_id']=3;e=pd.concat([e,extra],ignore_index=True);self.assertEqual(classify(g,e,['a','b'],{},i),[])
 def test_own_goal_actor_retained(self):
  g,e,i=self.setup();g.update(team_id='b',player_id='defender',qualifier_json=json.dumps({'28':None,'280':'OWN_GOAL','281':'passer','282':'a'}));out=classify(g,e,['a','b'],{},i);self.assertEqual(out[0]['candidates'],['other','passer'])
if __name__=='__main__':unittest.main()
