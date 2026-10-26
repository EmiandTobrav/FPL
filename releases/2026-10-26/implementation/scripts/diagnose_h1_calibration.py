"""Single preregistered calibration ablation. No new fitted parameters."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import copy,sys,json,hashlib
from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json,verify_files
from scripts import matched_availability_retest_v8 as guard
P=R/'reports/component_h1_calibration_probe_2026_10_26';F=guard.P

def prepare():
    d=pd.read_pickle(F/'head_data.pkl');q=pd.read_csv(F/'component.csv.gz');q=q.merge(d[['season','round','code','component_p1','u_count_0']],on=['season','round','code'],validate='one_to_one');av=pd.read_csv(F/'availability.csv.gz');q=q.merge(av[['season','round','code','confirmed_out_current','known_departed']],on=['season','round','code'],validate='one_to_one');old=q[[f'xp_{j}' for j in range(8)]].copy();q.xp_0=q.component_p1;q.loc[q.confirmed_out_current|q.known_departed|q.u_count_0.eq(0),'xp_0']=0
    np.testing.assert_allclose(q[[f'xp_{j}' for j in range(1,8)]],old[[f'xp_{j}' for j in range(1,8)]],rtol=0,atol=0);assert np.isfinite(q.xp_0).all();q.drop(columns=['component_p1','u_count_0','confirmed_out_current','known_departed']).to_csv(P/'forecasts.csv.gz',index=False)
    atomic_json(P/'forecast_lock.json',dict(only_xp0_changed=True,all_future_offsets_exact=True,hard_availability_and_blank_zeros_preserved=True,files={'forecasts.csv.gz':sha(P/'forecasts.csv.gz')}))

def run(season):
    verify_files(R,json.load(open(P/'proposal.json'))['input_hashes']);verify_files(P,json.load(open(P/'forecast_lock.json'))['files']);guard.configure();m=guard.m;origins=pd.read_pickle(F/'origins.pkl');forecast=pd.read_csv(P/'forecasts.csv.gz');forecast=forecast[forecast.season.eq(season)].set_index(['round','code']);env=m.MatchedEnvironment();folder=P/'manager'/season;folder.mkdir(parents=True,exist_ok=False);_,a=guard.solver();state=a.engine.initial_state();total=hits=0
    for g in range(1,39):
        at=origins[(season,g)];pool=m.method.qualify(guard.eligible_pool(season,g),season,at);q=forecast.loc[g].reindex(pool.code);assert pd.to_datetime(q.forecast_at,utc=True).eq(at).all();assert q.can_buy.tolist()==pool.can_buy.tolist();xp=q[[f'xp_{j}' for j in range(min(8,39-g))]].to_numpy(float);mod,a=guard.solver();choice=copy.deepcopy(a.decide(pool,xp,state,g)['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};after,choice=a.engine.apply_decision(state,choice,pool.to_dict('records'),g)
        atomic_json(folder/f'gw{g:02d}.decision.json',mod.clean(dict(state_before=state,state_after=after,choice=choice,forecast_at=str(at),solver_calls=a.ledger,outcomes_read=False,forecast_input_sha256=hashlib.sha256(xp.tobytes()).hexdigest())))
        outcomes,settlement,net=m.settle(a,env,season,g,dict(choice=choice),pool);atomic_json(folder/f'gw{g:02d}.settlement.json',mod.clean(dict(net=net,hits=4*choice['paid'],outcomes=outcomes,settlement=settlement)));total+=net;hits+=4*choice['paid'];state=after
        if g%8==0:print('H1 ABLATION',season,g,flush=True)
    atomic_json(folder/'summary.json',dict(season=season,net=total,hits=hits,rounds=38,complete=True));print('COMPLETE',season,total,flush=True)
if __name__=='__main__':prepare() if sys.argv[1]=='prepare' else run(sys.argv[1])
