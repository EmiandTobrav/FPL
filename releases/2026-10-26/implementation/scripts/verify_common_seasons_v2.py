"""Completion v2: audit partial technical stops without retrying or scoring them as full seasons.
Original projection verifier is unchanged; all original model/manager settings remain frozen.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.common_season_comparison import *

def forecasts(group='causal'):
    assert group in ['causal','weather'];verify_files(R,common.read(P/'proposal.json')['input_hashes'])
    root=P/('weather_base' if group=='weather' else 'base');lock=common.read(root/'lock.json');assert sha(root/'predictions.pkl')==lock['sha256'];verify_files(R,lock['source_model_hashes'])
    d=pd.read_pickle(P/'pool_features.pkl').merge(pd.read_pickle(root/'predictions.pkl'),on=KEY+['forecast_at'],validate='one_to_one');sealed=common.read(P/f'{group}_prediction_lock.json');verify_files(P,sealed['files']);assert sealed['saved_before_decisions']
    audit=pd.read_csv(P/f'{group}_projection_audit.csv');checked=values=0;cohorts={};predictions={}
    for a in audit.itertuples():
        at=pd.Timestamp(a.cutoff);complete=d[[f'y_{v}' for v in range(3)]].notna().all(axis=1);weather_at=d[[f'y_at_{v}' for v in range(3)]].max(axis=1)
        tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{a.offset}'].notna()&d[f'y_at_{a.offset}'].lt(at)&complete&weather_at.lt(at)].copy();assert len(tr)==a.rows>=1000 and common.keys_hash(tr)==a.training_keys_sha256
        k=(a.season,a.round,a.offset)
        if k in cohorts:assert cohorts[k]==a.training_keys_sha256
        cohorts[k]=a.training_keys_sha256;assert tr.forecast_at.max()<at and tr[f'y_at_{a.offset}'].max()<at and weather_at.loc[tr.index].max()<at
        path=P/a.model;assert sha(path)==a.model_sha256;model=common.read(path);raw,anchor,names=design(tr,a.base,a.offset);missing=~np.isfinite(raw);med=np.array([np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else 0. for v in raw.T]);filled=np.where(missing,med,raw);mean=filled.mean(0);std=filled.std(0);std=np.where(std<1e-8,1.,std)
        for n,v in [('median',med),('mean',mean),('std',std)]:np.testing.assert_allclose(v,model['transform'][n],rtol=1e-10,atol=1e-10)
        x=np.column_stack([np.ones(len(raw)),(filled-mean)/std,missing.astype(float)]);beta=np.asarray(model['beta']);pen=.01*beta;pen[0]=0;gradient=x.T@(x@beta-(tr[f'y_{a.offset}'].to_numpy(float)-anchor)/6)/len(x)+pen;assert np.max(np.abs(gradient))<1e-7;checked+=1
        for arm in WEATHER if group=='weather' else [a.base]:
            key=(a.season,arm)
            if key not in predictions:predictions[key]=pd.read_csv(P/'trajectories'/f'{a.season}_{arm}.csv.gz').set_index(KEY)
            end=next((v-1 for v in REFITS if v>a.round),38);q=d[d.season.eq(a.season)&d['round'].between(a.round,end)&(d['round']+a.offset<=38)].sort_values(KEY);saved=predictions[key].reindex(pd.MultiIndex.from_frame(q[KEY]));p=predict_projection(q,arm,model);np.testing.assert_allclose(p,saved[f'xp_{a.offset}'],rtol=1e-10,atol=1e-9);values+=len(q)
    assert checked==(80 if group=='weather' else 1440);atomic_json(P/f'{group}_forecast_verification.json',dict(passed=True,fits_replayed=checked,forecast_values_replayed=values,common_teacher_cohorts=True,past_only_labels_and_H3_weather=True,training_only_transforms=True,separate_future_offset_heads=True,production_changed=False));print('PROJECTIONS VERIFIED',group,checked,values,flush=True)

def managers():
    verify_files(R,common.read(P/'proposal.json')['input_hashes'])
    for group in ['causal','weather']:assert common.read(P/f'{group}_forecast_verification.json')['passed']
    env=Environment();mod,adapter=backend(16,40);rows=[];chips=[];checked=0;stops=[];completed=0
    for season in EVAL:
        for arm in ARMS+CONTROLS+WEATHER:
            group='weather' if arm in WEATHER else 'reference' if arm in CONTROLS else 'causal';lock=common.read(P/f'{group}_prediction_lock.json');verify_files(P,lock['files']);path=P/'trajectories'/f'{season}_{arm}.csv.gz';pred=pd.read_csv(path).set_index(['round','code']);folder=P/'manager'/f'{season}_{arm}';assert common.read(folder/'started.json')['forecast_sha256']==sha(path);state=adapter.engine.initial_state();net=hits=calls=0
            is_complete=(folder/'summary.json').exists();rounds=38 if is_complete else len(list(folder.glob('gw*.settlement.json')))
            if not is_complete:
                log=P/'logs'/f'manager_{season}_{arm}.log';trace=log.read_text();assert 'ControlledSolverError: Solver exceeded declared node limit' in trace;stops.append(dict(season=season,arm=arm,completed_rounds=rounds,status='technical_stop_resource_cap',reason='Native solver exceeded common declared node limit; no retry or changed cap',log=str(log.relative_to(P)),log_sha256=sha(log)))
            for gw in range(1,rounds+1):
                decision=common.read(folder/f'gw{gw:02d}.decision.json');saved=common.read(folder/f'gw{gw:02d}.settlement.json');assert not decision['outcomes_read'] and mod.clean(state)==decision['state_before'];pool,_,manifest,_=env.inputs(season,gw);at=inputs.EARLY if (season,gw)==('2024-25',15) else pd.Timestamp(manifest['forecast_at']);pool=qualify(pool,season,at);q=pred.loc[gw].reindex(pool.code);assert pd.to_datetime(q.forecast_at,utc=True).eq(at).all() and pd.Timestamp(decision['forecast_at'])==at;assert q.can_buy.tolist()==pool.can_buy.tolist()
                for c in ['price_available_at','position_available_at','club_available_at']:assert pd.to_datetime(pool[c],utc=True).lt(at).all()
                xp=q[[f'xp_{j}' for j in range(min(8,39-gw))]].to_numpy(float);assert hashlib.sha256(xp.tobytes()).hexdigest()==decision['forecast_input_sha256'];choice=decision['choice'];choice['prices']={int(k):v for k,v in choice['prices'].items()};state,legal=adapter.engine.apply_decision(state,choice,pool.to_dict('records'),gw);assert mod.clean(state)==decision['state_after'];outcomes,settlement,n=settle(adapter,env,season,gw,dict(choice=legal),pool);assert n==saved['net'] and mod.clean(settlement)==saved['settlement'] and outcomes==saved['outcomes'];assert len(decision['solver_calls'])<=40 and all(v['nodes']<=16 and v['full_mip_feasible'] for v in decision['solver_calls']);checked+=1;net+=n;hits+=4*legal['paid'];calls+=len(decision['solver_calls'])
                if legal['chip']:chips.append(dict(season=season,arm=arm,round=gw,chip=legal['chip']))
            if is_complete:
                summary=common.read(folder/'summary.json');assert summary['net']==net and summary['hits']==hits and summary['rounds']==38;completed+=1
            rows.append(dict(season=season,arm=arm,net=net if is_complete else np.nan,hits=hits if is_complete else np.nan,solver_calls=calls,completed_rounds=rounds,status='complete' if is_complete else 'technical_stop_resource_cap',information_tier='hindsight_weather_proxy' if arm in WEATHER else 'predeadline_proxy'));print('VERIFIED SEASON',season,arm,net if is_complete else 'TECHNICAL STOP',flush=True)
    assert completed+len(stops)==46 and checked==completed*38+sum(v['completed_rounds'] for v in stops);pd.DataFrame(rows).to_csv(P/'scores.csv',index=False);pd.DataFrame(chips).to_csv(P/'chips.csv',index=False);scores=pd.DataFrame(rows).pivot(index='arm',columns='season',values='net');gates=[]
    for arm in ARMS:
        delta={s:{c:float(scores.loc[arm,s]-scores.loc[c,s]) if pd.notna(scores.loc[arm,s]) and pd.notna(scores.loc[c,s]) else None for c in CONTROLS} for s in EVAL};gates.append(dict(arm=arm,passed=all(v is not None and v>0 for q in delta.values() for v in q.values()),deltas=delta))
    atomic_json(P/'manager_verification.json',dict(passed=True,decisions_replayed=checked,full_seasons=completed,attempted_seasons=46,technical_stops=stops,all_settlements_recomputed=True,budget_rules_autosubs_captain_chips_hits_checked=True,same_policy_pool_prices_and_resources=True,utility_gates=gates,production_changed=False));print('ALL SEASONS VERIFIED',checked,flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
