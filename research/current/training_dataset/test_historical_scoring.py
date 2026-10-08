"""Boundary and refusal tests for the historical scoring transformation."""
import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

import pandas as pd

from scoring.core import (EventBundle, MissingInput, basic_changes,
                          basic_component_account, bonus_for_complete_fixture,
                          bps_candidate, bps_changes, total_candidate)
from scoring import historical


def original(season='2023-24', position='MID', **updates):
    row = dict(season=season, position=position, minutes=90, goals_scored=0,
               assists=0, own_goals=0, clean_sheets=0, goals_conceded=0,
               saves=0, penalties_saved=0, penalties_missed=0, yellow_cards=0,
               red_cards=0, bps=20, bonus=2, total_points=4)
    return {**row, **updates}


def target(**updates):
    return dict(clearances_blocks_interceptions=0, times_tackled=0,
                assists_2026_27=0, legacy_net_tackles=0, won_tackles=0,
                goal_line_clearances=0, penalty_goals=0, fouls_won=0,
                shots_on_target=0, saves_inside_box=0, big_chance_saves=0,
                saves_outside_box=0, **updates)


class HistoricalScoringTests(unittest.TestCase):
    def test_bps_cbi_thresholds_and_assist_replacement(self):
        row = original(assists=1)
        values = target()
        values.update(clearances_blocks_interceptions=5, times_tackled=2,
                      assists_2026_27=2)
        value, terms = bps_candidate(row, values, 'clipped')
        self.assertEqual(terms['cbi'], -1)
        self.assertEqual(terms['assists'], 9)
        self.assertEqual(value, 30)
        self.assertEqual(row['bps'], 20)

    def test_negative_legacy_counter_keeps_two_hypotheses(self):
        values = target(); values.update(legacy_net_tackles=-2, won_tackles=1)
        self.assertEqual(bps_changes(original(), values, 'clipped')['tackles'], 2)
        self.assertEqual(bps_changes(original(), values, 'signed')['tackles'], 6)
        self.assertEqual(values['legacy_net_tackles'], -2)
        with self.assertRaisesRegex(ValueError, 'explicit'):
            bps_changes(original(), values, 'automatic')

    def test_season_specific_goal_line_penalty_and_conceded_terms(self):
        values = target(); values.update(goal_line_clearances=1, penalty_goals=1,
                                         fouls_won=2, shots_on_target=3)
        old = bps_changes(original(position='DEF', goals_conceded=2), values, 'clipped')
        self.assertEqual(old['goal_line_clearances'], 9)
        self.assertEqual(old['goals_conceded'], -8)
        self.assertEqual(old['fouls_won'] + old['shots_on_target'], 8)
        for pos, penalty_delta in [('MID', -6), ('FWD', -12)]:
            terms = bps_changes(original('2024-25', pos, goals_scored=1), values, 'clipped')
            self.assertEqual(terms['goal_line_clearances'], 6)
            self.assertEqual(terms['penalty_goals'], penalty_delta)
            self.assertNotIn('shots_on_target', terms)
        terms = bps_changes(original('2025-26'), values, 'clipped')
        self.assertNotIn('tackles', terms)
        self.assertNotIn('penalty_goals', terms)
        self.assertNotIn('goal_line_clearances', terms)

    def test_keeper_redemption_does_not_assume_save_partition(self):
        # FPL S=7, source I+O=5: never substitute the source partition for S.
        values = target(); values.update(saves_inside_box=3, saves_outside_box=2,
                                         big_chance_saves=2)
        for season, expected in [('2023-24', -3), ('2024-25', 3), ('2025-26', 5)]:
            terms = bps_changes(original(season, 'GK', saves=7, penalties_saved=1), values, 'clipped')
            self.assertEqual(terms['keeper_saves'], expected)

    def test_missing_changed_component_is_not_zero(self):
        values = target(); values.pop('times_tackled')
        with self.assertRaisesRegex(MissingInput, 'times_tackled'):
            bps_candidate(original(), values, 'clipped')
        values['times_tackled'] = float('nan')
        with self.assertRaises(MissingInput):
            bps_candidate(original(), values, 'clipped')
        values['times_tackled'] = -1
        with self.assertRaises(ValueError):
            bps_candidate(original(), values, 'clipped')
        with self.assertRaisesRegex(ValueError, 'preserved directly'):
            bps_candidate(original('2026-27'), target(), 'clipped')

    def test_total_replaces_bonus_and_avoids_double_defcon(self):
        row = original(total_points=4, bonus=2)
        values = target(); values['assists_2026_27'] = 1
        self.assertEqual(total_candidate(row, values, 0, 2)[0], 7)
        self.assertEqual(total_candidate(original('2025-26', total_points=6, bonus=2),
                                         values, 0, 2)[0], 7)
        self.assertEqual(basic_changes(original('2023-24', 'GK', goals_scored=1), values, 0)['keeper_goal_value'], 4)
        self.assertNotIn('keeper_goal_value', basic_changes(original('2024-25', 'GK', goals_scored=1), values, 0))
        with self.assertRaisesRegex(ValueError, 'ineligible'):
            basic_changes(original(position='GK'), values, 2)

    def test_complete_event_bundle_required(self):
        row = original(own_goals=1)
        bundle = EventBundle(1, -1, 20, 'approved_coherent_event', True)
        self.assertEqual(bps_candidate(row, target(), 'clipped', bundle)[0], 40)
        self.assertEqual(total_candidate(row, target(), 0, 0, bundle)[0], 9)
        with self.assertRaisesRegex(ValueError, 'Unqualified'):
            bps_candidate(row, target(), 'clipped', EventBundle(1, -1, 20, '', True))
        with self.assertRaisesRegex(ValueError, 'negative'):
            total_candidate(original(), target(), 0, 0, bundle)

    def test_whole_match_bonus_inventory_and_ties(self):
        scores = {i: -10 for i in range(22)}
        scores.update({0: 0, 1: 0, 2: -1})
        award = bonus_for_complete_fixture(scores, list(scores))
        self.assertEqual([award[i] for i in range(4)], [3, 3, 1, 0])
        scores.update({0: 5, 1: 2, 2: 2, 3: 1})
        award = bonus_for_complete_fixture(scores, list(scores))
        self.assertEqual([award[i] for i in range(4)], [3, 2, 2, 0])
        with self.assertRaisesRegex(ValueError, 'inventory'):
            bonus_for_complete_fixture(scores, list(scores) + [0])
        with self.assertRaisesRegex(ValueError, 'inventory'):
            bonus_for_complete_fixture(scores, list(scores) + [22])
        scores[4] = None
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            bonus_for_complete_fixture(scores, list(scores))

    def test_original_account_handles_zero_minutes_cards_and_keeper(self):
        self.assertEqual(sum(basic_component_account(original(minutes=0, red_cards=1, yellow_cards=1), None).values()), -4)
        row = original('2023-24', 'GK', minutes=59, saves=8, goals_conceded=3,
                       clean_sheets=0, penalties_saved=1)
        self.assertEqual(sum(basic_component_account(row, None).values()), 7)
        with self.assertRaisesRegex(ValueError, 'award'):
            basic_component_account(original('2025-26'), None)

    def test_duplicate_snapshot_requires_unique_official_match(self):
        gw = pd.DataFrame([dict(element=1, fixture=1, GW=2, kickoff_time='2020-01-01T15:00:00Z', minutes=0),
                           dict(element=1, fixture=1, GW=3, kickoff_time='2020-01-08T15:00:00Z', minutes=90)])
        fixtures = pd.DataFrame([dict(id=1, event=3, kickoff_time='2020-01-08T15:00:00Z')]).set_index('id')
        kept, logs = historical.resolve_duplicates(gw, fixtures, '2019-20')
        self.assertEqual(kept.minutes.tolist(), [90])
        self.assertEqual(logs[0]['discarded'], 1)
        gw.loc[0, ['GW', 'kickoff_time']] = [3, '2020-01-08T15:00:00Z']
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            historical.resolve_duplicates(gw, fixtures, '2019-20')

    def test_changed_ledger_fingerprint_stops_before_calculation(self):
        real = historical.digest
        def corrupt(path):
            return 'wrong' if path.name == 'requirements.csv.xz' else real(path)
        with tempfile.TemporaryDirectory() as tmp, patch.object(historical, 'digest', side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, 'fingerprint differs'):
                historical.build(Path(tmp))
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_changed_defcon_partition_is_rejected(self):
        real = historical.digest
        def corrupt(path):
            return 'wrong' if path.name == 'part-000.csv' else real(path)
        with patch.object(historical, 'digest', side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, 'partition changed'):
                historical.load_defcon({})

    def test_generated_candidates_cannot_be_consumed_as_training_labels(self):
        root = historical.P / 'results'
        rows = pd.read_csv(root / 'player_match_candidates.csv.xz')
        self.assertFalse(rows.scoring_qualified.any())
        self.assertFalse(rows.training_ready.any())
        for field in ['assists_2026_27', 'bps_2026_27', 'bonus_2026_27', 'total_points_2026_27']:
            self.assertTrue(rows[field].isna().all(), field)
        fixtures = pd.read_csv(root / 'fixture_status.csv')
        computed = fixtures[fixtures.whole_match_candidates_computed]
        self.assertGreater(len(computed), 0)
        complete = rows.merge(computed[['season', 'fixture']], on=['season', 'fixture'], validate='many_to_one')
        for mode in ['clipped', 'signed']:
            self.assertTrue(complete[[f'bps_candidate_{mode}', f'bonus_candidate_{mode}',
                                      f'total_points_candidate_{mode}']].notna().all().all())
        blocked = rows[rows.revision_bundle_blocked]
        self.assertTrue(blocked.bps_candidate_clipped.isna().all())

    def test_full_inventory_keeps_zero_minute_cards_and_points(self):
        root = historical.P / 'results'
        rows = pd.read_csv(root / 'historical_inventory.csv.xz')
        gaps = pd.read_csv(root / 'source_population_gaps.csv')
        self.assertEqual(len(gaps), 12)
        joined = gaps[historical.K].merge(rows, on=historical.K, validate='one_to_one')
        self.assertTrue(joined.minutes.eq(0).all())
        self.assertTrue((joined.yellow_cards + joined.red_cards).gt(0).all())
        self.assertTrue(joined.total_points.lt(0).all())
        self.assertTrue(rows.original_point_residual.eq(0).all())


if __name__ == '__main__':
    unittest.main()
