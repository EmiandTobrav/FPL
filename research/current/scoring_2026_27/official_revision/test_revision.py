import hashlib
import json
import unittest

import pandas as pd

from build import KEY, P, R, minute_components, paired_revision, team_totals


class TransformTests(unittest.TestCase):
    def fixture(self):
        return pd.DataFrame({'code':[10,20],'was_home':[True,False],
                             'goals_scored':[1,0],'own_goals':[0,1]}).set_index('code')

    def test_atomic_transfer_preserves_score_and_input(self):
        old = self.fixture()
        revised = paired_revision(old,10,20)
        self.assertEqual(team_totals(old),(2,0))
        self.assertEqual(team_totals(revised),(2,0))
        self.assertEqual(old.loc[20,'own_goals'],1)
        self.assertEqual(revised.loc[20,'own_goals'],0)

    def test_naive_overlay_double_counts_goal(self):
        naive = self.fixture()
        naive.loc[10,'goals_scored'] += 1
        self.assertEqual(team_totals(naive),(3,0))

    def test_missing_own_goal_is_not_zero(self):
        frame = self.fixture()
        frame.loc[20,'own_goals'] = float('nan')
        with self.assertRaises(ValueError): paired_revision(frame,10,20)
        with self.assertRaises(ValueError): team_totals(frame)

    def test_cannot_apply_twice(self):
        frame = paired_revision(self.fixture(),10,20)
        with self.assertRaises(ValueError): paired_revision(frame,10,20)

    def test_same_team_rejected(self):
        frame = self.fixture()
        frame['was_home'] = True
        with self.assertRaises(ValueError): paired_revision(frame,10,20)

    def test_proven_participation_band(self):
        self.assertEqual(minute_components(1,59),(1,3))
        for lo,hi in [(0,17),(59,60),(60,61)]:
            with self.assertRaises(ValueError): minute_components(lo,hi)
        self.assertEqual(minute_components(60,60),(2,3))


class ArtifactTests(unittest.TestCase):
    def test_all_input_hashes_match(self):
        for path,digest in json.loads((P/'manifest.json').read_text())['inputs'].items():
            self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),digest,path)

    def test_eight_corrections_four_conflicts(self):
        p = pd.read_csv(P/'counter_supplement.csv')
        self.assertEqual(len(p),8)
        self.assertFalse(p.duplicated(KEY+['field']).any())
        self.assertEqual(p.previous_status.eq('source_conflict').sum(),4)
        self.assertEqual(set(p.field),{'goals','own_goals'})
        self.assertTrue(p[p.field.eq('own_goals')].revised_value.eq(0).all())

    def test_every_match_has_balanced_pair(self):
        p = pd.read_csv(P/'counter_supplement.csv')
        for _,g in p.groupby(['season','fixture']):
            self.assertEqual(set(g.field),{'goals','own_goals'})
            self.assertEqual((g.revised_value-g.historical_fpl_value).sum(),0)
        audit = pd.read_csv(P/'goal_balance_audit.csv')
        for side in ['home','away']:
            self.assertTrue(audit[f'official_{side}'].eq(audit[f'revised_{side}']).all())
        self.assertTrue((audit.naive_home+audit.naive_away).eq(audit.official_home+audit.official_away+1).all())

    def test_assists_not_automatically_awarded(self):
        deps = pd.read_csv(P/'event_dependencies.csv')
        self.assertEqual(len(deps[deps.field.eq('assists_2026_27')]),4)
        self.assertFalse(deps.additional_missing_cell.any())
        findings = json.loads((P/'findings.json').read_text())
        self.assertEqual(findings['full_bps_or_bonus_labels_produced'],0)

    def test_counts_and_overlap_are_not_summed(self):
        q = pd.read_csv(P/'resolution_queue.csv.gz')
        pending=q[~q.scoring_requirement_discharged]
        findings=json.loads((P/'findings.json').read_text())
        self.assertEqual(len(pending),880709)
        self.assertEqual(q.raw_stat_still_unresolved.sum(),881632)
        self.assertEqual(len(pending[KEY].drop_duplicates()),77280)
        self.assertEqual(findings['remaining_unique_player_matches'],77280)
        fields=pd.read_csv(P/'field_summary.csv')
        self.assertEqual(fields.remaining_scoring_cells.sum(),len(pending))
        self.assertEqual(fields[['missing_data','source_conflict','rule_unresolved']].sum().sum(),len(pending))

    def test_minute_count_stays_unknown(self):
        m=pd.read_csv(P/'minute_component_supplement.csv')
        self.assertTrue(m.exact_minutes.isna().all())
        self.assertTrue(m.raw_stat_still_unresolved.all())
        self.assertEqual(m.iloc[0].base_minute_points,1)
        self.assertEqual(m.iloc[0].bps_minute_points,3)


if __name__=='__main__':
    unittest.main()
