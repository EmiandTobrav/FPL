"""Counter/source guard failures veto application; whole groups abstain."""
import contextlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import validate
from prepare import P,B,K,digest,save

class GuardTests(unittest.TestCase):
    def test_unexplained_error_and_guard_leak_veto(self):
        bounds=pd.DataFrame([dict(season='2019-20',fixture=i,code=i,field='big_chance_saves',value=0,emitted_value=0,source_guarded=False) for i in range(1,22)]+[dict(season='2019-20',fixture=22,code=22,field='big_chance_saves',value=0,emitted_value=None,source_guarded=True)])
        req=bounds[K].copy();req['value']=0.;req.loc[21,'value']=1.;req['is_open']=False
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'guarded';p.mkdir();(p/'inputs').mkdir();old=p.parent/'big_chance_zero_bounds/results';old.mkdir(parents=True)
            save(req[K],old/'closed_counter_controls.csv.gz');(p/'protocol.json').write_bytes((P/'protocol.json').read_bytes());(p/'prediction_freeze.json').write_text('{}')
            guards=pd.DataFrame([dict(season='2019-20',exception_fixture=22,exception_code=22,approved_big_chance_saves=1)])
            save(guards,p/'source_guards.csv.gz');save(bounds.iloc[:0],p/'predictions.csv.gz')
            for scenario in ['valid','counter_error','guard_leak']:
                x=req.copy();y=bounds.copy()
                if scenario=='counter_error':x.loc[0,'value']=1.
                if scenario=='guard_leak':y.loc[21,'emitted_value']=0
                x.to_csv(p/'requirements.csv',index=False);save(y,p/'all_counter_bounds.csv.gz')
                (p/'inputs/parent_CURRENT.json').write_text(json.dumps(dict(requirements='requirements.csv',requirements_sha256=digest(p/'requirements.csv'))))
                with patch.object(validate,'P',p),patch.object(validate,'B',p),contextlib.redirect_stdout(io.StringIO()):validate.main()
                report=json.loads((p/'results/validation.json').read_text())
                self.assertEqual(report['qualified'],scenario=='valid');self.assertEqual(report['all_original_controls'],22)
    def test_whole_source_group_and_missing_target_are_withheld(self):
        bounds=pd.read_csv(P/'all_counter_bounds.csv.gz');guarded=bounds[bounds.source_guarded]
        self.assertEqual(len(guarded),13);self.assertTrue(guarded.emitted_value.isna().all())
        parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());req=pd.read_csv(B/parent['requirements'],low_memory=False)
        pending=guarded.merge(req[req.is_open][K],on=K,validate='one_to_one');self.assertEqual(len(pending),1)
        overlay=pd.read_csv(P/'results/overlay.csv.gz');self.assertFalse(overlay.source_guarded.any());self.assertEqual(len(overlay),15)
        new=pd.read_csv(P/'results/requirements.csv.xz',low_memory=False);mask=pd.MultiIndex.from_frame(req[K]).isin(pd.MultiIndex.from_frame(overlay[K]))
        pd.testing.assert_frame_equal(req.loc[~mask],new.loc[~mask]);self.assertTrue(new.loc[mask,'value'].eq(0).all())
    def test_original_failed_rule_and_event_exception_are_retained(self):
        old=json.loads((P.parent/'big_chance_zero_bounds/results/validation.json').read_text());self.assertFalse(old['qualified']);self.assertEqual(old['errors'],1)
        report=json.loads((P/'results/validation.json').read_text());self.assertEqual(report['all_original_controls'],983);self.assertEqual(report['verified_negative_controls'],1);self.assertEqual(report['guard_abstentions'],12)
        e=pd.read_csv(P/'guard_event_evidence.csv.gz');self.assertTrue(e.qualifier_json.map(lambda q:'214' in json.loads(q)).all());self.assertTrue(e.blocked.eq(False).all())
if __name__=='__main__':unittest.main()
