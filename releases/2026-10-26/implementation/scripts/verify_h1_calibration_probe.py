"""Replay all ablation decisions and settle them from the frozen source outcomes."""
import sys,json,copy
from pathlib import Path
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json,verify_files
from scripts import diagnose_h1_calibration as run
P=run.P;F=run.F

def main():
    verify_files(R,json.load(open(P/'proposal.json'))['input_hashes']);run.guard.configure();m=run.guard.m;forecasts=pd.read_csv(P/'forecasts.csv.gz');control=pd.read_csv(F/'component.csv.gz');keys=['season','round','code'];merged=control.merge(forecasts,on=keys,validate='one_to_one',suffixes=('_old','_new'))
    for j in range(1,8):np.testing.assert_allclose(merged[f'xp_{j}_old'],merged[f'xp_{j}_new'],rtol=0,atol=1e-12)
    rows=[];decisions=0;calls=0;env=m.MatchedEnvironment();origins=pd.read_pickle(F/'origins.pkl')
    for s in ['2023-24','2024-25','2025-26']:
        folder=P/'manager'/s;summary=json.load(open(folder/'summary.json'));assert summary['complete'] and summary['rounds']==38;mod,adapter=run.guard.solver();state=adapter.engine.initial_state();total=hits=0
        for g in range(1,39):
            dec=json.load(open(folder/f'gw{g:02d}.decision.json'));sett=json.load(open(folder/f'gw{g:02d}.settlement.json'));assert mod.clean(state)==dec['state_before'];p=m.method.qualify(run.guard.eligible_pool(s,g),s,origins[(s,g)]);choice=copy.deepcopy(dec['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};state,choice=adapter.engine.apply_decision(state,choice,p.to_dict('records'),g);assert mod.clean(state)==dec['state_after'];outcome,replayed,n=m.settle(adapter,env,s,g,dict(choice=choice),p);assert n==sett['net'] and mod.clean(replayed)==sett['settlement'];assert len(dec['solver_calls'])<=40
            for call in dec['solver_calls']:
                assert call['full_mip_feasible'] and call['nodes']<=16
            total+=n;hits+=4*choice['paid'];calls+=len(dec['solver_calls']);decisions+=1
        assert total==summary['net'] and hits==summary['hits'];old=pd.read_csv(F/'scores.csv');old=float(old.loc[old.season.eq(s)&old.arm.eq('component'),'net'].iloc[0]);rows.append(dict(season=s,component=old,without_H1_residual_calibration=total,delta=total-old,hits=hits))
    result=pd.DataFrame(rows);result.to_csv(P/'comparison.csv',index=False);prior=result[result.season.ne('2025-26')];latest=result[result.season.eq('2025-26')].iloc[0]
    atomic_json(P/'verification.json',dict(passed=True,decisions_replayed=decisions,all_114_scores_exact=True,solver_calls=calls,node_cap=16,max_calls_per_decision=40,all_future_forecasts_unchanged=True,no_source_or_clock_change=True,active_descriptor_unchanged=True,original_latest_gap=float(latest.component-prior.component.mean()),ablated_latest_gap=float(latest.without_H1_residual_calibration-prior.without_H1_residual_calibration.mean()),files={str(p.relative_to(R)):sha(p) for p in [P/'comparison.csv',P/'forecasts.csv.gz',P/'forecast_lock.json',Path(__file__)]}))
    print(result.to_string(index=False));print('REPLAY PASSED',decisions,flush=True)
if __name__=='__main__':main()
