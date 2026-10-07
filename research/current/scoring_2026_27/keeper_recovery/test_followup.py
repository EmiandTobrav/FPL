import unittest
import pandas as pd
from reconcile_followup import paired_saves,team_shot_count

class FollowupTests(unittest.TestCase):
    def row(self):
        return pd.Series(dict(match_id='m',player_id='g',team_id='d',fotmob_saves=1,explicit_big_chance_saves=None))
    def events(self):
        return pd.DataFrame([
            dict(match_id='m',player_id='g',team_id='d',event_id=2,type_id=10,period_id=2,minute=60,second=1,q={}),
            dict(match_id='m',player_id='s',team_id='a',event_id=1,type_id=15,period_id=2,minute=60,second=0,q={'214':None})])
    def thin(self,big=True):
        shots=pd.DataFrame([dict(player_name='s',type_id=15,big_chance=big,is_blocked=None)])
        shooters=pd.DataFrame([dict(player_name='s',total_shots=1,goals=0,shots_blocked=0)])
        return shots,shooters
    def test_complete_save_inventory(self):
        self.assertEqual(paired_saves(self.row(),{'pl_saves':1},self.events())[0],1)
    def test_incomplete_save_inventory_rejected(self):
        r=self.row();r.fotmob_saves=2
        self.assertIsNone(paired_saves(r,{'pl_saves':2},self.events())[0])
    def test_wrong_period_rejected(self):
        e=self.events();e.loc[1,'period_id']=1
        self.assertIsNone(paired_saves(self.row(),{'pl_saves':1},e)[0])
    def test_explicit_counter_conflict_not_silently_overridden(self):
        r=self.row();r.explicit_big_chance_saves=0
        self.assertIsNone(paired_saves(r,{'pl_saves':1},self.events())[0])
    def test_zero_blocks_resolves_relevant_shot(self):
        self.assertEqual(team_shot_count(*self.thin()),1)
    def test_all_blocks_excluded(self):
        s,p=self.thin();p.loc[0,'shots_blocked']=1
        self.assertEqual(team_shot_count(s,p),0)
    def test_mixed_blocks_remain_ambiguous(self):
        s,p=self.thin();s=pd.concat([s,s],ignore_index=True);s.loc[1,'big_chance']=False
        p.loc[0,['total_shots','shots_blocked']]=[2,1]
        self.assertIsNone(team_shot_count(s,p))
    def test_incomplete_shots_rejected(self):
        s,p=self.thin();p.loc[0,'total_shots']=2
        self.assertIsNone(team_shot_count(s,p))
    def test_missing_chance_flag_rejected(self):
        s,p=self.thin(None)
        self.assertIsNone(team_shot_count(s,p))
    def test_zero_requires_explicit_nonbig_shots(self):
        self.assertEqual(team_shot_count(*self.thin(False)),0)

if __name__=='__main__':unittest.main()
