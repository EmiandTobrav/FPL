"""Adversarial source conservation and application checks."""
import json,tempfile,unittest
from pathlib import Path
import pandas as pd
from reproduce import stage_copy,run
from predict import P,digest,write
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

    def test_positive_parent_residual_is_not_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            destination=Path(temp)/'current';stage=stage_copy(destination)
            source=stage.parent/'primary_gap_recovery'
            raw=pd.DataFrame(json.loads((source/'players.json').read_text()))
            q=pd.read_csv(source/'qualified_components.csv.gz')
            missing=raw[raw.outfielder_block.isna()].merge(q[q.outfielder_block.eq(0)][['season','fixture','code','primary_team_id']],on=['season','fixture','code','primary_team_id'])
            self.assertGreater(len(missing),0);r=missing.iloc[0]
            teams=stage.parent/'season_conservation/inputs/full_team_totals.csv';frame=pd.read_csv(teams)
            mask=frame.season.eq(r.season)&frame.fixture.eq(r.fixture)&frame.primary_team_id.eq(r.primary_team_id)
            self.assertEqual(int(mask.sum()),1);frame.loc[mask,'outfielder_block']+=1;frame.to_csv(teams,index=False)
            frozen=json.loads((source/'freeze.json').read_text());frozen['inputs']['season_conservation/inputs/full_team_totals.csv']=digest(teams);write(source/'freeze.json',frozen)
            plan=json.loads((stage/'plan.json').read_text());plan['sources']['primary_gap_recovery/freeze.json']=digest(source/'freeze.json');write(stage/'plan.json',plan)
            selected=json.loads((stage/'selection_freeze.json').read_text());selected['plan.json']=digest(stage/'plan.json');write(stage/'selection_freeze.json',selected)
            result=run(stage,'predict.py');self.assertNotEqual(result.returncode,0);self.assertFalse((stage/'predictions.csv.gz').exists())

    def test_applied_scope_preserves_keepers_and_conflicts(self):
        parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());before=pd.read_csv(P.parents[1]/parent['requirements'],low_memory=False)
        overlay=pd.read_csv(P/'results/overlay.csv.gz');keys=['season','fixture','code','field'];joined=overlay.merge(before,on=keys,validate='one_to_one')
        self.assertEqual(len(joined),27);self.assertTrue(joined.position.isin(['DEF','MID','FWD']).all());self.assertTrue(joined.status.eq('missing_data').all());self.assertTrue(joined.value_y.isna().all())
        after=pd.read_csv(P/'results/requirements.csv.xz',low_memory=False);protected=before.position.eq('GK')|before.status.eq('external_conflict')
        pd.testing.assert_frame_equal(before.loc[protected],after.loc[protected])
if __name__=='__main__':unittest.main()
