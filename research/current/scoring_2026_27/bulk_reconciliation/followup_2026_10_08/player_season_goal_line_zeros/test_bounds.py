"""Adversarial checks of the actual explicit-zero route."""
import json,tempfile,unittest
from pathlib import Path
import pandas as pd
from reproduce import stage_copy,run
from predict import P,digest,write

def mutate_source(stage,owner=False):
    raw=stage/'inputs/2021-22.json';body=json.loads(raw.read_text());record=next(v for v in body['stats']['content'] if v['owner']['altIds']['opta']=='p225796')
    if owner:record['owner']['id']+=1
    else:body['stats']['content'].remove(record);body['stats']['pageInfo']['numEntries']-=1
    write(raw,body);sources=json.loads((stage/'sources.json').read_text());next(v for v in sources if v['season']=='2021-22')['sha256']=digest(raw);write(stage/'sources.json',sources)
    frozen=json.loads((stage/'reference_selection_freeze.json').read_text());frozen['sources.json']=digest(stage/'sources.json');write(stage/'reference_selection_freeze.json',frozen)

class BoundsTests(unittest.TestCase):
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

    def test_unlisted_player_is_not_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            stage=stage_copy(Path(temp)/'current');mutate_source(stage)
            result=run(stage,'predict.py');self.assertEqual(result.returncode,0,result.stderr)
            pred=pd.read_csv(stage/'predictions.csv.gz');self.assertFalse((pred.season.eq('2021-22')&pred.code.eq(225796)).any())

    def test_changed_primary_owner_blocks_prediction(self):
        with tempfile.TemporaryDirectory() as temp:
            stage=stage_copy(Path(temp)/'current');mutate_source(stage,owner=True)
            result=run(stage,'predict.py');self.assertNotEqual(result.returncode,0);self.assertFalse((stage/'predictions.csv.gz').exists())
if __name__=='__main__':unittest.main()
