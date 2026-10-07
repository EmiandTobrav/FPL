import hashlib
import json
import unittest
import pandas as pd
from build import KEY,P,S,minute_candidate,remaining_component_isolated,review_exception


class HypothesisTests(unittest.TestCase):
    def test_boundary_hypotheses_are_distinct(self):
        methods=['fpl_strict','primary_strict','fpl_inclusive']
        self.assertEqual([minute_candidate(60,61,m) for m in methods],[3,6,6])
        self.assertEqual([minute_candidate(60,60,m) for m in methods],[3,3,6])
        self.assertEqual([minute_candidate(59,61,m) for m in methods],[3,6,3])

    def test_missing_minutes_not_zero(self):
        with self.assertRaises(ValueError):minute_candidate(float('nan'),61,'fpl_strict')

    def test_missing_nonminute_fields_prevent_isolation(self):
        row=pd.Series(dict(position='MID',pl_total_pass=18))
        self.assertFalse(remaining_component_isolated(row))

    def test_diagnostic_fit_cannot_close_rule_gate(self):
        f=json.loads((P/'findings.json').read_text())
        self.assertFalse(f['rule_qualified'])
        self.assertEqual(f['strictly_isolated_discriminating_cases'],0)
        self.assertEqual(f['candidate_exact_fits'],dict(fpl_strict=620,primary_strict=621,fpl_inclusive=621))
        self.assertTrue(f['existing_development_not_holdout'])


class ExceptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events=pd.read_csv(S/'minute_reconciliation/inputs/clock_events.csv.gz')
        cls.targets=pd.read_csv(S/'minute_reconciliation/inputs/targets.csv').set_index(KEY)
        cls.cases=json.loads((P/'reviewed_cases.json').read_text())

    def case(self,mode):
        c=next(c for c in self.cases if c['mode']==mode)
        t=self.targets.loc[tuple(c[k] for k in KEY)]
        return t,self.events[self.events.match_id.eq(t.match_id)].copy()

    def test_one_second_pair_has_same_scoring_band(self):
        t,e=self.case('one_second_pair');r=review_exception(t,e,59,'one_second_pair',0)
        self.assertEqual(r['partner_seconds_delta'],1)
        self.assertEqual((r['base_minute_points'],r['bps_minute_points']),(1,3))

    def test_one_second_interval_crossing_threshold_is_rejected(self):
        t,e=self.case('one_second_pair')
        off=e[e.player_id.eq(t.player_id)&e.type_id.eq(18)].iloc[0]
        partner=e.team_id.eq(t.team_id)&e.type_id.eq(19)&e.minute.eq(off.minute)&e.second.eq(off.second+1)
        e.loc[partner,['minute','second']]=[60,0]
        e.loc[e.event_id.eq(off.event_id),['minute','second']]=[59,59]
        with self.assertRaises(ValueError):review_exception(t,e,59,'one_second_pair',0)

    def test_duplicate_partner_is_not_guessed(self):
        t,e=self.case('one_second_pair')
        off=e[e.player_id.eq(t.player_id)&e.type_id.eq(18)].iloc[0]
        partner=e[e.team_id.eq(t.team_id)&e.type_id.eq(19)&e.minute.eq(off.minute)&e.second.eq(off.second+1)].iloc[0].copy()
        partner.event_id=-1
        e=pd.concat([e,pd.DataFrame([partner])],ignore_index=True)
        with self.assertRaises(ValueError):review_exception(t,e,59,'one_second_pair',0)

    def test_later_video_gap_does_not_change_prior_exit(self):
        t,e=self.case('later_video_gap');r=review_exception(t,e,59,'later_video_gap',0)
        self.assertEqual(r['elapsed_regulation_seconds'],3581)

    def test_gap_before_exit_blocks_proof(self):
        t,e=self.case('later_video_gap');e.loc[e.type_id.eq(79),'minute']=58
        with self.assertRaises(ValueError):review_exception(t,e,59,'later_video_gap',0)

    def test_early_end_is_not_a_video_gap(self):
        t,e=self.case('later_video_gap');e.loc[e.type_id.eq(79),'type_id']=76
        with self.assertRaises(ValueError):review_exception(t,e,59,'later_video_gap',0)

    def test_second_yellow_clock_and_fpl_red_corroborate(self):
        t,e=self.case('second_yellow');r=review_exception(t,e,59,'second_yellow',1)
        self.assertEqual(r['elapsed_regulation_seconds'],3599)
        self.assertEqual(r['bps_minute_points'],3)

    def test_red_card_proof_requires_fpl_corroboration(self):
        t,e=self.case('second_yellow')
        with self.assertRaises(ValueError):review_exception(t,e,59,'second_yellow',0)

    def test_second_yellow_requires_first_yellow(self):
        t,e=self.case('second_yellow')
        mask=e.player_id.eq(t.player_id)&e.type_id.eq(17)&e.period_id.eq(1)
        with self.assertRaises(ValueError):review_exception(t,e[~mask],59,'second_yellow',1)


class OutputTests(unittest.TestCase):
    def test_hashes(self):
        for path,sha in json.loads((P/'manifest.json').read_text())['inputs'].items():
            self.assertEqual(hashlib.sha256((S.parent/path).read_bytes()).hexdigest(),sha,path)

    def test_four_exact_component_supplements(self):
        p=pd.read_csv(P/'minute_component_supplement.csv')
        self.assertEqual(len(p),4);self.assertFalse(p.duplicated(KEY).any())
        self.assertTrue(p.base_minute_points.eq(1).all());self.assertTrue(p.bps_minute_points.eq(3).all())

    def test_queue_conservation_and_unique_counts(self):
        old=pd.read_csv(S/'minute_reconciliation/resolution_queue.csv.gz')
        new=pd.read_csv(P/'resolution_queue.csv.gz')
        self.assertEqual(len(new),len(old))
        self.assertEqual(new.scoring_requirement_discharged.sum()-old.scoring_requirement_discharged.sum(),4)
        self.assertTrue(new.raw_stat_still_unresolved.equals(old.raw_stat_still_unresolved))
        pending=new[~new.scoring_requirement_discharged]
        self.assertEqual(len(pending),880385)
        self.assertEqual(len(pending[KEY].drop_duplicates()),77280)
        self.assertEqual(new[new.field.eq('minutes')].status.eq('rule_unresolved').sum(),364)
        pd.testing.assert_frame_equal(old[old.field.ne('minutes')],new[new.field.ne('minutes')])
        fields=pd.read_csv(P/'field_summary.csv')
        self.assertEqual(fields.remaining_scoring_cells.sum(),len(pending))
        self.assertEqual(fields[['missing_data','source_conflict','rule_unresolved']].sum().sum(),len(pending))


if __name__=='__main__':unittest.main()
