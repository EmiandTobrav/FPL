from pathlib import Path
import sys
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/current/behavior_diagnostics'))
from common import states_before,components,experiment
from scenarios import scenarios

def test_state_reconstruction_uses_persistent_owned_after_free_hit():
    obj={'handoff':{'owned':{'1':50},'bank':5,'ft':2},'trace':[
        {'gw':5,'squad':[9],'purchase_prices':{'1':50},'bank':5,'ft':2},
        {'gw':6,'squad':[2],'purchase_prices':{'2':60},'bank':0,'ft':1},
        {'gw':7,'squad':[2],'purchase_prices':{'2':60},'bank':0,'ft':2}]}
    result=states_before(obj)
    assert result[6]['owned']=={1:50}
    assert result[7]['owned']=={2:60} and result[7]['ft']==1
    result[5]['owned'][1]=999
    assert result[6]['owned'][1]==50 and obj['handoff']['owned']['1']==50

def test_bench_boost_increment_excludes_points_that_autosub_would_count():
    pos={1:1,2:2,3:2,4:2,5:3,6:3,7:3,8:3,9:4,10:4,11:4,12:1,13:2,14:2,15:3}
    points={i:2 for i in pos};points[2]=0;points[13]=8
    active={i:True for i in pos};active[2]=False
    game={'frame':pd.DataFrame({'pid':list(pos),'pos':list(pos.values())}),'actual':points,'active':active}
    starters=list(range(1,12));bench=[12,13,14,15]
    gross=experiment.settle(starters,bench,5,6,pos,points,active,'bench_boost')['gross']
    row=dict(starters=starters,bench=bench,captain=5,vice=6,chip='bench_boost',gross=gross,hits=4,net=gross-4)
    parts=components(row,game)
    assert parts['bb']==6
    assert parts['captain']==2 and sum(parts.values())==row['net']

def test_scenario_membership_ignores_actual_outcomes_and_keeps_missing_separate():
    p=pd.DataFrame({'pos':[3,4],'market':[60,100],'minutes_m6':[np.nan,80],'minutes_m12':[60,60],'n_history':[2,40],'count':[1,2],'home':[1,.5],'opp_ga':[.9,1.8],'opp_gf':[1.8,.9],'team_gf':[1.5,2],'elo_diff':[-120,120],'actual':[0,1]})
    a=scenarios(p,5);p['actual']=[100,-10];b=scenarios(p,5)
    for key in a:np.testing.assert_array_equal(a[key],b[key])
    assert list(a['minutes6'])==['missing','regular']
    assert list(a['minutes_change'])==['missing','rising']
    assert list(a['opponent_defence'])==['strong','weak']
