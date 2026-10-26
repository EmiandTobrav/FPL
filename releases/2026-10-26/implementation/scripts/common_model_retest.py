"""Frozen common player-round data and bounded model-family retest.

Run stages separately: build, prepare, train, score, verify, report.
No production or sealed prospective forecast is changed.
"""
import os
for _key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[_key]='1'
import sys,json,hashlib,time,importlib.util,pickle,warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor,HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_squared_error,mean_absolute_error

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json,verify_files,runtime
D=R/'datasets/fpl_common_training_v1'
P=R/'reports/common_model_retest_2026_10_25'
KEY=['season','round','code'];SEASONS=['2022-23','2023-24','2024-25','2025-26']
REFITS=[1,9,17,25,33];SEED=20261025
ID='common-model-retest-20261025-v1'
MASTER=R/'datasets/fpl_master_enriched_v5/player_matches.csv.xz'
CTX=R/'datasets/fpl_all_competitions_context_v1'

def dump(p,x): atomic_json(p,x)
def read(p): return json.loads(Path(p).read_text())
def keys_hash(d): return hashlib.sha256(d[KEY].to_csv(index=False).encode()).hexdigest()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def build():
    assert not (D/'training.pkl').exists(),'Never overwrite a frozen training table'
    D.mkdir(exist_ok=True);P.mkdir(exist_ok=True)
    deps=[MASTER,MASTER.with_name('manifest.json'),Path(__file__),CTX/'player_round_context.csv.xz',CTX/'fixture_snapshots.csv.gz',R/'datasets/fpl_availability_all_seasons_v1/player_round_context.csv.xz',R/'datasets/fpl_set_piece_roles_v1/player_round_context.csv.xz',R/'datasets/fpl_role_strength_v1/player_round_role_context.csv.xz',R/'datasets/fpl_role_strength_v1/fixture_strength_audit.csv',R/'datasets/fpl_role_strength_v1/build.py',R/'datasets/fpl_role_strength_v1/common.py',R/'datasets/fpl_role_strength_v1/contract.json']
    inputs={str(p.relative_to(R)):sha(p) for p in deps}
    assert sha(MASTER)==read(MASTER.with_name('manifest.json'))['files'][MASTER.name]
    m=pd.read_csv(MASTER,low_memory=False)
    assert not m.duplicated(['season','fixture','code']).any()
    # Workload was assembled at the original operational proxy. Use that origin
    # throughout; remove known origins that were later than the actual deadline.
    origins=m.groupby(['season','round']).agg(forecast_at=('wl_forecast_at','first'),unique_origins=('wl_forecast_at','nunique')).reset_index()
    assert origins.unique_origins.eq(1).all()
    origins.forecast_at=pd.to_datetime(origins.forecast_at,utc=True)
    excluded={('2021-22',18),('2024-25',15)}
    # 2026/27 remains a separately stored current section, never retrospective validation.
    labels=[]
    goal_values={'GK':10,'DEF':6,'MID':5,'FWD':4}
    for k,q in m.groupby(KEY,sort=False):
        minutes=q.native_minutes.sum(min_count=len(q));points=q.target_total_points.sum(min_count=len(q))
        starts=q.native_starts.sum(min_count=len(q))
        pos=q.position.iloc[0]
        attack=(q.native_goals_scored*goal_values.get(pos,4)+q.native_assists*3).sum(min_count=len(q))
        appearance=(q.native_minutes.ge(60)*2+(q.native_minutes.gt(0)&q.native_minutes.lt(60))).sum()
        labels.append(dict(zip(KEY,k),target_points_1=points,target_minutes_1=minutes,target_starts_1=starts,target_attack_1=attack,target_appearance_1=float(appearance),target_residual_1=points-attack-appearance,
          label_at_1=q.observation_available_after_proxy.max(),target_history_eligible=bool(q.history_eligible.all()),target_quality_flagged=bool(q.quality_flagged_for_sensitivity.any())))
    d=pd.DataFrame(labels).merge(origins[['season','round','forecast_at']],on=['season','round'],validate='many_to_one')
    d.label_at_1=pd.to_datetime(d.label_at_1,utc=True)
    d['excluded_origin']=[(s,int(g)) in excluded for s,g in zip(d.season,d['round'])]
    d['row_id']=d.season+':'+d['round'].astype(str)+':'+d.code.astype(str)
    # Every future target is an exact round-axis join. Missing/blank rows are
    # unknown; no fabricated zero, no observed future fixture count as input.
    for h in [3]:
        sums={x:np.zeros(len(d)) for x in ['points','minutes','starts','attack','appearance','residual']};ats=[];complete=np.ones(len(d),bool)
        for j in range(h):
            z=d[KEY+['target_'+x+'_1' for x in sums]+['label_at_1','target_history_eligible']].copy();z['round']-=j
            z=d[KEY].merge(z,on=KEY,how='left',validate='one_to_one')
            complete &= z.target_history_eligible.eq(True).to_numpy()
            for x in sums:sums[x]+=z['target_'+x+'_1'].to_numpy(float)
            ats.append(z.label_at_1)
        for x,v in sums.items():d[f'target_{x}_{h}']=np.where(complete,v,np.nan)
        d[f'label_at_{h}']=pd.concat(ats,axis=1).max(axis=1)
        d.loc[~complete,f'label_at_{h}']=pd.NaT
    # Numeric feature allowlist: raw strings/source identities never become X.
    groups={'history':[],'role':[],'availability':[],'set_piece':[],'workload':[],'calendar':[],'strength':[],'lagged_weather':[]}
    audits=[]
    for folder,prefix,gname in [('fpl_all_competitions_context_v1',('wl_','cal_'),None),('fpl_availability_all_seasons_v1',('av_',),'availability'),('fpl_set_piece_roles_v1',('sp_',),'set_piece'),('fpl_role_strength_v1',('pr_',),'role')]:
        filename='player_round_role_context.csv.xz' if folder=='fpl_role_strength_v1' else 'player_round_context.csv.xz'
        c=pd.read_csv(R/'datasets'/folder/filename,low_memory=False)
        assert not c.duplicated(KEY).any()
        stamp=next(x for x in [prefix[0]+'forecast_at'] if x in c)
        c[stamp]=pd.to_datetime(c[stamp],utc=True)
        check=d[KEY+['forecast_at']].merge(c[KEY+[stamp]],on=KEY,validate='one_to_one')
        # The two known early deadlines have differently timed context layers;
        # those entire origins are explicitly excluded for every arm.
        mismatch=check[stamp].ne(check.forecast_at)
        assert all((s,int(g)) in excluded for s,g in zip(check.loc[mismatch,'season'],check.loc[mismatch,'round']))
        selected=[]
        for col in c:
            if not col.startswith(prefix):continue
            if any(t in col for t in ['strict_historical','forecast_at','snapshot_team','FPL_position','source_age','snapshot_age','source_known','source_format','schema_complete','scope_complete','calendar_fresh','club_assignment','source_deadline','mixed_origin','chance_binding','status_only','role_update','actual_taker','exhaustive','is_FPL','is_scenario','missing_means','historical_deadline','internationals_covered','youth_included','friendlies_covered']):continue
            if col in ['wl_last_observed_club','cal_last_observed_club','pr_last_club_code','pr_last_club_differs']:continue
            if col.startswith('wl_') and not any(t in col for t in ['minutes_lower_bound','appearances_lower_bound','unknown_minute_rows','rest_hours','hours_since','extra_time_match','90plus','played_within']):continue
            if col.startswith('cal_') and not any(t in col for t in ['fixtures_next','blank_rounds','double_rounds','announced_cup','hours_until','registered_fixtures','bindings_complete']):continue
            # Strings may contain boolean numeric fields when some rows are empty.
            v=c[col].replace({'True':1.,'False':0.,True:1.,False:0.})
            num=pd.to_numeric(v,errors='coerce')
            if c[col].notna().sum() and num.notna().sum()!=c[col].notna().sum():continue
            if num.notna().sum()==0:continue
            c[col]=num;selected.append(col)
            group=gname or ('workload' if col.startswith('wl_') else 'calendar');groups[group].append(col)
        if folder=='fpl_availability_all_seasons_v1':
            for status in ['a','d','i','s','n','u']:
                col='av_status_'+status;c[col]=np.where(c.av_reported_status.notna(),c.av_reported_status.eq(status).astype(float),np.nan);selected.append(col);groups['availability'].append(col)
        if folder=='fpl_role_strength_v1':
            for role in ['start','sub','none','unknown']:
                col='pr_last_role_'+role;c[col]=np.where(c.pr_last_role.notna(),c.pr_last_role.eq(role).astype(float),np.nan);selected.append(col);groups['role'].append(col)
        d=d.merge(c[KEY+selected],on=KEY,how='left',validate='one_to_one')
        audits.append(dict(layer=folder,rows=len(c),features=len(selected),origin_mismatches=int(mismatch.sum())))
    # Rebuild core history using eligible master rows and strict availability.
    # Last-known position/price/club come from earlier observations, not target row.
    m['available']=pd.to_datetime(m.observation_available_after_proxy,utc=True)
    m['kickoff']=pd.to_datetime(m.fixture_kickoff_time,utc=True)
    stats={'minutes':'native_minutes','points':'target_total_points','goals':'native_goals_scored','assists':'native_assists','clean':'native_clean_sheets','starts':'native_starts','saves':'saves'}
    weather={'temperature':'weather_temperature_2m_mean','wind':'weather_wind_speed_10m_mean','rain':'weather_precipitation_sum','sun':'weather_sunshine_minutes_daylight_capped'}
    histories={int(k):q.sort_values(['available','fixture']) for k,q in m[m.history_eligible].groupby('code',sort=False)}
    extra=[];timing=[]
    for ci,(code,requests) in enumerate(d.groupby('code',sort=False)):
        hist=histories.get(int(code),m.iloc[:0]);av=hist.available.astype('int64').to_numpy();hs=hist.season.to_numpy()
        for row in requests.itertuples():
            end=np.searchsorted(av,row.forecast_at.value,side='left');prior=hist.iloc[:end];cur=prior[prior.season.eq(row.season)];old=prior[prior.season.lt(row.season)]
            if len(old):old=old[old.season.eq(old.season.max())]
            x=dict(zip(KEY,[row.season,row.round,int(code)]));x['h_cur_count']=len(cur);x['h_old_count']=len(old)
            for label,q in [('cur',cur),('old',old)]:
                for w in [3,10]:
                    for name,src in stats.items():x[f'h_{label}_{w}_{name}']=q[src].tail(w).mean()
            for name in stats:
                nc=min(len(cur),10);no=min(len(old),10);den=nc+no
                a=x[f'h_cur_10_{name}'];b=x[f'h_old_10_{name}'];x['h_fixed_'+name]=((nc*a if nc else 0)+(no*b if no else 0))/den if den else np.nan
            x['h_last_price']=prior.value.iloc[-1] if len(prior) else np.nan
            pos=prior.position.iloc[-1] if len(prior) else None
            for p in ['GK','DEF','MID','FWD']:x['h_pos_'+p]=float(pos==p) if pos else np.nan
            x['h_days_since']=((row.forecast_at-prior.kickoff.iloc[-1]).total_seconds()/86400) if len(prior) else np.nan
            for name,src in weather.items():x['lag_weather_'+name]=prior[src].tail(3).mean()
            x['known_club']=prior.historical_team.iloc[-1] if len(prior) else None
            x['known_club_code']=prior.club_code.iloc[-1] if len(prior) else None
            timing.append(dict(row_id=row.row_id,forecast_at=str(row.forecast_at),latest_history_available=str(prior.available.iloc[-1]) if len(prior) else None,history_rows=len(prior)))
            extra.append(x)
        if ci%200==0:print('HISTORY',ci,'players',len(extra),'rows',flush=True)
    e=pd.DataFrame(extra);groups['history']=[c for c in e if c.startswith('h_')];groups['lagged_weather']=[c for c in e if c.startswith('lag_weather_')]
    d=d.merge(e,on=KEY,validate='one_to_one')
    # Dynamic strength uses only already released scores and dated schedules.
    # Do not join master match-level opponent fields (those identify actual games).
    sys.path.insert(0,str(R/'datasets/fpl_role_strength_v1'))
    oldcommon=sys.modules.pop('common',None)
    ctx=module('_common_retest_strength',R/'datasets/fpl_role_strength_v1/build.py')
    if oldcommon:sys.modules['common']=oldcommon
    sys.path.pop(0)
    games=pd.read_csv(R/'datasets/fpl_role_strength_v1/fixture_strength_audit.csv');games.home=games.home.map(lambda x:str(int(x)));games.away=games.away.map(lambda x:str(int(x)))
    snaps=pd.read_csv(CTX/'fixture_snapshots.csv.gz');snaps.source_time=pd.to_datetime(snaps.source_time,utc=True,format='mixed');snapgroups=dict(tuple(snaps.groupby(['season','round'])))
    namecodes=m[['historical_team','club_code']].drop_duplicates();assert not namecodes.historical_team.duplicated().any();namecodes=dict(zip(namecodes.historical_team,namecodes.club_code.map(lambda x:str(int(x)))))
    strength=[]
    for s,qseason in d.groupby('season',sort=True):
        state=ctx.Strength();events={};pre={}
        for g in games[games.season.eq(s)].to_dict('records'):
            events.setdefault(pd.Timestamp(g['kickoff']),{'kick':[],'release':[],'query':[]})['kick'].append(g)
            events.setdefault(pd.Timestamp(g['available']),{'kick':[],'release':[],'query':[]})['release'].append(g)
        for gw,q in qseason.groupby('round'):
            at=q.forecast_at.iloc[0];events.setdefault(at,{'kick':[],'release':[],'query':[]})['query'].append((gw,q))
        for at,event in sorted(events.items()):
            for gw,q in event['query']:
                schedule=snapgroups.get((s,gw),snaps.iloc[:0]);schedule=schedule[schedule.calendar_usable.eq(True)&schedule.source_time.lt(at)&((at-schedule.source_time).dt.total_seconds().le(14*86400))]
                for row in q.itertuples():
                    club=str(int(row.known_club_code)) if pd.notna(row.known_club_code) else None;own=state.state(club)
                    x=dict(zip(KEY,[s,gw,int(row.code)]));x.update({'ds_own_'+k:v for k,v in own.items() if k!='latest_available'})
                    for h in [1,3]:
                        fs=schedule[schedule.event.ge(gw)&schedule.event.lt(gw+h)];fs=fs[(fs.home_team==row.known_club)|(fs.away_team==row.known_club)] if pd.notna(row.known_club) else fs.iloc[:0]
                        vals=[state.state(namecodes.get(r.away_team if r.home_team==row.known_club else r.home_team)) for r in fs.itertuples()]
                        for kind in ['attack_index','concession_index']:x[f'ds_opponent_{kind}_h{h}']=np.mean([v[kind] for v in vals]) if vals else np.nan
                        x[f'ds_known_matches_h{h}']=len(vals) if len(schedule) and club is not None else np.nan
                    strength.append(x)
            for g in event['kick']:pre[g['fixture']]=state.pre(g)
            for g in event['release']:state.add(g,pre[g['fixture']])
    e=pd.DataFrame(strength);groups['strength']=[c for c in e if c.startswith('ds_')];d=d.merge(e,on=KEY,validate='one_to_one')
    d=d.sort_values(['forecast_at','season','round','code']).reset_index(drop=True)
    features=sum(groups.values(),[]);assert len(features)==len(set(features));assert not any(c.startswith(('target_','weather_')) for c in features)
    for c in features:d[c]=pd.to_numeric(d[c],errors='raise').astype('float32')
    # Excluded origins remain identifiable but are never trainable/scored.
    d['train_eligible']=d.target_history_eligible&~d.excluded_origin&d.season.ge('2020-21')&d.season.le('2025-26')
    d['eval_eligible']=d.train_eligible&d.season.isin(SEASONS)
    assert not d.duplicated(KEY).any();d.to_pickle(D/'training.pkl');d.to_csv(D/'training.csv.gz',index=False)
    pd.DataFrame(timing).to_csv(D/'history_timing_audit.csv.gz',index=False)
    summary=d.groupby('season').agg(rows=('code','size'),train_eligible=('train_eligible','sum'),eval_eligible=('eval_eligible','sum'),known_H1=('target_points_1','count'),known_H3=('target_points_3','count')).reset_index();summary.to_csv(D/'coverage.csv',index=False)
    dump(D/'schema.json',dict(key=KEY,features=features,feature_groups=groups,targets=[c for c in d if c.startswith('target_')],excluded_origins=sorted(excluded),row_universe='Observed player-round rows, not a verified complete predeadline purchase roster. All model arms use identical evaluation keys.',weather='Only lagged previous-match weather; retrospective target-match weather excluded.',clock='Same operational proxy per origin; known after-deadline origins excluded across all arms. Prior match statistics and retrospective weather permitted at kickoff+24h proxy; real publication vintages unqualified.'))
    dump(D/'manifest.json',dict(id='fpl_common_training_v1',rows=len(d),features=len(features),feature_counts={k:len(v) for k,v in groups.items()},input_hashes=inputs,files={n:sha(D/n) for n in ['training.pkl','training.csv.gz','schema.json','coverage.csv','history_timing_audit.csv.gz']},layer_audits=audits,production_changed=False))
    verify_files(R,inputs);print(summary.to_string(index=False),flush=True);print('BUILT',len(d),len(features),flush=True)

def features_for(name,schema):
    groups=schema['feature_groups'];full=schema['features'];core=groups['history']
    if name=='catboost_history':return core
    if name.startswith('catboost_without_'):
        removed=name.removeprefix('catboost_without_');return [c for c in full if c not in groups[removed]]
    return full

ARMS=['ridge','extra_trees','ridge_extra_50','hgb','catboost','lightgbm','two_part','role_conditional','component','point_distribution','fixed_history','catboost_history','catboost_without_availability','catboost_without_set_piece','catboost_without_workload','catboost_without_role','catboost_without_strength','catboost_without_lagged_weather']

def prepare():
    schema=read(D/'schema.json');verify_files(D,read(D/'manifest.json')['files'])
    deps=[Path(__file__),R/'scripts/verify_common_model_retest.py',R/'scripts/report_common_model_retest.py',D/'manifest.json',D/'training.pkl',D/'schema.json',D/'history_timing_audit.csv.gz',D/'verification.json',R/'overview/FORECAST_OBJECTIVES_V1.json',R/'overview/COMMON_COMPARISON_BASIS_V1.json',R/'overview/ACTIVE_TEAM_BENCHMARK.json',R/'datasets/fpl_2026_27_best_effort_v1/manifest.json']
    spec=dict(id=ID,candidate_id='common_enriched_model_families_v1',hypothesis='Corrected common history and enriched predeadline role, availability, set-piece, workload and strength context change the relative value of previously tested model families.',change='One newly rebuilt player-round table from masterv5; bounded family retests and CatBoost block-removal tests; no result-selected hyperparameters.',related_work=['role-strength-models-20261025-v1','role-h8-manager-20261025-v1','minute-expectation-20261015-v1','probability-pilot-20261015-v1','campaign1-component_points_fixture_v1'],dataset_id='fpl_2026_27_best_effort_v1',benchmark_id='fixed_season_h8_adaptive_v1',clock='operational_proxy_v1_known_late_origins_excluded',features={name:features_for(name,schema) for name in ARMS},model_parameters=dict(seed=SEED,arms=ARMS,ridge_alpha=100,extra_trees=dict(n_estimators=100,min_samples_leaf=20,max_features=.7,max_depth=18),hgb=dict(max_iter=120,max_leaf_nodes=15,learning_rate=.05,l2_regularization=10,early_stopping=False),catboost=dict(iterations=150,depth=5,learning_rate=.05,l2_leaf_reg=5),lightgbm=dict(n_estimators=150,max_depth=5,num_leaves=24,learning_rate=.05,min_child_samples=40,reg_lambda=5),two_part='CatBoost participation classifier and separate played/unplayed mean regressions',role='CatBoost no-minutes/sub-appearance/any-start classifier and separate mean regressions',component='Multi-target CatBoost: goal/assist points, appearance points, remaining points, minutes; sum first3 predictions',distribution='CatBoost categories <=0,1–2,3–5,6–9,10+; conditional point and minute means are training-fitted, never arbitrary bin midpoints',fixed_history='Past-only sample-count weighted current/prior last10 point/minute means times announced fixture count; missing count uses1 with explicit limitation; training residual intercept',refits=REFITS,horizons=[1,3]),decision_policy=dict(stage='common_forecast_comparison',manager='not part of this model-family batch; no legal squad or net-season-points claims',primary_control='ridge trained afresh on the identical complete feature table',operational_anchor='active model is preserved; historical operational results are not transferred into this ranking'),seasons=SEASONS,resources=dict(maximum_fits=5000,maximum_runs=1,threads_per_fit=1,no_hyperparameter_search=True),maximum_runs=1,input_hashes={str(p.relative_to(R)):sha(p) for p in deps},success_criterion='Per horizon, strictly lower point MSE than common Ridge in each of three development seasons. Minute MSE separately. Changed participation probabilities additionally require nonworse participation Brier in each development season.2025/26 separate already-inspected temporal validation. CatBoost ablations compared with full CatBoost. No automatic promotion.',stop_rule='Stop on frozen input drift, time violation, duplicate keys, nonfinite predictions or fit budget excess. Preserve technical failures and do not retune using scored outcomes.',evaluation_contract=dict(primary_metric='Season-level equal-row point MSE and minute MSE separately; equal-season averages; H1 and H3 separately',target='Exact observed round/horizon sums; unknown targets remain missing; all arms score identical eligible keys per horizon',training='Expanding2020/21 onward. Row origin and complete-horizon label availability strictly before refit cutoff. All arms share exact training row IDs within horizon/fold.',information='Common predeadline feature allowlist; source identities and current/future outcomes excluded; retained quality flags are diagnostics only. Historical receipt times remain proxies.',evidence_role='2022/23–2024/25 previously inspected development;2025/26 separate previously inspected temporal check.2026/27 not scored or used to fit.',uncertainty='Paired four-round circular moving-block bootstrap,1000 draws, descriptive only, no untouched holdout claim',probabilities='Report participation Brier for two_part and role_conditional. Point-distribution proper score also reported; expectation computed from train-only conditional means.'))
    dump(P/'proposal.json',spec);print('PREPARED',len(ARMS),flush=True)

def cbreg():
    from catboost import CatBoostRegressor
    return CatBoostRegressor(iterations=150,depth=5,learning_rate=.05,l2_leaf_reg=5,random_seed=SEED,thread_count=1,verbose=False,allow_writing_files=False,loss_function='MultiRMSE')
def cbclass():
    from catboost import CatBoostClassifier
    return CatBoostClassifier(iterations=150,depth=5,learning_rate=.05,l2_leaf_reg=5,random_seed=SEED,thread_count=1,verbose=False,allow_writing_files=False)
def fit_arm(name,tr,cols,h):
    # Common median filling for all tree architectures; explicit missing flags
    # are fitted only on training. Linear scaling is also train-only.
    imp=SimpleImputer(strategy='median',add_indicator=False,keep_empty_features=True)
    a=tr[cols].to_numpy(float);missing=~np.isfinite(a);x=imp.fit_transform(a);x=np.column_stack([x,missing.astype(float)])
    y=tr[[f'target_points_{h}',f'target_minutes_{h}']].to_numpy(float);y[:,1]/=90
    bundle=dict(name=name,columns=cols,imputer=imp,models=[],horizon=h)
    if name=='ridge':
        model=make_pipeline(StandardScaler(),Ridge(alpha=100));model.fit(x,y);bundle['models']=[model]
    elif name=='extra_trees':
        model=ExtraTreesRegressor(n_estimators=100,min_samples_leaf=20,max_features=.7,max_depth=18,n_jobs=1,random_state=SEED);model.fit(x,y);bundle['models']=[model]
    elif name=='hgb':
        for j in range(2):
            model=HistGradientBoostingRegressor(max_iter=120,max_leaf_nodes=15,learning_rate=.05,l2_regularization=10,early_stopping=False,random_state=SEED);model.fit(x,y[:,j]);bundle['models'].append(model)
    elif name=='lightgbm':
        from lightgbm import LGBMRegressor
        for j in range(2):
            model=LGBMRegressor(n_estimators=150,max_depth=5,num_leaves=24,learning_rate=.05,min_child_samples=40,reg_lambda=5,n_jobs=1,random_state=SEED,verbosity=-1);model.fit(x,y[:,j]);bundle['models'].append(model)
    elif name in ['two_part','role_conditional','point_distribution']:
        if name=='two_part':labels=tr[f'target_minutes_{h}'].gt(0).astype(int).to_numpy()
        elif name=='role_conditional':labels=np.where(tr[f'target_starts_{h}'].gt(0),2,np.where(tr[f'target_minutes_{h}'].gt(0),1,0))
        else:labels=np.digitize(y[:,0],[.5,2.5,5.5,9.5])
        clf=cbclass();clf.fit(x,labels);bundle['classifier']=clf;bundle['classes']=clf.classes_.tolist();bundle['heads']={}
        for label in clf.classes_:
            mask=labels==label
            if name=='point_distribution':bundle['heads'][int(label)]=y[mask].mean(0)
            elif mask.sum()<100:bundle['heads'][int(label)]=y[mask].mean(0)
            else:
                model=cbreg();model.fit(x[mask],y[mask]);bundle['heads'][int(label)]=model
    elif name=='component':
        y=np.column_stack([tr[f'target_{t}_{h}'].to_numpy(float) for t in ['attack','appearance','residual']]+[y[:,1]])
        model=cbreg();model.fit(x,y);bundle['models']=[model]
    elif name=='fixed_history':
        fixture=tr[f'cal_PL_fixtures_next_{h}_rounds'].fillna(h).to_numpy(float)
        raw=tr[['h_fixed_points','h_fixed_minutes']].to_numpy(float);raw[:,1]/=90;raw=np.where(np.isfinite(raw),raw,np.nanmean(y,axis=0));raw*=fixture[:,None]
        bundle['offset']=(y-raw).mean(0);bundle['fallback']=np.nanmean(y,axis=0)
    else:
        model=cbreg();model.fit(x,y);bundle['models']=[model]
    return bundle

def predict_arm(bundle,te):
    cols=bundle['columns'];a=te[cols].to_numpy(float);x=np.column_stack([bundle['imputer'].transform(a),(~np.isfinite(a)).astype(float)]);name=bundle['name'];prob=None;distribution=None
    if name in ['two_part','role_conditional','point_distribution']:
        ps=bundle['classifier'].predict_proba(x);pred=np.zeros((len(te),2))
        for j,label in enumerate(bundle['classes']):
            head=bundle['heads'][int(label)];v=head.predict(x) if hasattr(head,'predict') else np.tile(head,(len(te),1));pred+=ps[:,j,None]*v
        if name in ['two_part','role_conditional']:prob=1-ps[:,bundle['classes'].index(0)]
        else:
            distribution=np.zeros((len(te),5))
            for j,label in enumerate(bundle['classes']):distribution[:,int(label)]=ps[:,j]
    elif name=='fixed_history':
        h=bundle['horizon'];fixture=te[f'cal_PL_fixtures_next_{h}_rounds'].fillna(h).to_numpy(float);pred=te[['h_fixed_points','h_fixed_minutes']].to_numpy(float);pred[:,1]/=90;pred=np.where(np.isfinite(pred),pred,bundle['fallback']);pred=pred*fixture[:,None]+bundle['offset']
    elif name in ['hgb','lightgbm']:pred=np.column_stack([m.predict(x) for m in bundle['models']])
    elif name=='component':
        v=bundle['models'][0].predict(x);pred=np.column_stack([v[:,:3].sum(1),v[:,3]])
    else:pred=bundle['models'][0].predict(x)
    pred[:,1]=np.maximum(0,pred[:,1]*90)
    assert pred.shape==(len(te),2) and np.isfinite(pred).all()
    return pred,prob,distribution

def train():
    spec=read(P/'proposal.json');verify_files(R,spec['input_hashes']);schema=read(D/'schema.json');d=pd.read_pickle(D/'training.pkl')
    assert not (P/'started.json').exists();dump(P/'started.json',dict(started_at=str(pd.Timestamp.now(tz='UTC')),runtime=runtime(),proposal_sha256=sha(P/'proposal.json')))
    tick=time.monotonic();audit=[];count=0
    for s in SEASONS:
        for h in [1,3]:
            for gw in REFITS:
                q=d[d.season.eq(s)&d['round'].between(gw,min(gw+7,38))&~d.excluded_origin].copy();at=d[d.season.eq(s)&d['round'].eq(gw)].forecast_at.iloc[0]
                mask=d.train_eligible&d.forecast_at.lt(at)&d[f'label_at_{h}'].lt(at)
                targets=[f'target_{t}_{h}' for t in ['points','minutes','starts','attack','appearance','residual']];mask&=d[targets].notna().all(axis=1)
                tr=d[mask].copy();assert len(tr)>1000
                common=dict(season=s,horizon=h,refit_round=gw,cutoff=str(at),training_rows=len(tr),training_keys_sha256=keys_hash(tr),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'label_at_{h}'].max()),prediction_keys_sha256=keys_hash(q))
                fold=P/'folds'/f'{s}_h{h}_gw{gw:02d}';fold.mkdir(parents=True,exist_ok=True)
                predcache={}
                for name in ARMS:
                    if name=='ridge_extra_50':
                        pred=(predcache['ridge']+predcache['extra_trees'])/2;prob=None;distribution=None;bundle=None
                    else:
                        bundle=fit_arm(name,tr,features_for(name,schema),h);pred,prob,distribution=predict_arm(bundle,q)
                        # Count primitive fitted estimators; ensemble reuses fits.
                        count+=len(bundle['models'])+(1+sum(hasattr(v,'predict') for v in bundle['heads'].values()) if 'classifier' in bundle else 0)
                    assert count<=spec['resources']['maximum_fits']
                    predcache[name]=pred
                    out=q[KEY+['row_id','forecast_at','eval_eligible','target_quality_flagged',f'target_points_{h}',f'target_minutes_{h}']].copy();out['predicted_points']=pred[:,0];out['predicted_minutes']=pred[:,1];out['p_play_constant']=float(tr[f'target_minutes_{h}'].gt(0).mean())
                    if prob is not None:out['p_play']=prob
                    if distribution is not None:
                        for j in range(5):out[f'p_bin_{j}']=distribution[:,j]
                    out.to_csv(fold/(name+'.csv.gz'),index=False)
                    if bundle is not None:
                        with (fold/(name+'.pkl')).open('wb') as f:pickle.dump(bundle,f,protocol=5)
                    audit.append(dict(common,arm=name,features=len(features_for(name,schema)),predictions_sha256=sha(fold/(name+'.csv.gz')),model_sha256=sha(fold/(name+'.pkl')) if bundle is not None else None))
                    print('FIT',s,'H'+str(h),'GW'+str(gw),name,'n',len(tr),'fits',count,'seconds',round(time.monotonic()-tick),flush=True)
                dump(fold/'lock.json',dict(common,predictions={n+'.csv.gz':sha(fold/(n+'.csv.gz')) for n in ARMS}))
                pd.DataFrame(audit).to_csv(P/'fit_audit.csv',index=False)
    verify_files(R,spec['input_hashes']);dump(P/'prediction_lock.json',dict(fits=count,folds=40,arms=ARMS,audit_sha256=sha(P/'fit_audit.csv'),saved_before_scoring=True,seconds=time.monotonic()-tick));print('SEALED',count,flush=True)

def collect():
    allrows=[]
    for s in SEASONS:
        for h in [1,3]:
            for gw in REFITS:
                fold=P/'folds'/f'{s}_h{h}_gw{gw:02d}';verify_files(fold,read(fold/'lock.json')['predictions'])
                for name in ARMS:
                    a=pd.read_csv(fold/(name+'.csv.gz'));a['arm']=name;a['horizon']=h;allrows.append(a)
    return pd.concat(allrows,ignore_index=True)

def score():
    assert read(P/'prediction_lock.json')['saved_before_scoring'];a=collect();metrics=[];cohorts=[];rng=np.random.default_rng(SEED);intervals=[]
    for (s,h),group in a.groupby(['season','horizon']):
        target=f'target_points_{h}';minute=f'target_minutes_{h}'
        valid=group.eval_eligible&group[target].notna()&group[minute].notna();g=group[valid].copy()
        expected=None
        for name,q in g.groupby('arm'):
            ids=q.row_id.tolist()
            if expected is None:expected=ids
            else:assert ids==expected
        # Common candidate set is selected before outcomes by simple history mean,
        # identical for all arms; this is diagnostic and not a legal FPL squad.
        base=pd.read_pickle(D/'training.pkl');base=base[base.season.eq(s)];base['candidate_rank']=base.groupby('round').h_fixed_points.rank(method='first',ascending=False)
        selected=set(base.loc[base.candidate_rank.le(60),'row_id'])
        for name,q in g.groupby('arm'):
            for scope,z in [('all',q),('history_top60',q[q.row_id.isin(selected)]),('unflagged',q[~q.target_quality_flagged])]:
                if not len(z):continue
                row=dict(season=s,horizon=int(h),arm=name,scope=scope,n=len(z),point_mse=mean_squared_error(z[target],z.predicted_points),point_mae=mean_absolute_error(z[target],z.predicted_points),point_bias=float((z.predicted_points-z[target]).mean()),minute_mse=mean_squared_error(z[minute],z.predicted_minutes),minute_mae=mean_absolute_error(z[minute],z.predicted_minutes))
                if 'p_play' in z and z.p_play.notna().all():
                    row['participation_brier']=float(((z.p_play-z[minute].gt(0))**2).mean());row['constant_participation_brier']=float(((z.p_play_constant-z[minute].gt(0))**2).mean())
                if name=='point_distribution':
                    observed=np.digitize(z[target],[.5,2.5,5.5,9.5]);ps=z[[f'p_bin_{j}' for j in range(5)]].to_numpy();truth=np.eye(5)[observed];row['rps']=float(((ps.cumsum(1)[:,:-1]-truth.cumsum(1)[:,:-1])**2).mean())
                metrics.append(row)
            cohorts.append(dict(season=s,horizon=int(h),arm=name,known_rows=len(q),keys_sha256=hashlib.sha256('\n'.join(q.row_id).encode()).hexdigest()))
        pivot=g.pivot(index=['row_id','round'],columns='arm',values='predicted_points');actual=g.drop_duplicates('row_id').set_index(['row_id','round'])[target];errs=pivot.sub(actual,axis=0)**2
        for name in ARMS:
            delta=errs[name]-errs.ridge;b=delta.groupby(level='round').agg(['sum','count']).reindex(range(1,39),fill_value=0).to_numpy();draw=[]
            for _ in range(1000):
                ix=np.concatenate([(np.arange(4)+j)%38 for j in rng.integers(0,38,10)])[:38];v=b[ix].sum(0);draw.append(v[0]/v[1])
            intervals.append(dict(season=s,horizon=int(h),arm=name,delta_mse=float(delta.mean()),lower=float(np.quantile(draw,.025)),upper=float(np.quantile(draw,.975))))
    m=pd.DataFrame(metrics);m.to_csv(P/'metrics.csv',index=False);pd.DataFrame(cohorts).to_csv(P/'cohorts.csv',index=False);pd.DataFrame(intervals).to_csv(P/'intervals.csv',index=False)
    summary=m[m.scope.eq('all')].assign(period=lambda x:np.where(x.season.eq('2025-26'),'later_2025_26','development')).groupby(['period','horizon','arm']).agg(point_mse=('point_mse','mean'),minute_mse=('minute_mse','mean'),point_mae=('point_mae','mean'),seasons=('season','nunique')).reset_index();summary.to_csv(P/'summary.csv',index=False)
    gates=[]
    for h in [1,3]:
        z=m[m.scope.eq('all')&m.horizon.eq(h)&~m.season.eq('2025-26')].pivot(index='season',columns='arm',values='point_mse')
        mins=m[m.scope.eq('all')&m.horizon.eq(h)&~m.season.eq('2025-26')].pivot(index='season',columns='arm',values='minute_mse')
        probs=m[m.scope.eq('all')&m.horizon.eq(h)&~m.season.eq('2025-26')]
        for name in ARMS:
            gate=dict(horizon=h,arm=name,point_pass_all_development_seasons=bool((z[name]<z.ridge).all()),minute_pass_all_development_seasons=bool((mins[name]<mins.ridge).all()),wins=int((z[name]<z.ridge).sum()))
            if name in ['two_part','role_conditional']:
                q=probs[probs.arm.eq(name)];gate['participation_brier_nonworse_vs_constant_all_seasons']=bool(q.participation_brier.le(q.constant_participation_brier).all())
            gates.append(gate)
    dump(P/'score.json',dict(gates=gates,production_changed=False,manager_run=False));print(summary.to_string(index=False),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
