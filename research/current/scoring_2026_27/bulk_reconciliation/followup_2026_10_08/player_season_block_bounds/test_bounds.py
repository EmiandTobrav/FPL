"""Adversarial checks of real predictions and the no-error application gate."""
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from reproduce import stage_copy, run
from predict import P, digest, write

class BoundsTests(unittest.TestCase):
    def test_one_missing_block_withholds_entire_season(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = stage_copy(Path(temp) / 'current')
            raw = stage / 'inputs/2019-20.json'
            body = json.loads(raw.read_text())
            body['stats']['content'][0]['value'] -= 1
            write(raw, body)
            manifest = json.loads((stage / 'sources.json').read_text())
            manifest[0]['sha256'] = digest(raw)
            write(stage / 'sources.json', manifest)
            result = run(stage, 'predict.py')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(pd.read_csv(stage / 'predictions.csv.gz').empty)
            residual = pd.read_csv(stage / 'season_conservation.csv')
            self.assertTrue(residual.residual.eq(1).all())

    def test_known_positive_contradiction_blocks_application(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / 'current'
            stage = stage_copy(destination)
            result = run(stage, 'predict.py')
            self.assertEqual(result.returncode, 0, result.stderr)
            pred = pd.read_csv(stage / 'predictions.csv.gz')
            parent = json.loads((stage / 'inputs/parent_CURRENT.json').read_text())
            ledger_path = stage.parents[1] / parent['requirements']
            ledger = pd.read_csv(ledger_path, low_memory=False)
            choices = ledger[ledger.field.eq('goal_line_clearances') & ~ledger.is_open].merge(pred[['season', 'fixture', 'code']], on=['season', 'fixture', 'code'])
            row = choices.iloc[0]
            mask = ledger.season.eq(row.season) & ledger.fixture.eq(row.fixture) & ledger.code.eq(row.code) & ledger.field.eq('goal_line_clearances')
            self.assertEqual(int(mask.sum()), 1)
            ledger.loc[mask, 'value'] = 1
            ledger.to_csv(ledger_path, index=False)
            dependencies = json.loads((stage / 'dependencies.json').read_text())
            dependencies[str(ledger_path.relative_to(destination))] = digest(ledger_path)
            write(stage / 'dependencies.json', dependencies)
            frozen = json.loads((stage / 'prediction_freeze.json').read_text())
            frozen['dependencies.json'] = digest(stage / 'dependencies.json')
            write(stage / 'prediction_freeze.json', frozen)
            result = run(stage, 'validate.py')
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((stage / 'results/validation.json').read_text())
            self.assertFalse(report['qualified'])
            self.assertEqual(report['errors'], 1)
            self.assertNotEqual(run(stage, 'build.py').returncode, 0)
            self.assertFalse((stage / 'results/requirements.csv.xz').exists())

    def test_actual_failed_season_and_keeper_scope_preserved(self):
        pred = pd.read_csv(P / 'predictions.csv.gz')
        self.assertEqual(set(pred.season), {'2019-20'})
        parent = json.loads((P / 'inputs/parent_CURRENT.json').read_text())
        ledger = pd.read_csv(P.parents[1] / parent['requirements'], low_memory=False)
        scope = pred.merge(ledger[ledger.field.eq('goal_line_clearances')][['season', 'fixture', 'code', 'position']], on=['season', 'fixture', 'code'], validate='one_to_one')
        self.assertFalse(scope.position.eq('GK').any())
        self.assertEqual(pd.read_csv(P / 'season_conservation.csv').query("season == '2020-21'").iloc[0].residual, 1)

if __name__ == '__main__':
    unittest.main()
