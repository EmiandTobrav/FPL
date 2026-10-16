import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from model_lab.common import atomic_json, claim, digest, read, sha
from model_lab.forecast import causal_training, fit_predict, validate
from model_lab import simulation


def rule_engine():
    p = Path(__file__).parents[1] / 'vendor/fpl_rules_v1/engine.py'
    spec = importlib.util.spec_from_file_location('_lab_test_rules', p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


class ForecastContracts(unittest.TestCase):
    def test_registered_model_parameters_cannot_change_after_registration(self):
        from scripts.research import fingerprint
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            names = ['datasets/fpl_model_pipeline_v1/manifest.json', 'datasets/fpl_model_pipeline_v1/schema.json',
                     'datasets/fpl_model_pipeline_v1/operational_proxy_v1.csv.xz']
            for name in names:
                p = root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('bound')
            model = {'id': 'new_candidate', 'backend': 'ridge', 'seed': 1, 'parameters': {}, 'feature_set': 'extended'}
            spec = {'version': 1, 'id': 'trial', 'purpose': 'registered_research', 'seasons': ['2023-24'], 'rounds': [1],
                'horizon': 1, 'models': [model], 'reference': model['id'], 'clock': 'operational_proxy_v1',
                'input_hashes': {n: sha(root / n) for n in names}, 'max_fits': 1, 'proposal': 'proposal.json'}
            proposal = {'dataset_id': 'test', 'input_hashes': spec['input_hashes'], 'clock': spec['clock'], 'features': 'extended',
                'candidate_id': model['id'], 'model_parameters': {k: model[k] for k in ['backend', 'seed', 'parameters']},
                'decision_policy': {'stage': 'forecast', 'horizon': 1, 'reference': model['id'], 'rounds': [1], 'window_days': None},
                'benchmark_id': 'test', 'seasons': spec['seasons'], 'resources': {'maximum_fits': 1}}
            proposal['fingerprint'] = fingerprint(proposal); spec['proposal_fingerprint'] = proposal['fingerprint']
            atomic_json(root / 'proposal.json', proposal)
            with patch('model_lab.forecast.ROOT', root):
                validate(spec)
                model['parameters'] = {'alpha': 999.}
                with self.assertRaisesRegex(ValueError, 'parameters changed'): validate(spec)

    def test_whole_target_horizon_must_be_available_strictly_before_origin(self):
        rows = pd.DataFrame({'forecast_at': pd.to_datetime(['2023-01-01Z'.replace('Z', 'T00:00Z')] * 3),
            'target_h3_available_at': pd.to_datetime(['2023-01-02T00:00Z', '2023-01-03T00:00Z', '2023-01-04T00:00Z']),
            'target_points_h3': [-2., 100., 200.]})
        train, _ = causal_training(rows, '2023-01-03T00:00Z', 3)
        self.assertEqual(train.target_points_h3.tolist(), [-2.])

    def test_unavailable_labels_never_become_zero(self):
        rows = pd.DataFrame({'forecast_at': pd.to_datetime(['2023-01-01T00:00Z']),
            'target_h1_available_at': pd.to_datetime(['2023-01-02T00:00Z']), 'target_total_points': [np.nan]})
        with self.assertRaisesRegex(ValueError, 'No causally'): causal_training(rows, '2023-01-03T00:00Z', 1)

    def test_custom_predictor_only_receives_allowlisted_prediction_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'adapter.py'
            p.write_text('def fit_predict(X, y, P, config):\n assert list(P.columns) == ["f_history"]\n assert y.tolist() == [-2.0, 0.0]\n return [1.0] * len(P)\n')
            train = pd.DataFrame({'f_history': [0., 1.], 'target': [-2., 0.]})
            pred = pd.DataFrame({'f_history': [2.], 'target': [999.], 'future_result': [999.]})
            with patch('model_lab.forecast.ROOT', Path(tmp)):
                result = fit_predict(train, pred, 'target', ['f_history'], {}, {'backend': 'custom', 'adapter': 'adapter.py'}, None)
            self.assertEqual(result.tolist(), [1.])


class ArtifactContracts(unittest.TestCase):
    def test_started_work_cannot_silently_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            claim(tmp, {'model': 1})
            with self.assertRaises(FileExistsError): claim(tmp, {'model': 1})

    def test_corrupt_completed_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); contract = {'model': 1}; claim(p, contract)
            (p / 'data').write_text('correct')
            atomic_json(p / 'complete.json', {'contract_hash': digest(contract), 'outputs': {'data': sha(p / 'data')}})
            self.assertIsNotNone(claim(p, contract))
            (p / 'data').write_text('corrupt')
            with self.assertRaisesRegex(ValueError, 'Changed bound file'): claim(p, contract)


class SimulatorBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name); self.engine = rule_engine()
        self.choice = {'squad': list(range(1, 16)), 'starters': [1, 3, 4, 5, 8, 9, 10, 11, 13, 14, 15],
            'bench': [2, 12, 6, 7], 'captain': 13, 'vice': 8,
            'prices': {str(i): 50 for i in range(1, 16)}}
        positions = [1, 1] + [2] * 5 + [3] * 5 + [4] * 3
        self.pool = pd.DataFrame({'code': range(1, 16), 'pid': range(1, 16), 'pos': positions,
            'club': [(i - 1) % 5 for i in range(1, 16)], 'market': 50, 'can_buy': True, 'metadata_complete': True,
            'price_available_at': '2023-01-01T00:00Z', 'position_available_at': '2023-01-01T00:00Z', 'club_available_at': '2023-01-01T00:00Z'})

    def tearDown(self): self.temp.cleanup()

    def bundle(self, name, points=2., missing=False):
        p = self.root / name; p.mkdir(); self.pool.to_csv(p / 'pool.csv', index=False)
        pd.DataFrame({'code': range(1, 16), 'forecast_at': '2023-01-02T00:00Z', 'xp_0': 1.}).to_csv(p / 'forecast.csv', index=False)
        outcomes = {str(i): {'points': points, 'active': True} for i in range(1, 16)}
        if missing: outcomes.pop('1')
        atomic_json(p / 'outcomes.json', outcomes)
        files = {n: sha(p / n) for n in ['pool.csv', 'forecast.csv', 'outcomes.json']}
        atomic_json(p / 'bundle.json', {'benchmark': simulation.BENCHMARK, 'files': files, 'origins': [
            {'season': '2023-24', 'round': 1, 'forecast_at': '2023-01-02T00:00Z', 'horizon': 1,
             'pool': 'pool.csv', 'outcomes': 'outcomes.json', 'forecasts': {simulation.BENCHMARK: 'forecast.csv', 'candidate': 'forecast.csv'}}]})
        return {'bundle': name + '/bundle.json', 'bundle_sha256': sha(p / 'bundle.json'), 'purpose': 'framework_validation',
            'models': [simulation.BENCHMARK, 'candidate'], 'reference': simulation.BENCHMARK,
            'max_decisions': 2, 'node_limit': 16, 'max_calls_per_decision': 40, 'policy': 'fixed'}

    def fake_backend(self, *args):
        engine = self.engine; choice = copy.deepcopy(self.choice)
        class Adapter:
            ledger = []
            def plan(self, pool, xp, state, gw, chip, fixed):
                assert 'points' not in pool and 'active' not in pool
                return {'choice': copy.deepcopy(choice)}
        adapter = Adapter(); adapter.engine = engine
        class Module:
            @staticmethod
            def clean(v): return v
        return Module, adapter

    def test_changed_outcomes_cannot_change_decisions(self):
        a = self.bundle('a', 2.); b = self.bundle('b', -1.)
        with patch.object(simulation, 'ROOT', self.root), patch.object(simulation, 'backend', self.fake_backend):
            ra = simulation.run(a, self.root / 'results'); rb = simulation.run(b, self.root / 'results')
        da = read(Path(ra['directory']) / 'decisions.json'); db = read(Path(rb['directory']) / 'decisions.json')
        self.assertEqual([r['decision'] for r in da], [r['decision'] for r in db])
        self.assertNotEqual(da[0]['net_points'], db[0]['net_points'])
        self.assertEqual(da[0]['net_points'], 24.)

    def test_unknown_selected_outcome_stops_instead_of_becoming_zero(self):
        spec = self.bundle('missing', missing=True)
        with patch.object(simulation, 'ROOT', self.root), patch.object(simulation, 'backend', self.fake_backend):
            with self.assertRaises(self.engine.MissingOutcomeError): simulation.run(spec, self.root / 'results')
        locks = list((self.root / 'results').rglob('locked_decisions/*/gw01.json'))
        self.assertEqual(len(locks), 1)
        self.assertIs(read(locks[0])['outcomes_read'], False)

    def test_future_metadata_is_rejected(self):
        spec = self.bundle('future'); p = self.root / 'future'; manifest = read(p / 'bundle.json')
        self.pool['price_available_at'] = '2023-01-03T00:00Z'; self.pool.to_csv(p / 'pool.csv', index=False)
        with self.assertRaisesRegex(ValueError, 'Future or missing'):
            simulation.pool_input(p, manifest['origins'][0], 'candidate')

    def test_missing_round_cannot_be_silently_skipped(self):
        spec = self.bundle('skip'); p = self.root / 'skip'; manifest = read(p / 'bundle.json')
        manifest['origins'][0]['round'] = 2
        # Rewrite a new contract explicitly, retaining immutable artifact behavior elsewhere.
        (p / 'bundle.json').write_text(json.dumps(manifest)); spec['bundle_sha256'] = sha(p / 'bundle.json')
        with patch.object(simulation, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'contiguous'): simulation.run(spec, self.root / 'results')


if __name__ == '__main__': unittest.main()
