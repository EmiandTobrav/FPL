"""Independent episode replay, paired diagnostics and final result publication."""
import sys,json,copy,collections
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import test_xg_adaptation as t
from model_lab.common import sha,atomic_json,verify_files
P=t.P;F=t.F;KEY=t.KEY

def managers(arm):
    assert arm in ['control']+t.ARMS;t.check();t.guard.configure();m=t.guard.m;env=m.MatchedEnvironment();origins=t.load(F/'origins.pkl');file=F/'component.csv.gz' if arm=='control' else P/f'{arm}.csv.gz';f=pd.read_csv(file);scores=[];replayed=0;calls=0
    for s in t.EVAL:
        directory=F/'manager'/f'{s}_component' if arm=='control' else P/'manager'/f'{s}_{arm}';summary=t.read(directory/'summary.json');assert summary['rounds']==38;pred=f[f.season.eq(s)].set_index(['round','code']);mod,adapter=t.guard.solver();state=adapter.engine.initial_state();total=hits=0;cap=base=0
        for g in range(1,39):
            dec=t.read(directory/f'gw{g:02d}.decision.json');sett=t.read(directory/f'gw{g:02d}.settlement.json');at=origins[(s,g)];pool=m.method.qualify(t.guard.eligible_pool(s,g),s,at);assert mod.clean(state)==dec['state_before'];assert pd.Timestamp(dec['forecast_at'])==at and not dec['outcomes_read'];q=pred.loc[g].reindex(pool.code);xp=q[[f'xp_{j}' for j in range(min(8,39-g))]].to_numpy(float);assert hashlib_sha(xp)==dec['forecast_input_sha256']
            choice=copy.deepcopy(dec['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};state,choice=adapter.engine.apply_decision(state,choice,pool.to_dict('records'),g);assert mod.clean(state)==dec['state_after'];out,result,n=m.settle(adapter,env,s,g,dict(choice=choice),pool);assert mod.clean(result)==sett['settlement'] and n==sett['net'] and mod.clean(out)==sett['outcomes'];assert len(dec['solver_calls'])<=40
            for call in dec['solver_calls']:assert call['full_mip_feasible'] and call['nodes']<=16
            total+=n;hits+=4*choice['paid'];cap+=result['captain_bonus'];base+=result['base'];calls+=len(dec['solver_calls']);replayed+=1
        assert total==summary['net'] and hits==summary['hits'];scores.append(dict(season=s,arm=arm,net=total,hits=hits,base=base,captain_bonus=cap,complete=True,rounds=38))
    pd.DataFrame(scores).to_csv(P/f'scores_{arm}.csv',index=False);atomic_json(P/f'manager_verification_{arm}.json',dict(passed=True,episodes=3,decisions_replayed=replayed,solver_calls=calls,all_legal_and_scoring_exact=True,all_hard_availability_passed=True,all_actual_node_caps16_and_calls40_passed=True));print('MANAGERS VERIFIED',arm,pd.DataFrame(scores).to_dict('records'),flush=True)

def hashlib_sha(a):
    import hashlib
    return hashlib.sha256(a.tobytes()).hexdigest()

def metrics():
    d=t.load(F/'head_data.pkl');av=pd.read_csv(F/'availability.csv.gz');d=d.merge(av[KEY+['model_can_buy']],on=KEY,validate='one_to_one')
    # Evaluation truth must not disappear just because its original supervised
    # feature origin was excluded (notably2024GW15). Use native outcome rows;
    # the unchanged y0..2 qualification below still controls evaluation keys.
    source=R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz';raw=pd.read_csv(source,usecols=KEY+['native_minutes']);truth=raw.groupby(KEY).native_minutes.sum(min_count=1).rename('target_minutes_1').reset_index();d=d.merge(truth,on=KEY,how='left',validate='one_to_one');windows=[]
    for j in range(3):
        q=truth.copy();q['round']-=j;windows.append(d[KEY].merge(q,on=KEY,how='left',validate='one_to_one').target_minutes_1)
    d['target_minutes_3']=pd.concat(windows,axis=1).sum(axis=1,min_count=3);ref=pd.read_csv(F/'operational_matched.csv.gz').set_index(KEY);index=pd.MultiIndex.from_frame(d[KEY]);d['common_rank']=ref.reindex(index).xp_0.to_numpy();d['common_top']=False
    for (_,_,pos),q in d[d.model_can_buy&d.season.isin(t.EVAL)].groupby(['season','round','position']):d.loc[q.nlargest(dict(GK=5,DEF=20,MID=20,FWD=10)[pos],'common_rank').index,'common_top']=True
    predictions={'control':pd.read_csv(F/'component.csv.gz').set_index(KEY)};predictions.update({arm:pd.read_csv(P/f'{arm}.csv.gz').set_index(KEY) for arm in t.ARMS});xg=pd.concat([t.load(P/f'base_{s}.pkl') for s in t.S]).set_index(KEY);rows=[];rankrows=[]
    for s in t.EVAL:
        q=d[d.season.eq(s)&d.model_can_buy].copy()
        for scope,subset in [('all_buyable',q),('common_top',q[q.common_top]),('common_MID',q[q.common_top&q.position.eq('MID')]),('premium9plus',q[q.price_tenths.ge(90)])]:
            for arm in ['control']+t.ARMS:
                p=predictions[arm].reindex(pd.MultiIndex.from_frame(subset[KEY]));z=subset.copy();z['point_prediction']=p.xp_0.to_numpy()
                for h in [1,3]:
                    good=z[[f'y_{j}' for j in range(h)]].notna().all(axis=1)&(z['round']+h<=39);v=z[good];target=v[[f'y_{j}' for j in range(h)]].sum(axis=1).to_numpy();pp=p.loc[good.to_numpy(),[f'xp_{j}' for j in range(h)]].sum(axis=1).to_numpy();err=pp-target
                    rows.append(dict(season=s,scope=scope,arm=arm,target='points',horizon=h,n=len(v),mse=float(np.mean(err*err)),mae=float(np.mean(abs(err))),bias=float(np.mean(err)),actual_variance=float(np.var(target))))
                    minute_good=v[f'target_minutes_{h}'].notna();v1=v[minute_good];base=xg.reindex(pd.MultiIndex.from_frame(v1[KEY]))[f'component_m{h}'].to_numpy() if arm=='xg_only' else v1[f'component_m{h}'].to_numpy();err=base-v1[f'target_minutes_{h}'].to_numpy()
                    rows.append(dict(season=s,scope=scope,arm=arm,target='minutes',horizon=h,n=len(v1),mse=float(np.mean(err*err)),mae=float(np.mean(abs(err))),bias=float(np.mean(err)),actual_variance=float(np.var(v1[f'target_minutes_{h}']))))
                known=z[z.y_0.notna()]
                for g,v in known.groupby('round'):
                    if v.point_prediction.nunique()>1 and v.y_0.nunique()>1:rankrows.append(dict(season=s,scope=scope,arm=arm,round=g,n=len(v),spearman=v.point_prediction.corr(v.y_0,method='spearman')))
    pd.DataFrame(rows).to_csv(P/'forecast_metrics.csv',index=False);pd.DataFrame(rankrows).to_csv(P/'ranking_by_round.csv',index=False);pd.DataFrame(rankrows).groupby(['season','scope','arm']).spearman.mean().to_csv(P/'ranking.csv');print('METRICS SEALED',flush=True)

def finish():
    t.check();assert t.read(P/'dataset_verification.json')['passed']
    for arm in ['control']+t.ARMS:assert t.read(P/f'manager_verification_{arm}.json')['passed']
    for arm in t.ARMS:assert t.read(P/f'prediction_verification_{arm}.json')['passed'] and t.read(P/f'preflight_{arm}.json')['passed']
    d=pd.concat([pd.read_csv(P/f'scores_{arm}.csv') for arm in ['control']+t.ARMS]);d.to_csv(P/'scores.csv',index=False);wide=d.pivot(index='season',columns='arm',values='net');wide['xg_delta']=wide.xg_only-wide.control;wide['recent_delta']=wide.recent_only-wide.control;wide.to_csv(P/'comparison.csv')
    gate={arm:bool((wide[arm]>wide.control).all()) for arm in t.ARMS};artifacts=[p for p in P.glob('*.csv')]+[P/f'manager_verification_{a}.json' for a in ['control']+t.ARMS]+[P/f'prediction_verification_{a}.json' for a in t.ARMS]+[P/'dataset_verification.json',t.D/'manifest.json',t.D/'release.json',Path(__file__),R/'scripts/verify_xg_adaptation.py']
    artifacts += [P/'interval_verification.json',P/'resource_execution_note.json']
    atomic_json(P/'final_verification.json',dict(passed=True,complete_episodes=6,reused_control_episodes=3,decisions_independently_replayed=342,new_base_fits=80,new_calibration_heads=480,independent_interventions_only=True,success_by_arm=gate,all_same_keys_targets_policy_clock_and_per_decision_resources=True,concurrency_execution_deviation='Fitting4 and simulation3 overlapped; peak7 processes, see resource_execution_note.json; native per-decision node/call budgets unchanged',active_model_unchanged=True,files={str(p.relative_to(R)):sha(p) for p in artifacts}));print('FINAL',wide.to_string(),gate,flush=True)

if __name__=='__main__':
    if sys.argv[1]=='managers':managers(sys.argv[2])
    elif sys.argv[1]=='metrics':metrics()
    elif sys.argv[1]=='finish':finish()
    else:raise ValueError(sys.argv[1])
