import unittest
import pandas as pd
from validate_bps import calculate,bonus
class Tests(unittest.TestCase):
 def row(self,**kwargs):
  r=dict(position='MID',minutes=90,assists=0,clean_sheets=0,goals_conceded=0,penalties_missed=0,yellow_cards=0,red_cards=0,own_goals=0);r.update(kwargs);return r
 def test_cbi_threshold(self):
  self.assertEqual(calculate(self.row(pl_total_clearance=2)),6)
  self.assertEqual(calculate(self.row(pl_total_clearance=3)),7)
 def test_keeper_big_chance_penalty(self):
  self.assertEqual(calculate(self.row(position='GK',pl_saves=1,pl_saved_ibox=1,pl_big_chance_saves=1,pl_penalty_save=1)),17)
 def test_penalty_goal(self):
  self.assertEqual(calculate(self.row(position='FWD',pl_goals=1,pl_att_pen_goal=1)),18)
  self.assertEqual(calculate(self.row(position='FWD',pl_goals=1)),30)
 def test_pass_minimum(self):
  self.assertEqual(calculate(self.row(pl_total_pass=29,pl_accurate_pass=29)),6)
  self.assertEqual(calculate(self.row(pl_total_pass=30,pl_accurate_pass=27)),12)
 def test_tackled_no_penalty(self):
  self.assertEqual(calculate(self.row(pl_times_tackled=8)),6)
 def test_ties(self):
  self.assertEqual(bonus(pd.Series([30,30,20,10])).tolist(),[3,3,1,0])
  self.assertEqual(bonus(pd.Series([30,20,20,10])).tolist(),[3,2,2,0])
  self.assertEqual(bonus(pd.Series([30,20,10,10])).tolist(),[3,2,1,1])
if __name__=='__main__':unittest.main()
