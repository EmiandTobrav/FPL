"""Meaningful rejection and preservation checks using archived primary lineups."""
from pathlib import Path
import json
import tarfile
import copy
import importlib.util
import unittest

import pandas as pd

from predict import P, classify_lineup
from apply import qualified_view, require_qualified

spec = importlib.util.spec_from_file_location('primary_reference_build', P / 'primary_reference/build.py')
primary = importlib.util.module_from_spec(spec)
import sys
sys.path.insert(0, str(P / 'primary_reference'))
spec.loader.exec_module(primary)


class PrimaryLineupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = next(pd.read_csv(P / 'primary_reference/fixture_plan.csv').itertuples())
        with tarfile.open(P / 'primary_reference/raw_inputs.tar.gz') as archive:
            cls.data = json.loads(archive.extractfile(f'raw/fixture_{cls.row.pulse_id}.json').read())

    def test_full_official_lineup_has_twenty_two_starters(self):
        rows = primary.extract_lineup(self.data, self.row, 'source')
        self.assertEqual(sum(x['reference_starts'] for x in rows), 22)
        self.assertTrue(any(x['reference_starts'] == 0 for x in rows))

    def test_duplicate_club_side_blocks_reference(self):
        data = copy.deepcopy(self.data)
        data['teamLists'][1]['teamId'] = data['teamLists'][0]['teamId']
        with self.assertRaisesRegex(ValueError, 'unique primary sides'):
            primary.extract_lineup(data, self.row, 'source')

    def test_same_player_in_both_squads_blocks_reference(self):
        data = copy.deepcopy(self.data)
        data['teamLists'][1]['lineup'][0] = data['teamLists'][0]['lineup'][0]
        with self.assertRaisesRegex(ValueError, 'Duplicate primary player'):
            primary.extract_lineup(data, self.row, 'source')

    def test_missing_starter_blocks_reference(self):
        data = copy.deepcopy(self.data)
        data['teamLists'][0]['lineup'].pop()
        with self.assertRaisesRegex(ValueError, 'eleven starters'):
            primary.extract_lineup(data, self.row, 'source')

    def test_wrong_fixture_score_blocks_reference(self):
        data = copy.deepcopy(self.data)
        data['teams'][0]['score'] += 1
        with self.assertRaisesRegex(ValueError, 'score mismatch'):
            primary.extract_lineup(data, self.row, 'source')

    def test_missing_stable_code_blocks_reference(self):
        data = copy.deepcopy(self.data)
        data['teamLists'][0]['lineup'][0]['altIds']['opta'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'stable primary code'):
            primary.extract_lineup(data, self.row, 'source')


class QualifiedViewTests(unittest.TestCase):
    def test_structural_zero_needs_direct_evidence_and_native_values_remain(self):
        original = pd.DataFrame([
            dict(season='2022-23', fixture=1, code=1, fixture_event=1, minutes=90, starts=0),
            dict(season='2022-23', fixture=1, code=2, fixture_event=1, minutes=0, starts=0),
            dict(season='2023-24', fixture=1, code=1, fixture_event=1, minutes=90, starts=1),
            dict(season='2019-20', fixture=1, code=1, fixture_event=1, minutes=90, starts=None)])
        predictions = original[['season', 'fixture', 'code']].copy()
        predictions['predicted_starts'] = [1, None, 0, 1]
        for name in ['status', 'match_id', 'player_id', 'primary_source_file', 'primary_source_sha256']:
            predictions[name] = 'test'
        reference = pd.DataFrame([dict(season='2022-23', fixture=1, code=1,
            reference_starts=1, source_file='primary', source_sha256='sha')])
        view = qualified_view(original, predictions, reference)
        self.assertEqual(view.starts_original.tolist()[:3], [0, 0, 1])
        self.assertEqual(view.starts_qualified.iloc[0], 1)
        self.assertTrue(pd.isna(view.starts_qualified.iloc[1]))
        self.assertEqual(view.starts_qualified.iloc[2], 1)
        self.assertEqual(view.starts_qualified.iloc[3], 1)

    def test_failed_primary_control_gate_blocks_application(self):
        qualification = json.loads((P / 'primary_reference/validation_summary.json').read_text())
        self.assertFalse(qualification['qualified'])
        with self.assertRaisesRegex(ValueError, 'qualification not passed'):
            require_qualified({'qualified': False, 'prediction_sha256': 'sha'}, 'sha')

    def test_qualification_of_another_prediction_cannot_be_applied(self):
        with self.assertRaisesRegex(ValueError, 'qualification not passed'):
            require_qualified({'qualified': True, 'prediction_sha256': 'old'}, 'new')

    def test_default_provider_starter_and_minutes_are_not_authority(self):
        rows = []
        for side in ['home', 'away']:
            for slot in range(1, 12):
                rows.append(dict(match_id='m', team_position=side, team_name=side,
                    player_id=f'{side}{slot}', formation_place=str(slot), position='Defender',
                    is_starter=False, minutes_played=0))
            rows.append(dict(match_id='m', team_position=side, team_name=side,
                player_id=f'{side}sub', formation_place='', position='Substitute',
                is_starter=True, minutes_played=90))
        result = classify_lineup(pd.DataFrame(rows))
        self.assertEqual(result.predicted_starts.sum(), 22)
        self.assertTrue(result[result.position.eq('Substitute')].predicted_starts.eq(0).all())

    def test_repeated_starting_slot_rejects_entire_fixture(self):
        data = pd.read_csv(P / 'opta_lineups.csv.xz', keep_default_na=False)
        data = data[data.match_id.eq(data.match_id.iloc[0])].copy()
        slots = data.index[pd.to_numeric(data.formation_place, errors='coerce').between(1, 11)]
        data.loc[slots[1], 'formation_place'] = data.loc[slots[0], 'formation_place']
        result = classify_lineup(data)
        self.assertTrue(result.predicted_starts.isna().all())


if __name__ == '__main__':
    unittest.main()
