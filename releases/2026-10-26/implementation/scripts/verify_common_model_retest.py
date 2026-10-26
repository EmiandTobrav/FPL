"""Independent accounting and replay checks for the common-data comparison."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,pickle,hashlib
from pathlib import Path
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json,verify_files
from scripts import common_model_retest as run
D=run.D;P=run.P;KEY=run.KEY

def table():
    manifest=run.read(D/'manifest.json');verify_files(R,manifest['input_hashes']);verify_files(D,manifest['files'])
    schema=run.read(D/'schema.json');d=pd.read_pickle(D/'training.pkl');assert len(d)==manifest['rows'];assert not d.duplicated(KEY).any()
    assert len(schema['features'])==len(set(schema['features']))
    assert not any(c.startswith(('target_','weather_')) or c in ['price_tenths','position','club_code','pr_last_club_differs'] for c in schema['features'])
    assert set(schema['features'])==set(sum(schema['feature_groups'].values(),[]))
    assert not (d.excluded_origin&d.train_eligible).any()
    assert not (d.season.eq('2026-27')&(d.train_eligible|d.eval_eligible)).any()
    t=pd.read_csv(D/'history_timing_audit.csv.gz');at=pd.to_datetime(t.forecast_at,utc=True);latest=pd.to_datetime(t.latest_history_available,utc=True)
    assert (latest.isna()|latest.lt(at)).all()
    original=pd.read_csv(run.MASTER,usecols=KEY+['fixture','native_minutes','native_starts','target_total_points','history_eligible','observation_available_after_proxy','native_goals_scored','native_assists','native_clean_sheets','saves','position','value','fixture_kickoff_time','weather_temperature_2m_mean','weather_wind_speed_10m_mean','weather_precipitation_sum','weather_sunshine_minutes_daylight_capped'],low_memory=False)
    original['available']=pd.to_datetime(original.observation_available_after_proxy,utc=True)
    agg=original.groupby(KEY).agg(points=('target_total_points',lambda a:a.sum(min_count=len(a))),minutes=('native_minutes',lambda a:a.sum(min_count=len(a))),eligible=('history_eligible','all')).reset_index()
    check=d[KEY+['target_points_1','target_minutes_1','target_history_eligible']].merge(agg,on=KEY,validate='one_to_one')
    np.testing.assert_allclose(check.target_points_1,check.points,equal_nan=True);np.testing.assert_allclose(check.target_minutes_1,check.minutes,equal_nan=True);assert check.target_history_eligible.eq(check.eligible).all()
    label=d.set_index(KEY)
    samples=d.sample(200,random_state=20261025)
    for row in samples.itertuples():
        past=original[original.code.eq(row.code)&original.history_eligible&original.available.lt(row.forecast_at)].sort_values(['available','fixture'])
        cur=past[past.season.eq(row.season)];old=past[past.season.lt(row.season)]
        if len(old):old=old[old.season.eq(old.season.max())]
        assert row.h_cur_count==len(cur) and row.h_old_count==len(old)
        for tag,q in [('cur',cur),('old',old)]:
            for w in [3,10]:
                for field,source in {'minutes':'native_minutes','points':'target_total_points','goals':'native_goals_scored','assists':'native_assists','clean':'native_clean_sheets','starts':'native_starts','saves':'saves'}.items():
                    np.testing.assert_allclose(getattr(row,f'h_{tag}_{w}_{field}'),q[source].tail(w).mean(),rtol=2e-6,atol=2e-6,equal_nan=True)
        np.testing.assert_allclose(row.lag_weather_temperature,past.weather_temperature_2m_mean.tail(3).mean(),rtol=2e-6,atol=2e-6,equal_nan=True)
        future=[]
        for j in range(3):
            key=(row.season,row.round+j,row.code)
            if key not in label.index or not label.loc[key,'target_history_eligible']:future=[];break
            future.append(label.loc[key,'target_points_1'])
        expected=sum(future) if len(future)==3 else np.nan
        np.testing.assert_allclose(row.target_points_3,expected,equal_nan=True)
        # Mutation principle: only the strict past is accessed by the independent
        # feature reconstruction; future changes cannot enter its input slice.
        assert not past.available.ge(row.forecast_at).any()
    for folder,prefix,latestcols in [('fpl_all_competitions_context_v1','wl_',['wl_latest_input_available_at','wl_international_latest_input_available_at','cal_pl_source_time']),('fpl_availability_all_seasons_v1','av_',['av_snapshot_at_proxy']),('fpl_set_piece_roles_v1','sp_',[]),('fpl_role_strength_v1','pr_',['pr_history_latest_available'])]:
        name='player_round_role_context.csv.xz' if prefix=='pr_' else 'player_round_context.csv.xz'
        c=pd.read_csv(R/'datasets'/folder/name,low_memory=False);c=c.merge(d[KEY+['forecast_at','excluded_origin']],on=KEY,validate='one_to_one');c=c[~c.excluded_origin]
        for col in latestcols:
            v=pd.to_datetime(c[col],utc=True,format='mixed');assert (v.isna()|v.lt(c.forecast_at)).all(),(folder,col)
    result=dict(passed=True,rows=len(d),features=len(schema['features']),unique_row_keys=True,master_H1_targets_recomputed=len(check),independent_history_and_H3_samples=len(samples),strict_past_history_all_rows=True,context_source_timestamps_checked=True,known_late_origins_excluded=True,current_season_not_used_for_fit_or_score=True,retrospective_target_weather_excluded=True,complete_purchase_roster_claimed=False)
    atomic_json(D/'verification.json',result);print(json.dumps(result,indent=2),flush=True)

def models():
    spec=run.read(P/'proposal.json');verify_files(R,spec['input_hashes']);d=pd.read_pickle(D/'training.pkl');audit=pd.read_csv(P/'fit_audit.csv');assert len(audit)==40*len(run.ARMS)
    for (s,h,gw),q in audit.groupby(['season','horizon','refit_round']):
        assert q.training_keys_sha256.nunique()==1 and q.prediction_keys_sha256.nunique()==1
        at=pd.Timestamp(q.cutoff.iloc[0]);tr=d[d.train_eligible&d.forecast_at.lt(at)&d[f'label_at_{h}'].lt(at)].copy()
        targets=[f'target_{t}_{h}' for t in ['points','minutes','starts','attack','appearance','residual']];tr=tr[tr[targets].notna().all(axis=1)]
        assert run.keys_hash(tr)==q.training_keys_sha256.iloc[0]
        te=d[d.season.eq(s)&d['round'].between(gw,min(gw+7,38))&~d.excluded_origin].copy();assert run.keys_hash(te)==q.prediction_keys_sha256.iloc[0]
        folder=P/'folds'/f'{s}_h{h}_gw{gw:02d}';verify_files(folder,run.read(folder/'lock.json')['predictions'])
        cache={}
        for row in q.itertuples():
            saved=pd.read_csv(folder/(row.arm+'.csv.gz'));assert len(saved)==len(te)
            assert saved.row_id.tolist()==te.row_id.tolist()
            if row.arm=='ridge_extra_50':v=(cache['ridge']+cache['extra_trees'])/2
            else:
                path=folder/(row.arm+'.pkl');assert sha(path)==row.model_sha256
                with path.open('rb') as f:bundle=pickle.load(f)
                # Full prediction replay, including probability mixtures.
                v,prob,distribution=run.predict_arm(bundle,te)
                if prob is not None:np.testing.assert_allclose(prob,saved.p_play,rtol=1e-10,atol=1e-10);assert ((prob>=0)&(prob<=1)).all()
                if distribution is not None:np.testing.assert_allclose(distribution.sum(1),1,atol=1e-10)
                # Compare trained median vector to independently calculated past data.
                a=tr[bundle['columns']].to_numpy(float)
                with np.errstate(all='ignore'):
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore',RuntimeWarning);median=np.nanmedian(a,axis=0)
                median=np.nan_to_num(median,nan=0.)
                np.testing.assert_allclose(bundle['imputer'].statistics_,median,atol=1e-10,rtol=1e-10)
            np.testing.assert_allclose(v,saved[['predicted_points','predicted_minutes']].to_numpy(),rtol=1e-9,atol=1e-9);cache[row.arm]=v
        print('VERIFIED',s,h,gw,flush=True)
    metric=pd.read_csv(P/'metrics.csv');allrows=run.collect()
    for row in metric[metric.scope.eq('all')].itertuples():
        q=allrows[allrows.season.eq(row.season)&allrows.horizon.eq(row.horizon)&allrows.arm.eq(row.arm)&allrows.eval_eligible].dropna(subset=[f'target_points_{row.horizon}',f'target_minutes_{row.horizon}'])
        assert len(q)==row.n
        np.testing.assert_allclose(((q.predicted_points-q[f'target_points_{row.horizon}'])**2).mean(),row.point_mse,rtol=1e-10)
        np.testing.assert_allclose(((q.predicted_minutes-q[f'target_minutes_{row.horizon}'])**2).mean(),row.minute_mse,rtol=1e-10)
    atomic_json(P/'verification.json',dict(passed=True,folds=40,arms_per_fold=len(run.ARMS),all_prediction_files_replayed=len(audit),same_training_keys_all_arms=True,same_prediction_keys_all_arms=True,past_only_label_and_origin_filter_recomputed=True,all_training_medians_independently_checked=True,metrics_recomputed=int(metric.scope.eq('all').sum()),production_changed=False))

if __name__=='__main__':globals()[sys.argv[1]]()
