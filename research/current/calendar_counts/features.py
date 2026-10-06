import numpy as np,pandas as pd

def count_forecast(base,clubs,snapshot,team_codes,gw,age_days,max_age_days=14):
    base=np.asarray(base,dtype=float);result=base.copy();clubs=np.asarray(clubs)
    assert base.shape==(len(clubs),3) and age_days>=0
    if age_days>max_age_days:return result
    for j in [1,2]:
        if gw+j>38:continue
        scheduled=snapshot[snapshot.event==gw+j]
        counts=pd.concat([scheduled.team_h,scheduled.team_a]).map(team_codes).value_counts()
        assert not pd.concat([snapshot.team_h,snapshot.team_a]).map(team_codes).isna().any()
        result[:,j]*=pd.Series(clubs).map(counts).fillna(0).to_numpy()
    np.testing.assert_array_equal(result[:,0],base[:,0])
    return result
