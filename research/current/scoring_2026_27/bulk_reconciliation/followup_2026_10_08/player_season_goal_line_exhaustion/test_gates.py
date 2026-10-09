"""Counterexamples must block the full frozen conservation qualification."""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import predict
import validate

class ConservationGates(unittest.TestCase):
    def check_counterexample(self, partial):
        original = predict.P
        with tempfile.TemporaryDirectory(prefix='fpl-gl-gate-test-') as temp:
            stage = Path(temp) / 'stage'
            shutil.copytree(original, stage, ignore=shutil.ignore_patterns('__pycache__'))
            groups = pd.read_csv(stage / 'season_groups.csv')
            row = groups[groups.all_values_complete].index[0]
            groups.loc[row, 'known_sum'] = groups.loc[row, 'source_total'] + 1
            if partial:
                groups.loc[row, 'all_values_complete'] = False
                groups.loc[row, 'open_matches'] = 1
            groups.to_csv(stage / 'season_groups.csv', index=False)
            freeze = json.loads((stage / 'prediction_freeze.json').read_text())
            freeze['season_groups.csv'] = predict.digest(stage / 'season_groups.csv')
            predict.write(stage / 'prediction_freeze.json', freeze)
            with patch.object(predict, 'P', stage), patch.object(validate, 'P', stage), contextlib.redirect_stdout(io.StringIO()):
                validate.main()
            result = json.loads((stage / 'validation.json').read_text())
            self.assertFalse(result['qualified'])
            self.assertEqual(result['fields_closed'], 0)
            self.assertEqual(result['complete_sum_errors'] if not partial else result['partial_negative_residuals'], 1)

    def test_complete_counter_mismatch_blocks_without_exclusion(self):
        self.check_counterexample(partial=False)

    def test_negative_partial_residual_blocks(self):
        self.check_counterexample(partial=True)

if __name__ == '__main__':
    unittest.main()
