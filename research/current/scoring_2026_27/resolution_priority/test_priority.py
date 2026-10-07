import hashlib
import json
import unittest

import pandas as pd

from build import KEY, P, S, bands, contribution, defensive_bounds, pass_score, winner_zero


class RuleTests(unittest.TestCase):
    def test_distinct_minute_boundaries(self):
        self.assertEqual([bands(x) for x in [0,1,59,60,61]],[(0,0),(1,3),(1,3),(2,3),(2,6)])

    def test_pass_attempt_threshold(self):
        self.assertEqual(pass_score(29,29),0)
        self.assertEqual(pass_score(30,27),6)
        self.assertEqual(pass_score(30,24),4)
        self.assertEqual(pass_score(30,21),2)
        self.assertEqual(pass_score(30,20),0)

    def test_invalid_passing_not_clipped(self):
        with self.assertRaises(ValueError): pass_score(30,31)

    def test_missing_defensive_count_is_not_zero(self):
        self.assertEqual(defensive_bounds('MID',[3,3,None]),(0,2))

    def test_partial_lower_bound_proves_award(self):
        self.assertEqual(defensive_bounds('MID',[12,None,None]),(2,2))

    def test_defender_does_not_need_recoveries(self):
        self.assertEqual(defensive_bounds('DEF',[5,4,None]),(0,0))
        self.assertEqual(defensive_bounds('DEF',[5,5,None]),(2,2))

    def test_keeper_not_defcon_eligible(self):
        self.assertEqual(defensive_bounds('GK',[None,None,None]),(0,0))

    def test_winning_goal_requires_team_win(self):
        self.assertTrue(winner_zero(2,2))
        self.assertTrue(winner_zero(1,2))
        self.assertFalse(winner_zero(2,1))
        self.assertFalse(winner_zero(None,0))

    def test_penalty_split_position_specific(self):
        for pos in ['GK','DEF']:
            self.assertEqual(contribution('penalty_goals',2,pos),(0,0))
        self.assertEqual(contribution('penalty_goals',1,'MID'),(0,-6))
        self.assertEqual(contribution('penalty_goals',1,'FWD'),(0,-12))

    def test_keeper_save_point_threshold(self):
        self.assertEqual(contribution('saves',2,'GK'),(0,4))
        self.assertEqual(contribution('saves',3,'GK'),(1,6))


class OutputTests(unittest.TestCase):
    def test_queue_partition_and_union(self):
        q=pd.read_csv(P/'resolution_queue.csv.gz',usecols=KEY+['field','scoring_requirement_discharged'])
        f=json.loads((P/'findings.json').read_text())
        self.assertFalse(q.duplicated(KEY+['field']).any())
        self.assertEqual(len(q),f['input_open_cells'])
        remaining=q[~q.scoring_requirement_discharged]
        self.assertEqual(len(remaining),f['remaining_scoring_requirement_cells'])
        self.assertEqual(len(remaining[KEY].drop_duplicates()),f['remaining_unique_player_matches'])
        self.assertEqual(int(pd.read_csv(P/'action_summary.csv').cells.sum()),len(q))

    def test_only_proven_team_results_enter_supplement(self):
        d=pd.read_csv(P/'documented_zero_supplement.csv')
        self.assertFalse(d.duplicated(KEY+['field']).any())
        self.assertTrue(d.value.eq(0).all())
        self.assertTrue(d.own_team_goals.le(d.opponent_goals).all())
        self.assertTrue(pd.read_csv(P/'winning_goal_contradictions.csv').empty)

    def test_subset_screen_abstains_despite_large_candidate_pool(self):
        f=pd.read_csv(P/'subset_bound_screen.csv')
        self.assertFalse(f.approved.any())
        self.assertGreater(int(f.violations.sum()),0)
        self.assertGreater(int(f.potential_zero_cells.sum()),10000)

    def test_candidate_agreement_not_discharge(self):
        q=pd.read_csv(P/'resolution_queue.csv.gz',usecols=['action','scoring_requirement_discharged','raw_stat_still_unresolved'])
        neutral=q[q.action.isin(['minutes_same_candidate_scoring_bands','passes_same_candidate_bps_band'])]
        self.assertGreater(len(neutral),0)
        self.assertFalse(neutral.scoring_requirement_discharged.any())
        self.assertTrue(neutral.raw_stat_still_unresolved.all())

    def test_frozen_inputs_outputs_and_code_hashes(self):
        manifest=json.loads((P/'manifest.json').read_text())
        for name,digest in manifest['inputs_sha256'].items():
            self.assertEqual(hashlib.sha256((S.parent/name).read_bytes()).hexdigest(),digest)
        for section in ['outputs_sha256','code_sha256']:
            for name,digest in manifest[section].items():
                self.assertEqual(hashlib.sha256((P/name).read_bytes()).hexdigest(),digest)


if __name__ == '__main__': unittest.main()
