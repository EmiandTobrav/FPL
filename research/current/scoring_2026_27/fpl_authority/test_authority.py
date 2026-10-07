import hashlib
import json
import unittest
import pandas as pd
from build import P,S,R,KEY,SOURCES,FPL_FIELDS,OPEN,choose,required_fields,fpl_rows


class PriorityTests(unittest.TestCase):
    def test_fpl_values_and_zeros_override_provider_majority(self):
        e=pd.DataFrame({'fpl':[60,0,None,None,None], 'archive':[61,1,2,2,None], 'primary':[61,1,2,3,None]})
        value,status,_,disagree=choose(e)
        self.assertEqual(value[:3].tolist(),[60,0,2])
        self.assertEqual(status.tolist(),['fpl_authoritative','fpl_authoritative','external_available','external_conflict','missing_data'])
        self.assertTrue(value[3:].isna().all())
        self.assertTrue(disagree[:2].all())

    def test_approved_evidence_is_used_only_without_fpl(self):
        e=pd.DataFrame({'fpl':[None,0], 'archive':[1,2], 'primary':[2,2]})
        v,s,_,_=choose(e,pd.Series([3,3]))
        self.assertEqual(v.tolist(),[3,0])
        self.assertEqual(s.tolist(),['approved_reconstruction','fpl_authoritative'])

    def test_unchanged_components_not_reconstructed(self):
        for season in ['2019-20','2024-25','2025-26']:
            for position in ['GK','DEF','MID','FWD']:
                fields=required_fields(season,position,1)
                self.assertTrue({'minutes','accurate_passes','winning_goal','yellow_cards'}.isdisjoint(fields))
                self.assertTrue({'historical_bps','times_tackled','clearances_blocks_interceptions'}<=fields)

    def test_season_specific_dependencies(self):
        old=required_fields('2023-24','MID',1)
        mid=required_fields('2024-25','MID',1)
        new=required_fields('2025-26','MID',1)
        self.assertTrue({'shots_on_target','fouls_won','legacy_net_tackles','penalty_goals','recoveries'}<=old)
        self.assertNotIn('shots_on_target',mid)
        self.assertNotIn('legacy_net_tackles',new)
        self.assertIn('defensive_contribution',new)
        self.assertNotIn('penalty_goals',required_fields('2022-23','MID',0))
        self.assertNotIn('saves_outside_box',required_fields('2024-25','GK',0))
        self.assertIn('saves_outside_box',required_fields('2025-26','GK',0))


class LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.req=pd.read_csv(P/'requirements.csv.gz',low_memory=False)
        cls.authority=pd.read_csv(P/'authoritative_values.csv.gz',low_memory=False)
        cls.meta=pd.read_csv(S/'remaining_ledger/player_matches.csv.gz',low_memory=False).set_index(KEY)
        cls.baseline=pd.read_csv(P/'fpl_baseline.csv.gz').set_index(KEY)
        cls.findings=json.loads((P/'findings.json').read_text())

    def test_baseline_exactly_matches_raw_fpl(self):
        raw=fpl_rows(self.meta)
        for col in dict.fromkeys(FPL_FIELDS.values()):
            pd.testing.assert_series_equal(self.baseline[col],raw[col],check_dtype=False)

    def test_every_compatible_fpl_cell_preserved_except_explicit_goal_appeals(self):
        a=self.authority
        present=a[a.fpl.notna()]
        revisions=present[present.status.eq('official_revision')]
        self.assertEqual(len(revisions),8)
        normal=present[~present.status.eq('official_revision')]
        self.assertTrue(normal.status.eq('fpl_authoritative').all())
        self.assertTrue(normal.value.eq(normal.fpl).all())
        patches=pd.read_csv(S/'official_revision/counter_supplement.csv')
        check=revisions.merge(patches,on=KEY+['field'],validate='one_to_one')
        self.assertTrue(check.value.eq(check.revised_value).all())

    def test_minutes_are_authoritative_and_not_open_work(self):
        minutes=self.authority[self.authority.field.eq('minutes')]
        self.assertEqual(len(minutes),77280)
        self.assertTrue(minutes.value.eq(minutes.fpl).all())
        self.assertFalse(self.req.field.eq('minutes').any())

    def test_keeper_approvals_and_unknowns_unchanged(self):
        actual=self.req[self.req.field.eq('big_chance_saves')].set_index(KEY)
        prior=pd.read_csv(S/'keeper_recovery/keeper_counts.csv.gz').set_index(KEY).reindex(actual.index)
        known=prior.status.eq('reconstructed')
        self.assertEqual(int(known.sum()),5343)
        self.assertTrue(actual.loc[known,'value'].eq(prior.loc[known,'big_chance_saves']).all())
        self.assertTrue(actual.loc[~known,'value'].isna().all())
        self.assertEqual(int((~known).sum()),38)
        self.assertTrue(actual.loc[~known,'is_open'].all())

    def test_latest_season_assists_reused_older_not_assumed(self):
        a=self.req[self.req.field.eq('assists_2026_27')].set_index(KEY)
        current=a.index.get_level_values('season')=='2025-26'
        self.assertTrue(a.loc[current,'status'].eq('fpl_authoritative').all())
        self.assertTrue(a.loc[current,'value'].eq(self.baseline.reindex(a.index[current]).assists).all())
        self.assertTrue(a.loc[~current,'status'].isin(['documented_zero','rule_recalculation']).all())

    def test_unique_keys_and_counts_are_not_field_sum(self):
        r=self.req
        self.assertFalse(r.duplicated(KEY+['field']).any())
        pending=r[r.is_open]
        self.assertEqual(len(pending),self.findings['open_cells'])
        self.assertEqual(len(pending[KEY].drop_duplicates()),self.findings['unique_affected_player_matches'])
        self.assertGreater(len(pending),len(pending[KEY].drop_duplicates()))
        summary=pd.read_csv(P/'field_summary.csv')
        self.assertEqual(int(summary.open_cells.sum()),len(pending))

    def test_external_quality_is_separate_and_union_deduplicated(self):
        r=self.req
        self.assertFalse((r.is_open&r.needs_external_quality_review).any())
        work=r[r.is_open|r.needs_external_quality_review]
        self.assertEqual(len(work[KEY].drop_duplicates()),self.findings['unique_open_or_external_quality_player_matches'])
        q=r[r.needs_external_quality_review]
        self.assertTrue(q.value.notna().all())
        self.assertEqual(len(q),self.findings['external_quality_review_cells'])

    def test_unknown_legacy_counter_not_proxy_imputed(self):
        legacy=self.req[self.req.field.eq('legacy_net_tackles')]
        self.assertTrue(legacy.value.isna().all())
        self.assertTrue(legacy.status.eq('missing_data').all())

    def test_ferguson_is_one_baseline_exception_without_minute_patch(self):
        exception=self.req[self.req.status.eq('fpl_extract_exception')]
        self.assertEqual(len(exception),1)
        row=exception.iloc[0]
        self.assertEqual((row.season,int(row.fixture),int(row.code),row.field),('2024-25',239,487117,'historical_bps'))
        self.assertEqual(self.baseline.loc[('2024-25',239,487117),'minutes'],0)

    def test_previous_queue_reclassification_balances(self):
        b=pd.read_csv(P/'reclassification_summary.csv').groupby('transition').cells.sum()
        self.assertEqual(int(b.still_open+b.no_longer_open_under_fpl_authority+b.removed_unchanged_component_or_outside_season_scope),880385)
        self.assertEqual(int(b.still_open+b.newly_identified_delta_requirement),self.findings['open_cells'])

    def test_event_review_preserved_without_extra_missing_cells(self):
        event=pd.read_csv(P/'official_event_review.csv')
        self.assertEqual(len(event),12)
        self.assertFalse(event.additional_missing_cell.any())
        self.assertEqual(len(event[['season','fixture']].drop_duplicates()),4)

    def test_manifest_inputs_intact_and_no_target_labels_claimed(self):
        for path,digest in json.loads((P/'manifest.json').read_text())['inputs'].items():
            self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),digest,path)
        self.assertFalse(self.findings['delta_engine_qualified'])
        self.assertEqual(self.findings['full_target_labels_produced'],0)


if __name__=='__main__':unittest.main()
