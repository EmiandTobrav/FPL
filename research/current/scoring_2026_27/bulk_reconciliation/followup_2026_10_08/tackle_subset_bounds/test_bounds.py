"""Synthetic evidence-boundary tests and preservation of frozen native cells."""
import contextlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import predict
from prepare import P,B,K,digest

class BoundsTests(unittest.TestCase):
    def test_missing_positive_conflicting_and_signed_counters(self):
        # 1 exact zero; 2 unknown total; 3 positive unknown wins;
        # 4 protected conflict; 5 known wins with signed negative net;
        # 6 impossible wins; 7 non-integral total; 8 closed native value.
        rows=[]
        def row(code,field,value,opened=False,status='documented_source_reconciliation'):
            rows.append(dict(season='2020',fixture=1,code=code,field=field,value=value,is_open=opened,status=status,provenance='test_explicit_source'))
        for code,total,won in [(1,0,None),(2,None,None),(3,2,None),(4,0,None),(5,3,1),(6,1,2),(7,0.5,None),(8,0,0)]:
            row(code,'total_tackles',total,total is None,'missing_data' if total is None else 'documented_source_reconciliation')
            row(code,'won_tackles',won,won is None,'external_conflict' if code==4 else 'missing_data' if won is None else 'native_fpl')
            row(code,'legacy_net_tackles',0 if code==8 else None,code!=8,'external_conflict' if code==4 else 'missing_data' if code!=8 else 'native_fpl')
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);req=p/'requirements.csv';pd.DataFrame(rows).to_csv(req,index=False)
            (p/'inputs').mkdir();(p/'inputs/parent_CURRENT.json').write_text(json.dumps(dict(requirements=req.name,requirements_sha256=digest(req))))
            (p/'selection_freeze.json').write_text('{}')
            for n in ['predict.py','prepare.py','protocol.json','dependencies.json']:(p/n).write_bytes((P/n).read_bytes())
            with patch.object(predict,'P',p),patch.object(predict,'B',p),contextlib.redirect_stdout(io.StringIO()):predict.main()
            out=pd.read_csv(p/'predictions.csv.gz');actual={(r.code,r.field):r.value for r in out.itertuples()}
            self.assertEqual(actual,{(1,'won_tackles'):0,(1,'legacy_net_tackles'):0,(5,'legacy_net_tackles'):-1})
    def test_invalid_count_types(self):
        for value in [None,float('nan'),float('inf'),-1,0.5,True,'0']:
            self.assertFalse(predict.nonnegative(value))
        self.assertTrue(predict.nonnegative(0));self.assertTrue(predict.nonnegative(3.0))
    def test_published_application_preserves_non_targets(self):
        parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());old=pd.read_csv(B/parent['requirements'],low_memory=False);new=pd.read_csv(P/'results/requirements.csv.xz',low_memory=False)
        overlay=pd.read_csv(P/'results/overlay.csv.gz');mask=pd.MultiIndex.from_frame(old[K]).isin(pd.MultiIndex.from_frame(overlay[K]))
        self.assertEqual(int(mask.sum()),2);pd.testing.assert_frame_equal(old.loc[~mask],new.loc[~mask])
        self.assertTrue(new.loc[mask,'value'].eq(0).all());self.assertFalse(new.loc[mask,'is_open'].any())
if __name__=='__main__':unittest.main()
