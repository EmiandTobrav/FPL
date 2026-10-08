"""Failure-sensitive tests of mathematical bounds and admissible evidence."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from bounds import POSITIVE, NEGATIVE, upper_bound
from certificates import zero_certificate
from primary_predict import check_conservation_scope
from validate import acceptance, verify_fingerprints


def observation():
    row = dict(season='2019-20',position='MID',minutes=60,goals_scored=0,
        assists=0,clean_sheets=0,goals_conceded=0,penalties_missed=0,
        yellow_cards=0,red_cards=0,own_goals=0,legacy_net_tackles=-3,
        clearances_blocks_interceptions=5,times_tackled=None)
    row.update({field:0 for field in POSITIVE})
    row.update({field:None for field in NEGATIVE})
    return row


class BoundTests(unittest.TestCase):
    def test_signed_and_clipped_are_distinct_without_changing_raw_net(self):
        row=observation(); before=copy.deepcopy(row)
        self.assertEqual(upper_bound(row,'clipped')[0]-upper_bound(row,'signed')[0],6)
        self.assertEqual(row,before)

    def test_omitted_negative_is_an_upper_bound_not_a_zero_observation(self):
        row=observation(); top,terms,ignored=upper_bound(row,'clipped')
        self.assertIn('fouls',ignored); self.assertNotIn('fouls',terms)
        row['fouls']=5
        self.assertEqual(upper_bound(row,'clipped')[0],top-5)
        self.assertIsNone(observation()['fouls'])

    def test_incomplete_positive_component_never_has_a_bound(self):
        for field in [*POSITIVE,'clearances_blocks_interceptions']:
            row=observation(); row[field]=None
            with self.assertRaises(ValueError): upper_bound(row,'clipped')

    def test_invalid_known_negative_never_becomes_an_omission(self):
        for invalid in [float('inf'),-1,.5,'1',True]:
            row=observation(); row['fouls']=invalid
            with self.assertRaises(ValueError): upper_bound(row,'signed')

    def test_ambiguous_minute_clock_gets_maximum_upper_award(self):
        for minutes in [1,59,60,61,90]:
            row=observation(); row['minutes']=minutes
            self.assertEqual(upper_bound(row,'signed')[1]['minutes_upper'],6)

    def test_winning_goal_maximum_only_for_goal_scorer(self):
        row=observation(); self.assertEqual(upper_bound(row,'signed')[1]['winning_goal_upper'],0)
        row['goals_scored']=2
        self.assertEqual(upper_bound(row,'signed')[1]['winning_goal_upper'],3)

    def test_2024_extras_required_and_defender_concessions_counted(self):
        row=observation(); row.update(season='2024-25',position='DEF',goals_conceded=2)
        with self.assertRaises(ValueError): upper_bound(row,'clipped')
        row.update(goal_line_clearances=1,fouls_won=2,shots_on_target=3)
        terms=upper_bound(row,'clipped')[1]
        self.assertEqual([terms[k] for k in ['goal_line_clearances','fouls_won','shots_on_target','goals_conceded']],[3,2,6,-8])

    def test_invalid_population_and_passes_fail(self):
        for changes in [{'position':'GK'},{'season':'2025-26'},{'minutes':0},
                        {'totalPass':2,'accuratePass':3}]:
            row=observation(); row.update(changes)
            with self.assertRaises(ValueError): upper_bound(row,'signed')


class ConservationTests(unittest.TestCase):
    def test_exact_total_exhaustion_can_certify_missing_selected_zero(self):
        self.assertEqual(zero_certificate(3,[None,1,2,float('nan')],None),0)
        self.assertEqual(zero_certificate(0,[None,0],float('nan')),0)

    def test_unknown_total_positive_residual_or_overrun_never_zero(self):
        for total,values in [(None,[0]),(4,[1,2]),(2,[1,2])]:
            self.assertIsNone(zero_certificate(total,values,None))

    def test_invalid_inputs_and_known_selected_positive_never_zero(self):
        for bad in [float('inf'),-1,1.5,'0',True]:
            self.assertIsNone(zero_certificate(0,[bad],None))
            self.assertIsNone(zero_certificate(0,[],bad))
            self.assertIsNone(zero_certificate(bad,[],None))
        self.assertIsNone(zero_certificate(3,[3],1))

    def scope(self):
        source=pd.DataFrame([dict(season='2024-25',fixture=1,match_id='x',team_id='a',player_id='p')])
        fixtures=pd.DataFrame([dict(match_id='x',season='2024-2025',home_team_id='a',away_team_id='b')]).set_index('match_id')
        verified=pd.DataFrame([dict(season='2024-25',fixture=1,match_id='x')]).set_index(['season','fixture'])
        return source,fixtures,verified

    def test_wrong_club_season_and_fixture_scope_fail(self):
        check_conservation_scope(*self.scope())
        for field,bad in [('team_id','c'),('season','2023-24'),('match_id','z'),('fixture',2)]:
            args=self.scope(); args[0].loc[0,field]=bad
            with self.assertRaises(ValueError): check_conservation_scope(*args)

    def test_duplicate_participants_cannot_exhaust_total_twice(self):
        source,fixtures,verified=self.scope()
        with self.assertRaises(ValueError):
            check_conservation_scope(pd.concat([source,source]),fixtures,verified)


class GateTests(unittest.TestCase):
    def protocol(self):
        return {'acceptance':dict(minimum_discriminating_rows=20,
            minimum_discriminating_rows_per_season=2,required_seasons=['2019-20','2020-21'],
            maximum_clipped_bound_violations=0,maximum_primary_explicit_disagreements=0)}

    def test_one_clipped_violation_or_source_disagreement_blocks_rule(self):
        evidence=pd.DataFrame({'season':['2019-20']*10+['2020-21']*10})
        self.assertTrue(acceptance(self.protocol(),evidence,0,0)[0])
        self.assertFalse(acceptance(self.protocol(),evidence,1,0)[0])
        self.assertFalse(acceptance(self.protocol(),evidence,0,1)[0])

    def test_total_count_cannot_hide_uncovered_season(self):
        evidence=pd.DataFrame({'season':['2019-20']*21})
        self.assertFalse(acceptance(self.protocol(),evidence,0,0)[0])

    def test_nineteen_controls_do_not_pass_twenty_control_gate(self):
        evidence=pd.DataFrame({'season':['2019-20']*10+['2020-21']*9})
        self.assertFalse(acceptance(self.protocol(),evidence,0,0)[0])

    def test_changed_input_or_output_stops_outcome_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); path=root/'frozen'; path.write_bytes(b'before')
            proof={'frozen':hashlib.sha256(path.read_bytes()).hexdigest()}
            verify_fingerprints(root,proof)
            path.write_bytes(b'after')
            with self.assertRaises(ValueError): verify_fingerprints(root,proof)


if __name__=='__main__': unittest.main()
