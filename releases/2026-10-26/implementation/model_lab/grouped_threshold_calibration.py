"""Past-only role/candidate-aware recalibration of locked probability forecasts."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from model_lab.common import ROOT,read,sha,atomic_json,verify_files,runtime

OUT=ROOT/'reports/grouped_threshold_calibration_2026_10_17'
PRIOR=ROOT/'reports/threshold_diagnosis_2026_10_17'
CACHE=ROOT/'reports/fpl_improvement_2026_10_14/cache'
BENCH='fixture_full_h3_adaptive_tc_harmonized_causal_v1'
ID='grouped-threshold-calibration-20261017-v1'
KEY=['season','round','code'];SEASONS=['2022-23','2023-24','2024-25'];TS=[6,8,10,12]
ROLES=['limited_history','established_starters','uncertain_players','inactive_recently']
LIMITS={'GK':5,'DEF':20,'MID':20,'FWD':10}
ARMS=['global','candidate_only','role_only','combined']
FC=['f_history_count','f_last5_started_round_share','f_last5_minutes_mean','f_last5_minutes_std']

def context():
    OUT.mkdir(exist_ok=True);assert not (OUT/'started.json').exists()
    frames=[];paths=[Path(__file__),ROOT/'model_lab/common.py']
    for s in SEASONS:
        pred=pd.read_csv(PRIOR/f'{s}_predictions.csv.gz')
        paths += [PRIOR/f'{s}_predictions.csv.gz',PRIOR/f'{s}_prediction_lock.json']
        for gw in range(1,39):
            folder=CACHE/s/f'gw{gw:02d}';man=read(folder/'manifest.json')
            for n in ['manifest.json','features.csv.gz','pool.csv.gz',BENCH+'.csv.gz','minutes_hurdle_fixture_v1.json']:
                paths.append(folder/n)
                if n!='manifest.json':assert sha(folder/n)==man['files'][n]
            f=pd.read_csv(folder/'features.csv.gz',usecols=['code','forecast_at']+FC)
            xp=pd.read_csv(folder/(BENCH+'.csv.gz'),usecols=['code','forecast_at','xp_0'])
            assert pd.to_datetime(f.forecast_at,utc=True).eq(pd.Timestamp(man['forecast_at'])).all()
            assert pd.to_datetime(xp.forecast_at,utc=True).eq(pd.Timestamp(man['forecast_at'])).all()
            q=pred[pred['round'].eq(gw)].merge(f.drop(columns='forecast_at'),on='code',validate='one_to_one').merge(xp[['code','xp_0']],on='code',validate='one_to_one')
            archived=read(folder/'minutes_hurdle_fixture_v1.json')
            if archived.get('official_all_blank_forced_wait') is True:
                # Explicitly archived predeadline blank, not an inferred zero outcome.
                counts=pd.Series(0,index=q.code)
            else:
                counts=pd.Series([a[0] for a in archived['match_counts_by_player']],index=archived['player_codes'])
            q['planned_count']=q.code.map(counts);assert q.planned_count.notna().all()
            enough=q.f_history_count.ge(5)
            stable=enough&q.f_last5_started_round_share.ge(.8)&q.f_last5_minutes_mean.ge(60)&q.f_last5_minutes_std.le(20)
            q['role']=np.select([~enough,stable,enough&q.f_last5_minutes_mean.gt(0)],ROLES[:3],default=ROLES[3])
            q['team_candidates']=False
            eligible=q[q.can_buy&q.planned_count.ne(0)]
            for pos,n in LIMITS.items():
                selected=eligible[eligible.position.eq(pos)].sort_values(['xp_0','code'],ascending=[False,True]).head(n).index
                q.loc[selected,'team_candidates']=True
            frames.append(q)
    allq=pd.concat(frames,ignore_index=True)
    source=ROOT/'reports/minute_simple_references_2026_10_16/predeadline_predictions.csv.gz';paths.append(source)
    old=pd.read_csv(source,usecols=KEY+['team_candidates','history_group'])
    v=allq[allq.season.ne('2022-23')].merge(old,on=KEY,validate='one_to_one',suffixes=('','_old'))
    assert len(v)==len(allq[allq.season.ne('2022-23')])
    assert v.team_candidates.eq(v.team_candidates_old).all() and v.role.eq(v.history_group).all()
    p=OUT/'predeadline_context.csv.gz';allq.to_csv(p,index=False);paths.append(p)
    oldspec=read(PRIOR/'proposal.json')
    paths += [PRIOR/'proposal.json',PRIOR/'verification.json',PRIOR/'metrics.csv']
    paths += [ROOT/'datasets/fpl_model_pipeline_v1/operational_proxy_v1.csv.xz',ROOT/'datasets/fpl_2026_27_best_effort_v1/manifest.json',ROOT/'overview/FORECAST_OBJECTIVES_V1.json']
    inputs={str(p.relative_to(ROOT)):sha(p) for p in paths}
    inputs.update({k:v for k,v in oldspec['input_hashes'].items() if k.startswith('reports/forecast_freeze_') or k.endswith('gw07_lock.json')})
    atomic_json(OUT/'context_verification.json',{'predeadline_only':True,'matched_archived_group_rows':len(v),'candidate_role_parity':True,'new_2022_groups_use_identical_rules':True,'rows':len(allq)})
    spec=dict(id=ID,hypothesis='Role/position and predeadline candidate membership improve probability calibration across seasons, particularly 6+, without worsening 8+/10+/12+.',
      change='Reuse locked raw five-class forecasts; add fixed predeadline categorical covariates to the previous global log-probability recalibrator, with candidate-only and role-only ablations. No raw predictor fitting or frozen model changes.',
      related_work=['threshold-diagnosis-20261017-v1','forecast-freeze-20261016-v1'],dataset_id='fpl_2026_27_best_effort_v1',input_hashes=inputs,clock='operational_proxy_v1',
      features='Five log raw class probabilities; position one-hot; four historical role categories; candidate flag; combined adds candidate x position and candidate x role interactions.',
      candidate_id='role_candidate_probability_calibration_v1',model_parameters={'LogisticRegression':{'C':1,'max_iter':1000},'arms':ARMS,'fixed_roles':ROLES,'no_tuning':True},
      decision_policy={'forecast_only':True,'primary_arm':'combined','raw_and_global_controls':True,'no_promotion':True},benchmark_id=BENCH,seasons=SEASONS,
      resources={'maximum_calibration_fits':8,'raw_predictor_fits':0,'threads':1,'bootstrap':2000},maximum_runs=1,
      success_criterion='Primary combined must strictly improve candidate Brier at each of four thresholds in EACH test season versus RAW and GLOBAL, and not worsen any all-pool Brier versus either. Report 6+ separately, no tradeoffs or switching to an ablation.',
      stop_rule='Stop on hash, chronology, key, group parity, global reproduction or probability failure; no automatic refit/tuning.',
      evaluation_contract={'forecast_objectives_id':'forecast-objectives-v1-20261015','target':'H1 harmonized round points; bins <6,6-<8,8-<10,10-<12,>=12; include doubles/negative outcomes',
       'training':'Calibrate 2023-24 using buyable known OOS 2022-23; calibrate 2024-25 using 2022-23 plus 2023-24. Every label available strictly before test preseason origin. No weighting/subsampling. Fixed through test season.',
       'role':'Historical >=5 observations; established if last5 start share>=.8, minutes mean>=60, std<=20; otherwise uncertain if mean>0; inactive otherwise; limited if <5/missing. Not observed upcoming start.',
       'candidate':'Top5 GK,20 DEF,20 MID,10 FWD by frozen benchmark xp_0, code tie break; buyable and planned count!=0; verified identical previous groups in both test seasons.',
       'ablation':'global=log probabilities; candidate_only=global+candidate; role_only=global+position+role; combined=all plus candidate*position and candidate*role. Shared coefficients with L2 shrinkage, not separate sparse-stratum models.',
       'controls':'Raw cached probabilities and exactly reproduced prior global calibrator; identical keys and outcomes.',
       'metrics':'Brier separately for all four thresholds; logloss, mean probability, frequency, AUC; per season and equal-season means; role/position/candidate diagnostics and first/second-half stability.',
       'uncertainty':'2000 paired circular 4-round block draws, seed20261017, per season for combined vs raw/global; same draws across thresholds and cohorts; descriptive unadjusted 95% intervals.',
       'limits':'Retrospective already-studied development data; hypothesis motivated by prior evaluation. No irreducible noise estimate or production claim.'})
    atomic_json(OUT/'proposal.json',spec)
    print('Prepared context and proposal; exact old group parity:',len(v),flush=True)

def design(q,arm):
    x=np.log(np.clip(q[[f'raw_c{i}' for i in range(5)]].to_numpy(),1e-12,1))
    cand=q.team_candidates.to_numpy(float)[:,None]
    rp=np.column_stack([q.position.eq(v).to_numpy(float) for v in LIMITS]+[q.role.eq(v).to_numpy(float) for v in ROLES])
    if arm=='global':return x
    if arm=='candidate_only':return np.column_stack([x,cand])
    if arm=='role_only':return np.column_stack([x,rp])
    return np.column_stack([x,cand,rp,cand*rp])

def run():
    spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes'])
    atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_hash':sha(OUT/'proposal.json')})
    q=pd.read_csv(OUT/'predeadline_context.csv.gz');q['forecast_at']=pd.to_datetime(q.forecast_at,utc=True)
    labels=pd.read_csv(ROOT/'datasets/fpl_model_pipeline_v1/operational_proxy_v1.csv.xz',usecols=KEY+['target_total_points','target_h1_available_at'])
    labels['target_h1_available_at']=pd.to_datetime(labels.target_h1_available_at,utc=True)
    joined=q.merge(labels,on=KEY,how='left',validate='one_to_one')
    for s in SEASONS[1:]:
        test=q[q.season.eq(s)].copy();cutoff=test.forecast_at.min()
        train=joined[joined.season.lt(s)&joined.can_buy&joined.target_total_points.notna()&joined.target_h1_available_at.lt(cutoff)].copy()
        assert train.forecast_at.max()<cutoff
        y=np.searchsorted(TS,train.target_total_points,side='right');audit=[]
        for arm in ARMS:
            with threadpool_limits(limits=1):
                model=LogisticRegression(C=1,max_iter=1000).fit(design(train,arm),y)
                p=model.predict_proba(design(test,arm))
            assert list(model.classes_)==list(range(5)) and model.n_iter_.max()<1000
            assert np.isfinite(p).all() and (p>=0).all() and np.allclose(p.sum(axis=1),1)
            if arm=='global':assert np.allclose(p,test[[f'calibrated_c{i}' for i in range(5)]],atol=1e-10,rtol=1e-10)
            for i in range(5):test[f'{arm}_c{i}']=p[:,i]
            for i,t in enumerate(TS):test[f'{arm}_p{t}']=p[:,i+1:].sum(axis=1)
            audit.append({'arm':arm,'n_features':model.n_features_in_,'iterations':int(model.n_iter_.max()),'coefficients':model.coef_.tolist(),'intercept':model.intercept_.tolist()})
        path=OUT/f'{s}_predictions.csv.gz';test.to_csv(path,index=False)
        atomic_json(OUT/f'{s}_lock.json',{'sha256':sha(path),'fit_cutoff':str(cutoff),'n_train':len(train),'max_training_label':str(train.target_h1_available_at.max()),'max_training_origin':str(train.forecast_at.max()),'fits':audit,'global_reproduced':True})
        z=test.merge(labels,on=KEY,how='left',validate='one_to_one');z=z[z.can_buy&z.target_total_points.notna()]
        z.to_csv(OUT/f'{s}_scored.csv.gz',index=False)
        print('Locked and scored',s,len(z),'calibration rows',len(train),flush=True)
    verify_files(ROOT,spec['input_hashes'])

def score():
    records=[];intervals=[];rng=np.random.default_rng(20261017)
    for s in SEASONS[1:]:
        z=pd.read_csv(OUT/f'{s}_scored.csv.gz');rounds=np.arange(1,39)
        starts=rng.integers(0,38,size=(2000,10));draws=((starts[:,:,None]+np.arange(4))%38).reshape(2000,40)[:,:38]
        cohorts={'all':z,'team_candidates':z[z.team_candidates]}
        for role in ROLES:cohorts['role_'+role]=z[z.role.eq(role)];cohorts['candidates_'+role]=z[z.team_candidates&z.role.eq(role)]
        for pos in LIMITS:cohorts['candidates_'+pos]=z[z.team_candidates&z.position.eq(pos)]
        for half,mask in [('first_half',z['round'].le(19)),('second_half',z['round'].gt(19))]:cohorts['candidates_'+half]=z[z.team_candidates&mask]
        for cohort,g in cohorts.items():
            if g.empty:continue
            for t in TS:
                y=g.target_total_points.ge(t).to_numpy(float)
                for arm in ['raw']+ARMS:
                    p=g[f'{arm}_p{t}'].to_numpy();bs=(p-y)**2
                    ll=-np.mean(y*np.log(np.clip(p,1e-12,1))+(1-y)*np.log(np.clip(1-p,1e-12,1)))
                    records.append(dict(season=s,cohort=cohort,threshold=t,arm=arm,n=len(g),events=int(y.sum()),predicted=p.mean(),observed=y.mean(),brier=bs.mean(),logloss=ll,auc=roc_auc_score(y,p) if 0<y.sum()<len(y) else np.nan))
                if cohort not in ['all','team_candidates']:continue
                for ctrl in ['raw','global']:
                    delta=(g[f'combined_p{t}'].to_numpy()-y)**2-(g[f'{ctrl}_p{t}'].to_numpy()-y)**2
                    a=pd.DataFrame({'round':g['round'].to_numpy(),'delta':delta}).groupby('round').delta.agg(['sum','count']).reindex(rounds,fill_value=0)
                    boots=a['sum'].to_numpy()[draws].sum(axis=1)/a['count'].to_numpy()[draws].sum(axis=1)
                    intervals.append(dict(season=s,cohort=cohort,threshold=t,control=ctrl,delta_brier=delta.mean(),lower=np.quantile(boots,.025),upper=np.quantile(boots,.975)))
    m=pd.DataFrame(records);m.to_csv(OUT/'metrics.csv',index=False);pd.DataFrame(intervals).to_csv(OUT/'intervals.csv',index=False)
    m.groupby(['cohort','threshold','arm'])[['brier','logloss','predicted','observed','auc']].mean().reset_index().to_csv(OUT/'equal_season_metrics.csv',index=False)
    gates=[]
    for ctrl in ['raw','global']:
        for (s,c,t),g in m[m.cohort.isin(['all','team_candidates'])].groupby(['season','cohort','threshold']):
            a=g.set_index('arm').brier;delta=a['combined']-a[ctrl]
            gates.append(dict(season=s,cohort=c,threshold=int(t),control=ctrl,delta_brier=float(delta),passed=bool(delta<0 if c=='team_candidates' else delta<=0)))
    atomic_json(OUT/'complete.json',{'passed':all(r['passed'] for r in gates),'passed_checks':sum(r['passed'] for r in gates),'total_checks':len(gates),'gates':gates,'raw_model_fits':0,'calibration_fits':8,'frozen_model_unchanged':True})
    verify_files(ROOT,read(OUT/'proposal.json')['input_hashes'])
    print('Gates',sum(r['passed'] for r in gates),'/',len(gates))

if __name__=='__main__':{'context':context,'run':run,'score':score}[sys.argv[1]]()
