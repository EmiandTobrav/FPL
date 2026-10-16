import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace
import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location('_test_learned_component', Path(__file__).with_name('policy.py'))
policy = importlib.util.module_from_spec(spec); spec.loader.exec_module(policy)


class LearnedPolicyChecks(unittest.TestCase):
    def sample(self, season, available, y):
        return {'season': season, 'chip': 'triple_captain', 'features': [1.] * len(policy.FEATURES),
                'forecast_at': season[:4] + '-08-01T00:00:00Z', 'label_available_at': available, 'wait_bonus': y}

    def test_future_label_and_current_season_outcomes_do_not_enter_fit(self):
        early = self.sample('2022-23', '2023-05-30T00:00:00Z', 3.)
        late = self.sample('2023-24', '2024-05-30T00:00:00Z', 9999.)
        a = policy.fit([early], '2023-08-01T00:00:00Z')
        b = policy.fit([early, late], '2023-08-01T00:00:00Z')
        self.assertEqual(a, b); self.assertEqual(a['triple_captain']['rows'], 1)

    def test_label_at_cutoff_is_not_available(self):
        row = self.sample('2022-23', '2023-08-01T00:00:00Z', 2.)
        self.assertIsNone(policy.fit([row], row['label_available_at'])['triple_captain'])

    def test_no_training_is_exact_baseline_fallback_and_other_chips_unchanged(self):
        original = lambda chip, gw: float(gw)
        adapter = SimpleNamespace(policy=SimpleNamespace(reserve_value=original))
        pool = pd.DataFrame({'pid': [1, 2], 'can_buy': [True, True]})
        xp = np.array([[1., 2.], [2., 3.]]); before = xp.copy()
        policy.attach(adapter, {'triple_captain': None, 'bench_boost': None}, pool, xp, {'owned': {}, 'bank': 1000, 'ft': 1}, 1)
        for chip in ['triple_captain', 'bench_boost', 'wildcard', 'free_hit']:
            self.assertEqual(adapter.policy.reserve_value(chip, 1), original(chip, 1))
        np.testing.assert_array_equal(xp, before)

    def test_prediction_matches_saved_training_scaler_and_is_nonnegative(self):
        rows = [self.sample('2022-23', '2023-05-30T00:00:00Z', -4.)]
        fitted = policy.fit(rows, '2023-08-01T00:00:00Z')['triple_captain']
        self.assertEqual(policy.predict(fitted, [1.] * len(policy.FEATURES)), 0.)


if __name__ == '__main__': unittest.main()
