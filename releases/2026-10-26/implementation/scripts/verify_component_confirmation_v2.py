"""Independent fit gradients and complete legal settlement replay."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.component_confirmation_v2 import *

def forecasts():
    verify_files(R,common.read(P/'proposal.json')['input_hashes']);lock=common.read(P/'prediction_lock.json');verify_files(P,lock['files']);assert lock['saved_before_decisions'];d=pd.read_pickle(P/'projection_data.pkl');saved=pd.read_csv(P/'component.csv.gz').set_index(KEY);checked=values=0
    for a in pd.read_csv(P/'projection_audit.csv').itertuples():
        at=pd.Timestamp(a.cutoff);j=a.offset;complete=d[[f'y_{v}' for v in range(3)]].notna().all(axis=1);weather_at=d[[f'y_at_{v}' for v in range(3)]].max(axis=1);tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&weather_at.lt(at)].copy();assert len(tr)==a.rows and common.keys_hash(tr)==a.training_keys_sha256;assert tr[f'y_at_{j}'].max()<at and tr.forecast_at.max()<at and weather_at.loc[tr.index].max()<at;model=common.read(P/a.model);assert sha(P/a.model)==a.model_sha256;raw,anchor,names=method.design(tr,'component',j);missing=~np.isfinite(raw);median=np.array([np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else 0. for v in raw.T]);filled=np.where(missing,median,raw);mean=filled.mean(0);std=filled.std(0);std=np.where(std<1e-8,1.,std)
        for name,v in [('median',median),('mean',mean),('std',std)]:np.testing.assert_allclose(v,model['transform'][name],atol=1e-10,rtol=1e-10)
        x=np.column_stack([np.ones(len(raw)),(filled-mean)/std,missing.astype(float)]);beta=np.asarray(model['beta']);pen=.01*beta;pen[0]=0;assert max(abs(x.T@(x@beta-(tr[f'y_{j}'].to_numpy(float)-anchor)/6)/len(x)+pen))<1e-7
        end=next((v-1 for v in common.REFITS if v>a.round),38);q=d[d.season.eq(S)&d['round'].between(a.round,end)&(d['round']+j<=38)];v=method.predict_projection(q,'component',model);z=saved.reindex(pd.MultiIndex.from_frame(q[KEY]));np.testing.assert_allclose(v,z[f'xp_{j}'],atol=1e-9,rtol=1e-10);values+=len(q);checked+=1
    assert checked==40;reference=pd.read_csv(P/'operational_fixed.csv.gz').set_index(KEY);history=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=['season','fixture','code','native_minutes','native_goals_scored','native_assists','native_clean_sheets','native_saves','target_total_points','kickoff_time']);history['available']=pd.to_datetime(history.kickoff_time,utc=True)+pd.Timedelta(hours=24);history=history.rename(columns=dict(native_minutes='minutes',native_goals_scored='goals',native_assists='assists',native_clean_sheets='clean',native_saves='saves',target_total_points='points'));history['played']=history.minutes.gt(0).astype(float);history['sixty']=history.minutes.ge(60).astype(float);_,recipe=fixed.recipe();gate,_=fixed.recipe();archive=fixed.load_training_archive();heads=0
    for gw in range(1,39):
        folder=C/S/f'gw{gw:02d}';pool=pd.read_csv(folder/'pool.csv.gz');at=pd.Timestamp(common.read(folder/'manifest.json')['forecast_at']);base=pd.read_csv(folder/(BENCH+'.csv.gz'))
        for j in range(8):
            if f'xp_{j}' not in base:
                assert gw+j>38; base[f'xp_{j}']=0.
        features=fixed.make_features(pool[['code','position','price_tenths']].assign(season=S,round=gw,forecast_at=at).merge(base.drop(columns='forecast_at'),on='code',validate='one_to_one'),history)
        if gw in range(1,39,4):
            bundle=common.read(P/'reference_models'/f'gw{gw:02d}.json');assert pd.Timestamp(bundle['cutoff'])==at
            for pos in ['GK','DEF','MID','FWD']:
                for j in range(8):
                    tr=recipe.training(archive,at,pos,j);a=next(v for v in bundle['audits'] if v['key']==f'{pos}_{j}');assert len(tr)==a['rows'] and tr.forecast_at.max()<at and tr[f'label_at_{j}'].max()<at;model=gate.fit(tr,learned=False);np.testing.assert_allclose(model['beta'],bundle['models'][f'{pos}_{j}']['beta'],rtol=1e-10,atol=1e-10);assert model['theta']==[0.,1.,0.];heads+=1
        pred=fixed.forecast(features,bundle).set_index(KEY);z=reference.reindex(pred.index)
        for j in range(min(8,39-gw)):np.testing.assert_allclose(pred[f'xp_{j}'],z[f'xp_{j}'],atol=1e-9,rtol=1e-10)
    assert heads==320;atomic_json(P/'forecast_verification.json',dict(passed=True,component_projection_fits_replayed=40,reference_heads_replayed=320,component_trajectory_values_replayed=values,causal_training_labels=True,training_only_transforms=True,no_target_weather=True,original_recipes_unchanged=True,production_changed=False));print('CONFIRMATION FORECASTS VERIFIED',flush=True)

def managers():
    verify_files(R,common.read(P/'proposal.json')['input_hashes']);verify_files(P,common.read(P/'prediction_lock.json')['files']);assert common.read(P/'forecast_verification.json')['passed'];env=ConfirmationEnvironment();mod,adapter=backend(16,40);rows=[];stops=[];checked=0
    for arm in ARMS:
        pred=pd.read_csv(P/(arm+'.csv.gz')).set_index(['round','code'])
        for setting in SETTINGS:
            folder=P/'manager'/f'{arm}_{setting}';state=adapter.engine.initial_state()
            if setting=='no_chips':state['used_chips']={h:list(adapter.engine.CHIPS) for h in ['1','2']}
            complete=(folder/'summary.json').exists();rounds=38 if complete else len(list(folder.glob('gw*.settlement.json')));net=hits=0
            if not complete:
                path=P/'logs'/f'{arm}_{setting}.log';trace=path.read_text();assert 'ControlledSolverError: Solver exceeded declared node limit' in trace or 'Unknown selected outcome' in trace;stops.append(dict(arm=arm,setting=setting,completed_rounds=rounds,log=str(path.relative_to(P)),log_sha256=sha(path),reason=trace.splitlines()[-1]))
            assert common.read(folder/'started.json')['forecast_sha256']==sha(P/(arm+'.csv.gz'))
            for gw in range(1,rounds+1):
                decision=common.read(folder/f'gw{gw:02d}.decision.json');saved=common.read(folder/f'gw{gw:02d}.settlement.json');assert not decision['outcomes_read'] and mod.clean(state)==decision['state_before'];pool,_,m,_=env.inputs(S,gw);at=pd.Timestamp(m['forecast_at']);pool=method.qualify(pool,S,at);q=pred.loc[gw].reindex(pool.code);assert q.can_buy.tolist()==pool.can_buy.tolist();assert pd.Timestamp(decision['forecast_at'])==at;xp=q[[f'xp_{j}' for j in range(min(8,39-gw))]].to_numpy(float);assert hashlib.sha256(xp.tobytes()).hexdigest()==decision['forecast_input_sha256'];choice=decision['choice'];choice['prices']={int(k):v for k,v in choice['prices'].items()};state,legal=adapter.engine.apply_decision(state,choice,pool.to_dict('records'),gw);assert mod.clean(state)==decision['state_after'];outcomes,result,n=settle(adapter,env,S,gw,dict(choice=legal),pool);assert outcomes==saved['outcomes'] and mod.clean(result)==saved['settlement'] and n==saved['net'];assert len(decision['solver_calls'])<=40 and all(v['nodes']<=16 and v['full_mip_feasible'] for v in decision['solver_calls'])
                if setting=='no_chips':assert not legal['chip']
                net+=n;hits+=4*legal['paid'];checked+=1
            if complete:
                summary=common.read(folder/'summary.json');assert summary['net']==net and summary['hits']==hits and summary['rounds']==38
            rows.append(dict(arm=arm,setting=setting,net=net if complete else None,hits=hits if complete else None,rounds=rounds,complete=complete));print('CONFIRMATION VERIFIED',arm,setting,net if complete else 'TECHNICAL STOP',flush=True)
    score=pd.DataFrame(rows);score.to_csv(P/'scores.csv',index=False);pairs=[]
    for setting in SETTINGS:
        z=score[score.setting.eq(setting)].set_index('arm');ok=bool(z.complete.all());delta=float(z.loc['component','net']-z.loc['operational_fixed','net']) if ok else None;pairs.append(dict(setting=setting,complete=ok,delta=delta,passed=ok and delta>0))
    atomic_json(P/'manager_verification.json',dict(passed=True,decisions_replayed=checked,full_seasons=int(score.complete.sum()),technical_stops=stops,paired_results=pairs,confirmation_gate_passed=all(v['passed'] for v in pairs),all_saved_settlements_recomputed=True,operational_model_unchanged=True));print('CONFIRMATION GATE',all(v['passed'] for v in pairs),pairs,flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
