"""Withholding boundaries: even one qualified-counter disagreement vetoes."""
import contextlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import validate
from predict import P,K,save,digest

class WithholdingTests(unittest.TestCase):
    def test_single_disagreement_vetoes_all_candidates(self):
        rows=[dict(season='2019-20',fixture=i,code=i,field='big_chance_saves',value=0,is_open=False) for i in range(1,22)]
        rows.append(dict(season='2019-20',fixture=22,code=22,field='big_chance_saves',value=None,is_open=True))
        bounds=pd.DataFrame([{**{k:r[k] for k in K},'value':0} for r in rows])
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);(p/'inputs').mkdir();(p/'plan.json').write_bytes((P/'plan.json').read_bytes())
            save(bounds,p/'all_counter_bounds.csv.gz');save(bounds.tail(1),p/'predictions.csv.gz');(p/'prediction_freeze.json').write_text('{}')
            for bad in [False,True]:
                rows[0]['value']=int(bad);req=pd.DataFrame(rows);req.to_csv(p/'requirements.csv',index=False)
                (p/'inputs/parent_CURRENT.json').write_text(json.dumps(dict(requirements='requirements.csv',requirements_sha256=digest(p/'requirements.csv'))))
                with patch.object(validate,'P',p),patch.object(validate,'B',p),contextlib.redirect_stdout(io.StringIO()):validate.main()
                report=json.loads((p/'results/validation.json').read_text());overlay=pd.read_csv(p/'results/overlay.csv.gz')
                self.assertEqual(report['qualified'],not bad);self.assertEqual(report['errors'],int(bad));self.assertEqual(len(overlay),0 if bad else 1)
    def test_real_failure_remains_explicit(self):
        report=json.loads((P/'results/validation.json').read_text());self.assertFalse(report['qualified']);self.assertEqual(report['errors'],1)
        self.assertTrue(pd.read_csv(P/'results/overlay.csv.gz').empty);self.assertEqual(len(pd.read_csv(P/'predictions.csv.gz')),16)
if __name__=='__main__':unittest.main()
