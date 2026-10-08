from pathlib import Path
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
import plan
import validate

class PenaltyControlsTests(unittest.TestCase):
    def test_selection_does_not_read_fpl_assist_outcomes(self):
        original = pd.read_csv
        def read(path, *args, **kwargs):
            if Path(path).name == 'fpl_baseline.csv.gz':
                raise AssertionError('Outcome accessed during selection')
            return original(path, *args, **kwargs)
        with patch.object(plan.pd, 'read_csv', side_effect=read):
            plan.main()
        frozen = json.loads((plan.P / 'freeze.json').read_text())
        self.assertFalse(frozen['outcomes_read_by_selection'])
        self.assertGreaterEqual(frozen['comparisons'], 20)
        self.assertGreaterEqual(frozen['distinct_fixtures'], 20)

    def test_wrong_assist_outcome_blocks_qualification(self):
        original = pd.read_csv
        control = original(plan.P / 'plan.csv').iloc[0]
        def read(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if Path(path).name == 'fpl_baseline.csv.gz':
                match = result.season.eq(control.season) & result.fixture.eq(control.fixture) & result.code.eq(control.code)
                self.assertEqual(int(match.sum()), 1)
                result.loc[match, 'assists'] -= 1
            return result
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for name in ['freeze.json', 'plan.csv', 'validation_lock_v2.json']:
                shutil.copyfile(plan.P / name, out / name)
            with patch.object(validate, 'P', out), patch.object(validate.pd, 'read_csv', side_effect=read):
                result = validate.validate()
            self.assertGreater(result['residual_errors'], 0)
            self.assertEqual(result['qualified_kinds'], [])

    def test_frozen_input_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            freeze = json.loads((plan.P / 'freeze.json').read_text())
            first = next(iter(freeze['inputs']))
            freeze['inputs'][first] = '0' * 64
            (out / 'freeze.json').write_text(json.dumps(freeze))
            with patch.object(validate, 'P', out):
                with self.assertRaisesRegex(ValueError, 'Frozen input changed'):
                    validate.validate()

if __name__ == '__main__':
    unittest.main()
