import unittest
import numpy as np
import pandas as pd
from model_lab.simulation import backend
from model_lab import joint_planning as p


class ExplicitPlanningChecks(unittest.TestCase):
    def fixture(self, gw, doubled=False):
        _, a = backend(16, 40)
        positions = ([1]*2+[2]*5+[3]*5+[4]*3)*(2 if doubled else 1)
        pool = pd.DataFrame({'pid': np.arange(1, len(positions)+1), 'pos': positions,
            'club': [str(i % 5) for i in range(len(positions))], 'market': 50, 'can_buy': True})
        s = a.engine.initial_state(start_gw=gw, bank=250)
        s['owned'] = {i: 50 for i in range(1, 16)}
        s['ownership_clubs'] = dict(zip(pool.pid[:15], pool.club[:15]))
        return a, pool, s

    def test_waiting_is_chosen_from_future_points_without_a_reserve(self):
        a, pool, s = self.fixture(17)
        s['used_chips']['1'] = ['wildcard', 'free_hit', 'bench_boost']
        xp = np.full((15, 2), 2.); xp[8] = [5., 20.]
        options = p.plans(a, pool, xp, s, 17)
        j, _ = p.select(options)
        self.assertEqual(options[j]['schedule'], [None, 'triple_captain'])

    def test_positive_expiring_chip_beats_identical_no_chip_plan(self):
        a, pool, s = self.fixture(38)
        s['used_chips']['2'] = ['wildcard', 'free_hit', 'triple_captain']
        options = p.plans(a, pool, np.full((15, 1), 2.), s, 38)
        j, scores = p.select(options)
        self.assertEqual(options[j]['schedule'], ['bench_boost'])
        self.assertAlmostEqual(max(scores)-min(scores), 8.)

    def test_inventory_expires_resets_and_blocks_consecutive_free_hits(self):
        a, _, s = self.fixture(19)
        seq = p.schedules(a.engine, s, 19, 2)
        self.assertIn(['bench_boost', 'bench_boost'], seq)
        self.assertNotIn(['free_hit', 'free_hit'], seq)
        self.assertNotIn(['bench_boost', 'bench_boost'], p.schedules(a.engine, s, 18, 2))

    def test_opening_squad_is_not_charged_fifteen_transfers(self):
        a, pool, _ = self.fixture(1)
        state = a.engine.initial_state()
        option = p.evaluate(a, pool, np.full((15, 2), 2.), state, 1, [None, None])
        first = option['steps'][0]
        self.assertEqual(first['choice']['transfers'], 0)
        self.assertEqual(first['choice']['paid'], 0)
        self.assertEqual(first['state_after']['ft'], 1)
        self.assertAlmostEqual(option['expected_net_points'], 48.)

    def test_free_hit_continuation_uses_restored_team_and_cash(self):
        a, pool, s = self.fixture(17, doubled=True)
        xp = np.full((30, 2), 2.); xp[15:, 0] = 10.; xp[:15, 1] = 10.
        option = p.evaluate(a, pool, xp, s, 17, ['free_hit', None])
        first, second = option['steps']
        self.assertNotEqual(set(first['choice']['squad']), set(s['owned']))
        self.assertEqual(first['state_after']['owned'], s['owned'])
        self.assertEqual(second['state_before']['bank'], s['bank'])
        self.assertEqual(second['state_before']['owned'], s['owned'])

    def test_candidate_never_calls_the_reserve_function(self):
        a, pool, s = self.fixture(38)
        def forbidden(*args): raise AssertionError('Reserve called by pure planning')
        a.policy.reserve_value = forbidden
        options = p.plans(a, pool, np.full((15, 1), 2.), s, 38)
        j, scores = p.select(options)
        self.assertEqual(scores[j], options[j]['expected_net_points'])


if __name__ == '__main__': unittest.main()
