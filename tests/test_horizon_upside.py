from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/current'))
import experiment
from horizon_upside.features import horizon_forecast,combine
from horizon_upside.planner import solve
from horizon_upside.run import horizon_chips

def test_neutral_future_does_not_repeat_double_or_blank_round():
    f=horizon_forecast([12,0],[4,3],[2,0])
    np.testing.assert_allclose(f,[[12,5,4.5,4.25],[0,3,3,3]])

def test_mixture_includes_ordinary_points_and_extreme_probabilities():
    np.testing.assert_allclose(combine([0,.25,1],[12,12,12],[4,4,4]),[4,6,12])

def test_horizon_stops_at_reset_chips_and_season_end():
    assert horizon_chips(5,4,'fixed_chips')==[None]
    assert horizon_chips(18,4,'fixed_chips')==['free_hit']
    assert horizon_chips(37,4,'no_chips')==[None,None]

def test_planner_carries_free_transfers_and_preserves_cash():
    p=pd.DataFrame(dict(pid=range(1,16),pos=[1]*2+[2]*5+[3]*5+[4]*3,club=[i%5 for i in range(15)],market=[50]*15,can_buy=True))
    owned={i:50 for i in p.pid}
    c=solve(p,np.full((15,4),3.),owned,25,4,[None]*4)
    assert c['transfers']==0 and c['bank_after']==25
    assert [r['free_before'] for r in c['plan']]==[5,5,5]
    assert all(r['bank_after']==25 and r['paid']==0 for r in c['plan'])
    import json
    json.dumps(c['plan'],default=lambda x:x.item() if isinstance(x,np.generic) else list(x))

def test_multistage_plan_can_schedule_purchase_later():
    p=pd.DataFrame(dict(pid=range(1,17),pos=[1]*2+[2]*5+[3]*5+[4]*4,club=[i%6 for i in range(16)],market=[50]*16,can_buy=True))
    # Club limits: initial holdings 3,3,3,2,2,2; replacement club 3 has spare capacity.
    owned={i:50 for i in range(1,16)};xp=np.full((16,2),3.);xp[-1]=[0,20]
    c=solve(p,xp,owned,0,1,[None,None])
    assert 16 not in c['squad'] and 16 in c['plan'][0]['squad']
    assert c['plan'][0]['paid']==0 and c['plan'][0]['free_before']==2

def test_planner_charges_hits_and_uses_profit_adjusted_sale_prices():
    p=pd.DataFrame(dict(pid=range(1,18),pos=[1]*2+[2]*5+[3]*5+[4]*3+[2]*2,club=[i%6 for i in range(17)],market=[50]*17,can_buy=True))
    xp=np.full((17,2),3.);xp[-2:]=100
    c=solve(p,xp,{i:40 for i in range(1,16)},10,1,[None,None])
    assert c['transfers']==2 and c['paid']==1 and c['bank_after']==0
    assert c['plan'][0]['free_before']==1
