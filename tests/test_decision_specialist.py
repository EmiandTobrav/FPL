from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/current'))
from decision_specialist.models import future_proxy,gate_design,fit_gate,predict_gate

def test_future_proxy_removes_double_round_and_uses_blank_fallback():
    # Frozen reference neutral is 4: double current 12 gives future1=5.
    # Refreshed per-fixture increment is 1, so its neutral becomes5.
    out=future_proxy([14.,0.],[12.,0.],[2,0],[5.,3.])
    np.testing.assert_allclose(out,[[14,6,5.5],[0,3,3]])
    reference=future_proxy([12.,0.],[12.,0.],[2,0],[5.,3.])
    np.testing.assert_allclose(reference,[[12,5,4.5],[0,3,3]])

def test_conditional_gate_learns_which_expert_is_useful_and_stays_convex():
    m=np.tile([20.,80.],100);old=np.full(len(m),80.)
    x=gate_design(m,old);a=np.full(len(m),2.);b=np.full(len(m),8.);y=np.where(m<30,7.,3.)
    beta,_=fit_gate(x,a,b,y,np.ones(len(m)),True)
    constant,_=fit_gate(x,a,b,y,np.ones(len(m)),False)
    xt=gate_design([25.,75.],[80.,80.]);truth=np.array([7.,3.])
    pred,w=predict_gate(xt,np.array([2.,2.]),np.array([8.,8.]),beta)
    control,_=predict_gate(xt,np.array([2.,2.]),np.array([8.,8.]),constant)
    assert np.mean((pred-truth)**2)<.25*np.mean((control-truth)**2)
    assert w[0]>w[1] and np.all((w>0)&(w<1))
    assert np.all((pred>=2)&(pred<=8))

def test_new_planner_preserves_budget_and_free_transfer_carry():
    import pandas as pd
    import experiment
    from decision_specialist.planner import solve
    p=pd.DataFrame(dict(pid=range(1,16),pos=[1]*2+[2]*5+[3]*5+[4]*3,club=[i%5 for i in range(15)],market=[50]*15,can_buy=True))
    c=solve(p,np.full((15,3),3.),{i:50 for i in p.pid},25,4,[None]*3)
    assert c['transfers']==0 and c['bank_after']==25
    assert [r['free_before'] for r in c['plan']]==[5,5]
    assert all(r['bank_after']==25 and r['paid']==0 for r in c['plan'])
