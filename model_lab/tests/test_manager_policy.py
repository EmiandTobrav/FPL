import copy
import importlib.util
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from model_lab import manager_policy as m

spec = importlib.util.spec_from_file_location('_episodic_rule_checks', Path(__file__).parents[1]/'vendor/fpl_rules_v1/engine.py')
rules = importlib.util.module_from_spec(spec); spec.loader.exec_module(rules)


class ManagerLearningChecks(unittest.TestCase):
    def fixture(self):
        positions = [1]*2+[2]*5+[3]*5+[4]*3
        pool = pd.DataFrame({'pid': list(range(1, 16)), 'pos': positions,
            'club': [str(i % 5) for i in range(15)], 'market': [50]*15, 'can_buy': [True]*15})
        xp = np.array([[float(i % 7 + 1)]*3 for i in range(15)])
        history = {i: dict(zip(m.HISTORY, [75., .9, 0.])) for i in pool.pid}
        return pool, xp, history

    def test_lineup_alternatives_are_legal_and_partition_squad(self):
        pool, xp, _ = self.fixture(); values = dict(zip(pool.pid, xp[:, 0]))
        for second in [False, True]:
            c = m.lineup(list(pool.pid), pool, values, second)
            self.assertTrue(rules.legal_positions(c['starters'], dict(zip(pool.pid, pool.pos))))
            self.assertEqual(set(c['starters']) | set(c['bench']), set(pool.pid))
            self.assertEqual(len(set(c['starters']) & set(c['bench'])), 0)
            self.assertNotEqual(c['captain'], c['vice'])

    def test_return_target_reaches_end_of_season(self):
        logs = [{'gw': gw, 'net_points': 1., 'forecast_at': '2022-08-01T00:00:00Z', 'episode': 'a',
            'selected': {'features': [0.]*len(m.FEATURES), 'base_score': 0., 'id': str(gw)}} for gw in range(1, 39)]
        rows = m.episode_samples(logs, '2022-23', '2023-06-01T00:00:00Z')
        self.assertEqual(rows[0]['return_to_go'], 38.)
        self.assertEqual(rows[-1]['return_to_go'], 1.)
        with self.assertRaises(ValueError): m.episode_samples(logs[:-1], '2022-23', '2023-06-01T00:00:00Z')

    def test_fit_rejects_unavailable_label_and_evaluation_season(self):
        row = {'features': [0.]*len(m.FEATURES), 'residual_return': 10., 'forecast_at': '2022-08-01T00:00:00Z',
            'label_available_at': '2023-06-01T00:00:00Z', 'season': '2022-23', 'episode': 'a'}
        model = m.fit([row], '2023-08-01T00:00:00Z')
        self.assertEqual(model['training_seasons'], ['2022-23'])
        with self.assertRaises(ValueError): m.fit([row], row['label_available_at'])
        future = dict(row, season='2023-24')
        with self.assertRaises(ValueError): m.fit([future], '2023-08-01T00:00:00Z')

    def test_learned_action_value_can_change_captain_ranking(self):
        x = [0.]*len(m.FEATURES); y = copy.deepcopy(x); y[m.FEATURES.index('captain_minutes')] = 1.
        options = [{'id': 'a', 'features': x, 'base_score': 10., 'family': 'h3_ordinary_best'},
                   {'id': 'b', 'features': y, 'base_score': 9., 'family': 'h3_ordinary_captain'}]
        self.assertEqual(m.select(options, None)[0], 0)
        coef = [0.]*len(m.FEATURES); coef[m.FEATURES.index('captain_minutes')] = 2.
        model = {'features': m.FEATURES, 'mean': x, 'scale': [1.]*len(x), 'coef': coef, 'intercept': 0.}
        self.assertEqual(m.select(options, model)[0], 1)

    def test_expiring_chip_inventory_is_not_carried_across_half(self):
        pool, xp, history = self.fixture(); before = rules.initial_state(start_gw=19)
        c = m.lineup(list(pool.pid), pool, dict(zip(pool.pid, xp[:, 0])))
        after, c = rules.apply_decision(before, c, pool.to_dict('records'), 19)
        x = m.encode(pool, xp, history, before, after, c, rules, 19)
        for chip in m.CHIPS: self.assertEqual(x[m.FEATURES.index('available_after_'+chip)], 0.)
        self.assertEqual(set(rules.available_chips(after, 20)), set(m.CHIPS))

    def test_free_hit_restores_squad_for_future_value_features(self):
        pool, xp, history = self.fixture()
        initial = rules.initial_state(); c = m.lineup(list(pool.pid), pool, dict(zip(pool.pid, xp[:, 0])))
        state, _ = rules.apply_decision(initial, c, pool.to_dict('records'), 1)
        after, c = rules.apply_decision(state, dict(c, chip='free_hit'), pool.to_dict('records'), 2)
        self.assertEqual(after['owned'], state['owned']); self.assertEqual(after['bank'], state['bank'])
        x = m.encode(pool, xp, history, state, after, c, rules, 2)
        self.assertEqual(x[m.FEATURES.index('used_free_hit')], 1.)
        self.assertEqual(x[m.FEATURES.index('available_after_free_hit')], 0.)


if __name__ == '__main__': unittest.main()
