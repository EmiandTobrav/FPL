"""Origin-bound direct trajectories and paired historical takeovers.

This is a new direct-mean family, not a relabelling of frozen hurdle H1 models.
No forecast or policy tuning is performed from evaluation results.
"""
import os
for _k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[_k]='1'
import copy
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from model_lab.common import read, sha, atomic_json, verify_files
from model_lab.forecast import pipeline_modules
from model_lab.probability_experiment import features
from model_lab.takeover_inputs import attach_targets, causal_training, copy_takeover_state
from model_lab.simulation import backend, BENCHMARK
from model_lab import manager_policy as mp
from model_lab.manager_learning import Environment, settle

R=Path(__file__).resolve().parents[1]
P=R/'reports/takeover_campaign_2026_10_17'
C=R/'reports/fpl_improvement_2026_10_14/cache'
S=['2023-24','2024-25']
ARMS=['benchmark','trajectory_base','trajectory_full']
MANAGERS=['adaptive','proposal_ranker']
REFITS=[7,15,23,31]
EXTRA=['calendar_known','planned_count','planned_home','planned_away','unassigned','calendar_age',
       'own_gf','own_ga','opp_gf','opp_ga']
PARAMS=dict(iterations=200,depth=5,learning_rate=.05,loss_function='RMSE',random_seed=20261017,
            thread_count=1,verbose=False,allow_writing_files=False)

def context(pool, calendar, strength, gw, at):
    """Compute once per club/offset, then join to ORIGINAL-origin players."""
    if calendar.empty:
        return pd.DataFrame([dict(code=int(p.code),offset=h,calendar_known=0)
            for h in range(min(8,39-gw)) for p in pool.itertuples()]).reindex(columns=['code','offset']+EXTRA)
    for c in ['source_time','event_evidence_at']:
        if c in calendar and not pd.to_datetime(calendar[c],utc=True).lt(at).all():
            raise ValueError('Future/unknown calendar evidence')
    if calendar.fixture_id.duplicated().any(): raise ValueError('Duplicate fixture')
    out=[]
    for club in pool.club_code.unique():
        games=calendar[calendar.home_code.eq(club)|calendar.away_code.eq(club)]
        unknown=int(games.event.isna().sum());known=bool(len(games) and unknown==0)
        age=(at-pd.to_datetime(games.source_time,utc=True).max()).total_seconds()/86400 if len(games) else np.nan
        for h in range(min(8,39-gw)):
            g=games[games.event.eq(gw+h)]
            opp=[r.away_code if r.home_code==club else r.home_code for r in g.itertuples()]
            st=strength.reindex(opp)
            out.append(dict(club_code=club,offset=h,calendar_known=int(known),
                planned_count=len(g) if known else np.nan,
                planned_home=int(g.home_code.eq(club).sum()) if known else np.nan,
                planned_away=int(g.away_code.eq(club).sum()) if known else np.nan,
                unassigned=unknown,calendar_age=age,
                own_gf=strength.gf.get(club,np.nan),own_ga=strength.ga.get(club,np.nan),
                opp_gf=st.gf.mean() if known and len(st) and st.gf.notna().all() else np.nan,
                opp_ga=st.ga.mean() if known and len(st) and st.ga.notna().all() else np.nan))
    return pool[['code','club_code']].merge(pd.DataFrame(out),on='club_code',validate='many_to_many').drop(columns='club_code')

def prepare():
    P.mkdir(exist_ok=True)
    deps=[Path(__file__),R/'model_lab/takeover_inputs.py',R/'model_lab/manager_policy.py',
          R/'model_lab/simulation.py',R/'model_lab/manager_learning.py',
          R/'datasets/fpl_2026_27_best_effort_v1/manifest.json',
          R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',
          R/'datasets/fpl_model_pipeline_v1/operational_proxy_v1.csv.xz',
          R/'datasets/fpl_model_pipeline_v1/schema.json',
          R/'reports/calendar_dataset_2026_10_16/fixture_snapshots.csv.gz',
          R/'reports/calendar_dataset_2026_10_16/player_context.csv.gz',
          R/'reports/takeover_workpackage_2026_10_17/takeover_states.json']
    for s in S:
        for gw in range(1,39):
            d=C/s/f'gw{gw:02d}'
            deps += [d/n for n in ['manifest.json','pool.csv.gz','features.csv.gz',BENCHMARK+'.csv.gz']]
    spec=dict(id='takeover-trajectories-20261017-v1',candidate_id='direct_trajectories_takeover_v1',
        hypothesis='Origin-bound future-round direct means improve realised takeover points versus the frozen benchmark.',
        change='New pooled-offset direct CatBoost base/full trajectories H1-H8; six forecast/manager combinations with H8 inputs; 16 fixed states through GW38.',
        related_work=['point-context-20261016-v1','season-manager-20261015-v1'],
        dataset_id='fpl_2026_27_best_effort_v1',benchmark_id=BENCHMARK,clock='operational_proxy_v1',
        features='extended numeric + position onehot + offset; full adds target schedule and origin team strength',
        input_hashes={str(p.relative_to(R)):sha(p) for p in deps},seasons=S,model_parameters=PARAMS,
        decision_policy=dict(managers=MANAGERS,forecast_arms=ARMS,horizon=8,refits=REFITS,
                             states='all16 frozen states',node_limit=16,max_calls=40),
        resources=dict(maximum_fits=16,maximum_episodes=96,threads_per_model=1,episode_workers=4,no_tuning=True),
        maximum_runs=1,
        success_criterion='Each candidate combination must beat benchmark+adaptive mean paired net points in EACH season; forecast MSE separately reported by season/offset. No automatic promotion.',
        stop_rule='Stop on causal/hash/illegal decision/unknown selected outcome/budget failure; preserve failure, no blind retries.',
        evaluation_contract=dict(target='Harmonized actual points in the concrete target round, including zero and negatives; missing stays missing.',
            train='Same rows base/full. Earlier origin AND target availability strictly before refit. Pooled offsets0..7, original-origin features only. No future minute inputs. History from2020 onward; unavailable early calendar remains unknown.',
            inference='Direct unconditional mean, unclipped. Original frozen H1 untouched. New trajectory H1 is NOT the archived hurdle H1.',
            manager='All six arms receive H8 forecasts; existing managers retain their native local H3 planning, frozen prices within planning, observed prices at each actual next origin; decisions saved before outcome settlement.',
            evidence_role='Previously inspected historical development seasons, correlated start states; no untouched-test or top1-percent claim.',
            intervals='Descriptive paired deltas only;16 overlapping states are not16 independent seasons.'))
    atomic_json(P/'proposal.json',spec)

def build():
    verify_files(R,read(P/'proposal.json')['input_hashes'])
    rows,schema=pipeline_modules()[0].load_rows();rows=rows[rows.season.le(S[-1])].copy()
    labels=rows[['season','round','code','target_total_points','target_h1_available_at']]
    cols=[c for c in schema['extended_features'] if c not in schema['categorical_features']]
    cal=pd.read_csv(R/'reports/calendar_dataset_2026_10_16/fixture_snapshots.csv.gz')
    players=pd.read_csv(R/'reports/calendar_dataset_2026_10_16/player_context.csv.gz')
    matches=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=['season','fixture','club_code','was_home','team_h_score','team_a_score','fixture_kickoff_time']).drop_duplicates(['season','fixture','club_code'])
    matches['available']=pd.to_datetime(matches.fixture_kickoff_time,utc=True)+pd.Timedelta(hours=24)
    matches['gf']=np.where(matches.was_home,matches.team_h_score,matches.team_a_score)
    matches['ga']=np.where(matches.was_home,matches.team_a_score,matches.team_h_score)
    frames=[];audits=[]
    for (s,gw),q in rows.groupby(['season','round'],sort=True):
        at=q.forecast_at.iloc[0];assert q.forecast_at.eq(at).all()
        if s in S:
            d=C/s/f'gw{gw:02d}';f=pd.read_csv(d/'features.csv.gz')
            # Archived inference pools include held players missing from label rows.
            assert pd.to_datetime(f.forecast_at,utc=True).eq(at).all()
        else:f=q
        x=features(f,cols);x['code']=f.code.to_numpy();x['season']=s;x['origin_round']=gw;x['forecast_at']=at
        pc=players[players.season.eq(s)&players['round'].eq(gw)][['code','club_code']]
        pool=f[['code']].merge(pc,on='code',how='left',validate='one_to_one')
        hist=matches[matches.available.lt(at)&matches.gf.notna()&matches.ga.notna()].sort_values(['available','season','fixture']).groupby('club_code').tail(6)
        st=hist.groupby('club_code')[['gf','ga']].mean()
        ctx=context(pool,cal[cal.season.eq(s)&cal['round'].eq(gw)],st,gw,at)
        z=x.merge(ctx,on='code',validate='one_to_many');z['target_round']=gw+z.offset
        z=attach_targets(z,labels);frames.append(z)
        audits.append(dict(season=s,round=int(gw),rows=len(z),forecast_at=str(at),strength_max=str(hist.available.max())))
    data=pd.concat(frames,ignore_index=True)
    data.to_pickle(P/'training.pkl')
    atomic_json(P/'data_lock.json',dict(sha256=sha(P/'training.pkl'),base_features=list(features(rows.iloc[:1],cols).columns)+['offset'],audits=audits,rows=len(data)))
    print('DATA',len(data),flush=True)

def forecasts():
    from catboost import CatBoostRegressor
    verify_files(R,read(P/'proposal.json')['input_hashes'])
    lock=read(P/'data_lock.json');assert sha(P/'training.pkl')==lock['sha256']
    data=pd.read_pickle(P/'training.pkl');fits=0;outputs={}
    for s in S:
        models={}
        for gw in range(7,39):
            at=pd.Timestamp(read(C/s/f'gw{gw:02d}'/'manifest.json')['forecast_at'])
            if gw in REFITS:
                train=causal_training(data,at)
                assert train.forecast_at.max()<at and pd.to_datetime(train.label_available_at,utc=True).max()<at
                for arm in ARMS[1:]:
                    names=lock['base_features']+([] if arm=='trajectory_base' else EXTRA)
                    t=time.monotonic();model=CatBoostRegressor(**PARAMS)
                    model.fit(train[names],train.target_total_points)
                    model.save_model(str(P/f'{s}_{gw:02d}_{arm}.cbm'));models[arm]=(model,names);fits+=1
                    atomic_json(P/f'{s}_{gw:02d}_{arm}.fit.json',dict(rows=len(train),cutoff=str(at),
                        latest_origin=str(train.forecast_at.max()),latest_label=str(train.label_available_at.max()),
                        seconds=time.monotonic()-t,features=names,training_keys_sha256=__import__('hashlib').sha256(train[['season','origin_round','target_round','code']].to_csv(index=False).encode()).hexdigest()))
                    print('FIT',s,gw,arm,len(train),round(time.monotonic()-t,1),flush=True)
            q=data[data.season.eq(s)&data.origin_round.eq(gw)].copy()
            result=q[['season','origin_round','target_round','code','offset','forecast_at']].copy()
            for arm,(model,names) in models.items():result[arm]=model.predict(q[names])
            assert np.isfinite(result[ARMS[1:]].to_numpy()).all()
            p=P/f'{s}_gw{gw:02d}.csv.gz';result.to_csv(p,index=False);outputs[p.name]=sha(p)
    assert fits==16
    atomic_json(P/'forecast_lock.json',dict(fits=fits,outputs=outputs))

def episode(task):
    item,arm,manager=task
    env=Environment();s=item['season'];start=item['round'];state=copy_takeover_state(item['state'],start)
    name=item['id']+'__'+arm+'__'+manager;folder=P/'episodes'/name;folder.mkdir(parents=True,exist_ok=False)
    lock=read(P/'forecast_lock.json');logs=[];began=time.monotonic()
    try:
        for gw in range(start,39):
            pool,bxp,manifest,history=env.inputs(s,gw)
            if arm=='benchmark':xp=bxp[:,:min(8,39-gw)]
            else:
                p=P/f'{s}_gw{gw:02d}.csv.gz';assert sha(p)==lock['outputs'][p.name]
                pred=pd.read_csv(p);xp=pred.pivot(index='code',columns='offset',values=arm).loc[pool.code,list(range(min(8,39-gw)))].to_numpy()
            mod,a=backend(16,40)
            if manager=='adaptive':choice=a.decide(pool,xp,state,gw)['choice']
            else:
                options=mp.proposals(a,pool,xp,history,state,gw);choice=options[mp.select(options,None)[0]]['choice']
            choice=copy.deepcopy(choice)
            if 'prices' in choice:choice['prices']={int(k):v for k,v in choice['prices'].items()}
            after,choice=a.engine.apply_decision(state,choice,pool.to_dict('records'),gw)
            decision=dict(state_before=state,state_after=after,choice=choice,forecast_at=manifest['forecast_at'],
                forecast_sha256=__import__('hashlib').sha256(xp.tobytes()).hexdigest(),outcomes_read=False,solver_calls=a.ledger)
            atomic_json(folder/f'gw{gw:02d}.decision.json',mod.clean(decision))
            outcomes,settlement,net=settle(a,env,s,gw,dict(choice=choice),pool)
            record=dict(round=gw,net=net,hits=4*choice['paid'],chip=choice['chip'],outcomes=outcomes,settlement=settlement)
            atomic_json(folder/f'gw{gw:02d}.settlement.json',mod.clean(record));logs.append(record);state=after
        result=dict(state_id=item['id'],season=s,start=start,forecast=arm,manager=manager,
            net_points=sum(z['net'] for z in logs),hits=sum(z['hits'] for z in logs),rounds=len(logs),seconds=time.monotonic()-began)
        atomic_json(folder/'summary.json',result);print('EPISODE',name,result['net_points'],round(result['seconds'],1),flush=True)
        return result
    except Exception as e:
        atomic_json(folder/'failure.json',dict(error=repr(e),completed_rounds=len(logs)));raise

def simulations():
    from concurrent.futures import ProcessPoolExecutor
    verify_files(R,read(P/'proposal.json')['input_hashes'])
    states=read(R/'reports/takeover_workpackage_2026_10_17/takeover_states.json')
    tasks=[(s,a,m) for s in states for a in ARMS for m in MANAGERS]
    assert len(tasks)==96
    with ProcessPoolExecutor(max_workers=4) as executor:results=list(executor.map(episode,tasks))
    pd.DataFrame(results).to_csv(P/'episodes.csv',index=False)
    print('SIMULATIONS COMPLETE',len(results),flush=True)

def report():
    q=pd.read_csv(P/'episodes.csv');assert len(q)==96
    ref=q[q.forecast.eq('benchmark')&q.manager.eq('adaptive')][['state_id','net_points']].rename(columns={'net_points':'reference'})
    q=q.merge(ref,on='state_id',validate='many_to_one');q['delta']=q.net_points-q.reference
    q.to_csv(P/'paired_results.csv',index=False)
    summary=q.groupby(['season','forecast','manager']).agg(mean_points=('net_points','mean'),mean_delta=('delta','mean'),minimum_delta=('delta','min'),maximum_delta=('delta','max'),wins=('delta',lambda x:int((x>0).sum())),states=('delta','size')).reset_index()
    summary.to_csv(P/'summary.csv',index=False)
    print(summary.to_string(index=False),flush=True)
    atomic_json(P/'complete.json',dict(status='completed',episodes=len(q),decisions=int(q['rounds'].sum()),model_fits=16,production_promoted=False,rank_claim=False))

if __name__=='__main__':globals()[sys.argv[1]]()
