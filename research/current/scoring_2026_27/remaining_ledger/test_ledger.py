import hashlib
import json
import unittest

import pandas as pd

from build import KEY, P, R, S, SPECS, classify, unique


class TransformationTests(unittest.TestCase):
    def test_omission_is_not_zero(self):
        values, status, conflict = classify(pd.DataFrame({'a':[None,0,2], 'b':[None,None,2]}))
        self.assertTrue(pd.isna(values.iloc[0]))
        self.assertEqual(status.tolist(), ['missing_data','documented_zero','documented_value'])
        self.assertFalse(conflict.any())

    def test_conflict_not_resolved_by_priority(self):
        evidence = pd.DataFrame({'a':[0,1], 'b':[1,0]})
        values, status, _ = classify(evidence)
        self.assertTrue(values.isna().all())
        self.assertTrue(status.eq('source_conflict').all())
        self.assertTrue(classify(evidence[['b','a']])[0].equals(values))

    def test_approved_keeper_beats_conflicting_candidate(self):
        value, status, conflict = classify(pd.DataFrame({'candidate':[0], 'primary':[1]}), pd.Series([1.]))
        self.assertEqual(value.iloc[0], 1)
        self.assertEqual(status.iloc[0], 'documented_value')
        self.assertTrue(conflict.iloc[0])

    def test_duplicate_key_rejected(self):
        with self.assertRaises(ValueError):
            unique(pd.DataFrame([['2020-21',1,2],['2020-21',1,2]],columns=KEY))

    def test_missing_identity_rejected(self):
        with self.assertRaises(ValueError):
            unique(pd.DataFrame([['2020-21',1,None]],columns=KEY))

    def test_wrong_metric_not_used_as_substitute(self):
        specs = {x[0]:x for x in SPECS}
        self.assertIsNone(specs['won_tackles'][2])
        self.assertIsNone(specs['noncorner_crosses'][2])
        self.assertEqual(specs['total_tackles'][2], 'matchstats.headers.tackles')


class OutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = pd.read_csv(P/'player_matches.csv.gz', low_memory=False)
        cls.findings = json.loads((P/'findings.json').read_text())
        cls.fields = pd.read_csv(P/'field_summary.csv').set_index('field')

    def test_union_not_category_sum(self):
        flags = self.meta[['missing_data','source_conflict','rule_unresolved']]
        self.assertEqual(int(flags.any(axis=1).sum()), self.findings['affected_unique_player_matches'])
        self.assertEqual(int(self.meta.unresolved_fields.sum()), self.findings['unresolved_field_cells'])
        self.assertGreater(int(flags.sum().sum()), int(flags.any(axis=1).sum()))
        self.assertFalse(self.meta.duplicated(KEY).any())

    def test_source_and_event_gaps_separate(self):
        self.assertEqual(self.findings['missing_archive_player_matches'], 593)
        self.assertEqual(self.findings['missing_archive_matches'], 21)
        self.assertEqual(self.findings['additional_event_gap_matches'], 3)
        self.assertEqual(self.findings['additional_event_gap_goals'], 9)
        self.assertFalse((self.meta.missing_archive_match & self.meta.additional_event_gap).any())

    def test_keeper_population_and_approved_values(self):
        keeper = pd.read_csv(S/'keeper_recovery/keeper_counts.csv.gz').set_index(KEY)
        keeper = keeper.loc[keeper.index.get_level_values('season') != '2026-27']
        chunks = pd.read_csv(P/'field_ledger.csv.gz',chunksize=100000, usecols=KEY+['field','value'])
        actual = pd.concat([c[c.field.eq('big_chance_saves')] for c in chunks]).set_index(KEY)
        pd.testing.assert_series_equal(actual.value.sort_index(),keeper.big_chance_saves.sort_index(),check_names=False)
        self.assertEqual(int(actual.value.notna().sum()),5343)
        self.assertEqual(int(actual.value.isna().sum()),38)

    def test_assist_zero_bound_not_historical_zero(self):
        self.assertEqual(int(self.fields.loc['assists_2026_27','documented_zero']), int(self.meta.own_team_goals.eq(0).sum()))
        self.assertEqual(int(self.fields.loc['assists_2026_27','rule_unresolved']), int(self.meta.own_team_goals.ne(0).sum()))
        self.assertTrue((self.meta.own_team_goals.gt(0)&self.meta.historical_fpl_assists.eq(0)&self.meta.rule_unresolved).any())
        self.assertEqual(int(self.meta.has_official_assist_addition.sum()),4)
        self.assertTrue(self.meta.loc[self.meta.has_official_assist_addition,'rule_unresolved'].all())

    def test_field_statuses_partition_requirements(self):
        f = self.fields
        self.assertTrue(f[['documented_value','documented_zero','missing_data','source_conflict','rule_unresolved']].sum(axis=1).eq(f.applicable).all())
        self.assertEqual(int(f.loc[f.required_for_scoring,'applicable'].sum()),self.findings['required_field_cells'])

    def test_cbi_components_not_counted_twice(self):
        parts = self.fields.loc[['clearances','shot_blocks','interceptions']]
        self.assertFalse(parts.required_for_scoring.any())
        self.assertTrue(parts.unresolved_cells.eq(0).all())
        self.assertTrue(self.fields.loc['clearances_blocks_interceptions','required_for_scoring'])

    def test_inputs_and_outputs_match_manifest(self):
        manifest = json.loads((P/'manifest.json').read_text())
        for name,digest in manifest['inputs_sha256'].items():
            self.assertEqual(hashlib.sha256((R/name).read_bytes()).hexdigest(),digest,name)
        for name,digest in manifest['outputs_sha256'].items():
            self.assertEqual(hashlib.sha256((P/name).read_bytes()).hexdigest(),digest,name)
        for name,digest in manifest['code_sha256'].items():
            self.assertEqual(hashlib.sha256((P/name).read_bytes()).hexdigest(),digest,name)


if __name__ == '__main__':
    unittest.main()
