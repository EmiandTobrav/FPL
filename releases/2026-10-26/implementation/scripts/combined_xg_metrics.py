"""Evaluate combined minutes from its actual xG bases, independently of arm names.

The shared three-arm reporter routes an unknown fourth arm to control minutes.
Correct that reporting-only dispatch before season outcomes are inspected.
"""
from scripts import combined_xg_adaptation as c
import pandas as pd,numpy as np
from model_lab.common import atomic_json,sha

def main():
    P=c.P;F=c.t.F;R=c.R;KEY=c.t.KEY;c.t.check()
    m=pd.read_csv(P/'forecast_metrics.csv');old=m.copy();d=c.t.load(F/'head_data.pkl');av=pd.read_csv(F/'availability.csv.gz');d=d.merge(av[KEY+['model_can_buy']],on=KEY,validate='one_to_one')
    raw=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=KEY+['native_minutes']);truth=raw.groupby(KEY).native_minutes.sum(min_count=1).rename('target_minutes_1').reset_index();d=d.merge(truth,on=KEY,how='left',validate='one_to_one');windows=[]
    for j in range(3):
        q=truth.copy();q['round']-=j;windows.append(d[KEY].merge(q,on=KEY,how='left',validate='one_to_one').target_minutes_1)
    d['target_minutes_3']=pd.concat(windows,axis=1).sum(axis=1,min_count=3);ref=pd.read_csv(F/'operational_matched.csv.gz').set_index(KEY);d['common_rank']=ref.reindex(pd.MultiIndex.from_frame(d[KEY])).xp_0.to_numpy();d['common_top']=False
    for (_,_,pos),q in d[d.model_can_buy&d.season.isin(c.t.EVAL)].groupby(['season','round','position']):d.loc[q.nlargest(dict(GK=5,DEF=20,MID=20,FWD=10)[pos],'common_rank').index,'common_top']=True
    actual_bases=pd.concat([c.t.load(P/f'base_{s}.pkl') for s in c.t.S]).set_index(KEY);checked=0
    for row in m[m.arm.eq('combined')&m.target.eq('minutes')].itertuples():
        q=d[d.season.eq(row.season)&d.model_can_buy].copy()
        if row.scope=='common_top':q=q[q.common_top]
        elif row.scope=='common_MID':q=q[q.common_top&q.position.eq('MID')]
        elif row.scope=='premium9plus':q=q[q.price_tenths.ge(90)]
        else:assert row.scope=='all_buyable'
        h=row.horizon;q=q[q[[f'y_{j}' for j in range(h)]].notna().all(axis=1)&(q['round']+h<=39)&q[f'target_minutes_{h}'].notna()];assert len(q)==row.n
        err=actual_bases.reindex(pd.MultiIndex.from_frame(q[KEY]))[f'component_m{h}'].to_numpy()-q[f'target_minutes_{h}'].to_numpy();values=dict(mse=float(np.mean(err**2)),mae=float(np.mean(abs(err))),bias=float(np.mean(err)),actual_variance=float(np.var(q[f'target_minutes_{h}'])))
        for field,value in values.items():m.loc[row.Index,field]=value
        reference=m[m.season.eq(row.season)&m.scope.eq(row.scope)&m.target.eq('minutes')&m.horizon.eq(h)&m.arm.eq('xg_only')].iloc[0]
        np.testing.assert_allclose(list(values.values()),reference[list(values)].to_numpy(float),atol=1e-9,rtol=1e-10);checked+=1
    assert checked==24
    pd.testing.assert_frame_equal(old[~(old.arm.eq('combined')&old.target.eq('minutes'))],m[~(m.arm.eq('combined')&m.target.eq('minutes'))])
    backup=P/'forecast_metrics_first_pass_incorrect_combined_minutes.csv';assert not backup.exists();old.to_csv(backup,index=False);m.to_csv(P/'forecast_metrics.csv',index=False)
    atomic_json(P/'metric_reporting_correction.json',dict(passed=True,reason='Three-arm shared reporter routed fourth-arm minutes to control. Recomputed24combined-minute cells from actual reused xG bases and native outcomes; all point scores and other arms unchanged.',no_models_forecasts_targets_or_manager_changes=True,all24_cells_match_identical_xg_minute_predictions=True,checked_cells=checked,files={str(p.relative_to(R)):sha(p) for p in [P/'forecast_metrics.csv',backup,c.Path(__file__)]}));print('COMBINED MINUTE METRICS INDEPENDENTLY VERIFIED',flush=True)

if __name__=='__main__':main()
