"""Audit diagnostic archive eligibility, coefficients, forecasts and play."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.audit_rolling_reference_v2 import *
def forecasts():
    verify_files(R,cf.common.read(P/'proposal.json')['input_hashes']);verify_files(P,cf.common.read(P/'prediction_lock.json')['files']);d=pd.read_pickle(P/'diagnostic_archive.pkl');saved=pd.read_csv(P/(ARM+'.csv.gz')).set_index(cf.KEY);gate,recipe=cf.fixed.recipe();checked=0;current=[]
    for gw in range(1,39):
        at=pd.Timestamp(cf.common.read(cf.C/cf.S/f'gw{gw:02d}/manifest.json')['forecast_at']);q=d[d.season.eq(cf.S)&d['round'].eq(gw)]
        if gw in range(1,39,4):
            bundle=cf.common.read(P/'models'/f'gw{gw:02d}.json');assert pd.Timestamp(bundle['cutoff'])==at
            for pos in ['GK','DEF','MID','FWD']:
                for j in range(8):
                    tr=recipe.training(d,at,pos,j);assert tr.forecast_at.max()<at and tr[f'label_at_{j}'].max()<at and (tr.latest_feature_available.isna()|tr.latest_feature_available.lt(tr.forecast_at)).all();a=next(v for v in bundle['audits'] if v['key']==f'{pos}_{j}');assert len(tr)==a['rows'];model=gate.fit(tr,learned=False);np.testing.assert_allclose(model['beta'],bundle['models'][f'{pos}_{j}']['beta'],rtol=0,atol=1e-10);assert model['theta']==[0.,1.,0.];checked+=1
            current.append(int(recipe.training(d,at,'GK',0).season.eq(cf.S).sum()))
        predicted=cf.fixed.forecast(q,bundle).set_index(cf.KEY)
        for j in range(min(8,39-gw)):np.testing.assert_allclose(predicted[f'xp_{j}'],saved.reindex(predicted.index)[f'xp_{j}'],atol=1e-9,rtol=1e-10)
    assert checked==320 and current[0]==0 and all(v>0 for v in current[1:]);atomic_json(P/'forecast_verification.json',dict(passed=True,heads_replayed=320,training_clock_checks=True,same_season_updates_after_first_refit_verified=True,GK_H1_current_teacher_rows=current,only_archive_updated=True,production_changed=False));print('ROLLING FORECASTS VERIFIED',flush=True)
def managers():
    verify_files(R,cf.common.read(P/'proposal.json')['input_hashes']);verify_files(P,cf.common.read(P/'prediction_lock.json')['files']);mod,adapter=cf.backend(16,40);env=cf.ConfirmationEnvironment();pred=pd.read_csv(P/(ARM+'.csv.gz')).set_index(['round','code']);scores=[];checked=0;stops=[]
    for setting in cf.SETTINGS:
        f=P/'manager'/f'{ARM}_{setting}';state=adapter.engine.initial_state()
        if setting=='no_chips':state['used_chips']={h:list(adapter.engine.CHIPS) for h in ['1','2']}
        complete=(f/'summary.json').exists();rounds=38 if complete else len(list(f.glob('gw*.settlement.json')));net=hits=0
        if not complete:
            trace=(P/'logs'/f'{setting}.log').read_text();assert 'ControlledSolverError: Solver exceeded declared node limit' in trace or 'Unknown selected outcome' in trace;stops.append(dict(setting=setting,rounds=rounds,reason=trace.splitlines()[-1]))
        for gw in range(1,rounds+1):
            decision=cf.common.read(f/f'gw{gw:02d}.decision.json');saved=cf.common.read(f/f'gw{gw:02d}.settlement.json');assert not decision['outcomes_read'] and mod.clean(state)==decision['state_before'];pool,_,m,_=env.inputs(cf.S,gw);at=pd.Timestamp(m['forecast_at']);pool=cf.method.qualify(pool,cf.S,at);q=pred.loc[gw].reindex(pool.code);assert q.can_buy.tolist()==pool.can_buy.tolist();xp=q[[f'xp_{j}' for j in range(min(8,39-gw))]].to_numpy(float);assert hashlib.sha256(xp.tobytes()).hexdigest()==decision['forecast_input_sha256'];choice=decision['choice'];choice['prices']={int(k):v for k,v in choice['prices'].items()};state,legal=adapter.engine.apply_decision(state,choice,pool.to_dict('records'),gw);assert mod.clean(state)==decision['state_after'];outcomes,result,n=cf.settle(adapter,env,cf.S,gw,dict(choice=legal),pool);assert n==saved['net'] and outcomes==saved['outcomes'] and mod.clean(result)==saved['settlement'];assert len(decision['solver_calls'])<=40 and all(v['nodes']<=16 and v['full_mip_feasible'] for v in decision['solver_calls']);checked+=1;net+=n;hits+=4*legal['paid']
            if setting=='no_chips':assert not legal['chip']
        if complete:assert cf.common.read(f/'summary.json')['net']==net
        scores.append(dict(setting=setting,complete=complete,net=net if complete else None,hits=hits if complete else None,rounds=rounds))
    pd.DataFrame(scores).to_csv(P/'scores.csv',index=False);atomic_json(P/'manager_verification.json',dict(passed=True,decisions_replayed=checked,scores=scores,technical_stops=stops,production_changed=False));print('ROLLING DIAGNOSTIC VERIFIED',scores,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
