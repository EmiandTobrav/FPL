from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/current'))
from legacy_candidates import ResidualHGB, minutes_baseline


def test_residual_training_and_addback():
    class Capture:
        def fit(self,x,y): self.target=y.copy()
        def predict(self,x): return np.full(len(x),2.)
    x=pd.DataFrame({'historic_m6':[4.,6.,np.nan], 'minutes_m6':[90.,45.,0.]})
    model=ResidualHGB();model.model=Capture()
    model.fit(x,np.array([5.,2.,0.]))
    np.testing.assert_allclose(model.model.target,[1.,-1.,0.])
    np.testing.assert_allclose(model.predict(x),[6.,5.,2.])


def test_minutes_shrinkage_uses_no_current_outcome():
    x=pd.DataFrame({'historic_m6':[4.], 'minutes_m6':[45.], 'historic':[1000.]})
    a=minutes_baseline(x);x['historic']=-1000.
    np.testing.assert_array_equal(minutes_baseline(x),a)


def test_frozen_trace_accounting_and_common_handoff():
    import gzip,json
    paths=list((ROOT/'research/current/results').glob('trace_*.json.gz'))
    assert len(paths)==120
    handoffs={}
    for p in paths:
        d=json.loads(gzip.decompress(p.read_bytes()));s=d['summary']
        h=json.dumps(d['handoff'],sort_keys=True)
        assert handoffs.setdefault(s['season'],h)==h
        assert [r['gw'] for r in d['trace']]==list(range(5,39))
        assert s['points38']==s['opening_points']+sum(r['gross']-r['hits'] for r in d['trace'])
        for r in d['trace']:
            assert r['gross']==sum(r['contributions'].values())+r['captain_bonus']
            assert r['bank']>=0 and len(set(r['squad']))==15
