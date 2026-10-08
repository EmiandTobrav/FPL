"""Regression tests for provenance, scoped corrections and uncertainty guards."""
import copy
import json
import unittest

import numpy as np
import pandas as pd

from build import transform, verify_snapshot_objects, season_checks, K
from plan import P, FIELDS


def observations():
    original = pd.DataFrame([
        dict(season='2022-23', fixture=1, code=1, fixture_event=1,
             expected_goals=0., expected_assists=0., expected_goal_involvements=0.,
             expected_goals_conceded=0., minutes=90, total_points=6),
        dict(season='2022-23', fixture=2, code=1, fixture_event=16,
             expected_goals=.313, expected_assists=.2, expected_goal_involvements=.513,
             expected_goals_conceded=1.113, minutes=90, total_points=2),
        dict(season='2022-23', fixture=3, code=1, fixture_event=29,
             expected_goals=.21, expected_assists=.32, expected_goal_involvements=0.,
             expected_goals_conceded=.87, minutes=90, total_points=3),
        dict(season='2022-23', fixture=4, code=1, fixture_event=30,
             expected_goals=.30, expected_assists=.10, expected_goal_involvements=.40,
             expected_goals_conceded=.60, minutes=90, total_points=5),
    ])
    final = original[K + FIELDS].copy()
    final.loc[0, FIELDS] = [.15, .10, .25, .5]
    final.loc[1, FIELDS] = [.25, .18, .43, 1.05]
    final.loc[2, 'expected_goal_involvements'] = .53
    final.loc[3, 'expected_goals'] = .31
    final['source_file'], final['source_sha256'] = 'player.csv', 'a' * 64
    return original, final


class ReconciliationTests(unittest.TestCase):
    def test_backfill_keeps_original_zero_and_scoring_values(self):
        original, final = observations()
        view, _ = transform(original, final)
        self.assertEqual(view.loc[0, 'expected_goals_original'], 0.)
        self.assertEqual(view.loc[0, 'expected_goals_qualified'], .15)
        pd.testing.assert_frame_equal(view[['minutes','total_points']], original[['minutes','total_points']])
        self.assertFalse(view.historical_feature_availability_qualified.any())

    def test_snapshot_revision_is_explicit_and_raw_preserved(self):
        original, final = observations()
        view, _ = transform(original, final)
        self.assertEqual(view.loc[1, 'expected_goals_qualified'], .25)
        self.assertEqual(view.loc[1, 'expected_goals_original'], .313)
        self.assertEqual(view.loc[1, 'expected_goals_quality'], 'documented_later_fpl_snapshot_revision')

    def test_xgi_repair_uses_native_components_and_leaves_other_fields(self):
        original, final = observations()
        view, corrected = transform(original, final)
        self.assertEqual(corrected.tolist(), [False,False,True,False])
        self.assertEqual(view.loc[2, 'expected_goal_involvements_qualified'], .53)
        for field in ['expected_goals','expected_assists','expected_goals_conceded']:
            self.assertEqual(view.loc[2, field + '_qualified'], original.loc[2, field])

    def test_later_compatible_values_are_not_replaced_by_final_source(self):
        original, final = observations()
        view, _ = transform(original, final)
        self.assertEqual(view.loc[3, 'expected_goals_qualified'], .30)
        self.assertEqual(view.loc[3, 'expected_goals_final'], .31)

    def test_missing_backfill_is_not_zero(self):
        original, final = observations()
        final.loc[0, 'expected_goals'] = np.nan
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            transform(original, final)

    def test_invalid_backfill_is_rejected(self):
        for value in [-.01, np.inf]:
            with self.subTest(value=value):
                original, final = observations()
                final.loc[0, 'expected_goals'] = value
                with self.assertRaisesRegex(ValueError, 'nonfinite'):
                    transform(original, final)

    def test_missing_or_duplicate_source_observations_are_rejected(self):
        original, final = observations()
        for invalid in [final.iloc[:-1], pd.concat([final, final.iloc[:1]])]:
            with self.assertRaisesRegex(ValueError, 'identities'):
                transform(original, invalid)

    def test_other_seasons_are_not_subject_to_this_reconciliation(self):
        original, final = observations()
        original.loc[0, 'season'] = '2021-22'
        with self.assertRaisesRegex(ValueError, '2022/23'):
            transform(original, final)

    def test_season_aggregate_checks_actual_view_not_only_final_source(self):
        original, final = observations()
        view, _ = transform(original, final)
        register = pd.DataFrame([dict(code=1, **{
            field: float(view[field + '_qualified'].sum()) for field in FIELDS})])
        gates = dict(maximum_season_total_difference_per_summed_row=.00500001,
                     season_total_fixed_rounding_allowance=.01000001)
        self.assertTrue(season_checks(view, register, gates).passed.all())
        view.loc[0, 'expected_goals_qualified'] += .05
        self.assertFalse(season_checks(view, register, gates).passed.all())


class ProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((P.parent / 'source_plan.json').read_text())
        cls.manifest = json.loads((P.parent / 'raw_manifest.json').read_text())
        cls.directories = pd.read_csv(P / 'end_season_directory_trees.csv')
        cls.blobs = pd.read_csv(P / 'end_season_file_blobs.csv')

    def check(self, **replacements):
        inputs = dict(plan=self.plan, directories=self.directories, blobs=self.blobs,
                      manifest=self.manifest, archive_path=P.parent / 'raw_inputs.tar.gz')
        inputs.update(replacements)
        return verify_snapshot_objects(**inputs)

    def test_wrong_2023_blob_identity_rejects_authentic_but_different_version(self):
        blobs = self.blobs.copy()
        blobs.loc[0, 'git_blob_sha'] = '0' * 40
        with self.assertRaisesRegex(ValueError, '2023 Git object'):
            self.check(blobs=blobs)

    def test_later_modified_directory_is_rejected(self):
        directories = self.directories.copy()
        directories.loc[0, 'tree_sha'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'changed after season end'):
            self.check(directories=directories)

    def test_duplicate_inventory_is_rejected_even_if_dictionary_has_778_keys(self):
        duplicate = pd.concat([self.blobs, self.blobs.iloc[:1]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.check(blobs=duplicate)

    def test_missing_file_or_repeated_player_is_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest['entries'][0] = copy.deepcopy(manifest['entries'][1])
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.check(manifest=manifest)


if __name__ == '__main__':
    unittest.main()
