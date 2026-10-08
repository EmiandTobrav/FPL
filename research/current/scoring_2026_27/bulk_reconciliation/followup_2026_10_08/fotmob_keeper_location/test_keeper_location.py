import copy
import unittest
from build import located_saves

class LocationSafety(unittest.TestCase):
    def setUp(self):
        self.players = {11:dict(code=101,team_id=1,is_goalkeeper=True),
                        22:dict(code=202,team_id=2,is_goalkeeper=True),
                        33:dict(code=303,team_id=2,is_goalkeeper=False)}
        self.shot = dict(id=1,teamId=2,eventType='AttemptSaved',isOwnGoal=False,
                         isBlocked=False,isSavedOffLine=False,isOnTarget=True,
                         keeperId=11,isFromInsideBox=False)

    def test_direct_outside_save(self):
        keepers,reasons = located_saves([self.shot],self.players,{1:0,2:1})
        self.assertFalse(reasons)
        self.assertEqual(len(keepers[11]),1)
        self.assertIs(keepers[11][0]['isFromInsideBox'],False)

    def test_missing_origin_is_not_outside_or_zero(self):
        shot = dict(self.shot)
        del shot['isFromInsideBox']
        self.assertIn('missing_explicit_shot_origin',located_saves([shot],self.players,{1:0,2:1})[1])

    def test_missing_classification_abstains(self):
        for flag in ['isBlocked','isOnTarget','isSavedOffLine']:
            shot = dict(self.shot)
            del shot[flag]
            with self.subTest(flag=flag):
                self.assertIn('missing_save_classification',located_saves([shot],self.players,{1:0,2:1})[1])

    def test_block_and_goal_line_save_are_excluded(self):
        for flag in ['isBlocked','isSavedOffLine']:
            shot = dict(self.shot,**{flag:True})
            with self.subTest(flag=flag):
                keepers,reasons = located_saves([shot],self.players,{1:0,2:1})
                self.assertFalse(reasons)
                self.assertEqual(keepers[11],[])

    def test_unknown_wrong_and_outfield_keeper_rejected(self):
        for pid in [None,99,22,33]:
            shot = dict(self.shot,keeperId=pid)
            with self.subTest(pid=pid):
                self.assertIn('unknown_or_wrong_keeper',located_saves([shot],self.players,{1:0,2:1})[1])

    def test_incomplete_inventory_never_certifies_zero(self):
        _,reasons = located_saves([],self.players,{1:0,2:1})
        self.assertIn('incomplete_team_shot_inventory',reasons)

    def test_missing_explicit_total_never_certifies_zero(self):
        self.assertIn('incomplete_team_shot_inventory',located_saves([],self.players,{1:0,2:None})[1])

    def test_complete_explicit_zero_inventory(self):
        keepers,reasons = located_saves([],self.players,{1:0,2:0})
        self.assertFalse(reasons)
        self.assertEqual(keepers[11],[])

    def test_duplicate_shot_ids_are_rejected(self):
        self.assertIn('duplicate_or_missing_shot_id',located_saves([self.shot,copy.copy(self.shot)],self.players,{1:0,2:2})[1])

    def test_own_goal_is_not_an_opponent_keeper_save(self):
        keepers,reasons = located_saves([dict(self.shot,isOwnGoal=True)],self.players,{1:0,2:0})
        self.assertFalse(reasons)
        self.assertEqual(keepers[11],[])

if __name__=='__main__':
    unittest.main()
