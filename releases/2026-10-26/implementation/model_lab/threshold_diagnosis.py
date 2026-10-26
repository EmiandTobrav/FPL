"""Separate chronological tail-probability research; never edits frozen forecasts."""
from pathlib import Path
import json, sys
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from threadpoolctl import threadpool_limits
from model_lab.common import ROOT, sha, read, atomic_json, verify_files, runtime
from model_lab.forecast import pipeline_modules, causal_training
from model_lab.probabilistic import Head, PARAMS, check
from model_lab.probability_experiment import features

OUT=ROOT/'reports/threshold_diagnosis_2026_10_17'
CACHE=ROOT/'reports/fpl_improvement_2026_10_14/cache'
KEY=['season','round','code']
SEASONS=['2022-23','2023-24','2024-25']
THRESHOLDS=[6,8,10,12]
ID='threshold-diagnosis-20261017-v1'
GROUPS=ROOT/'reports/minute_simple_references_2026_10_16/predeadline_predictions.csv.gz'
def classes(y):
    return np.searchsorted(THRESHOLDS,np.asarray(y),side='right')

def prepare():
    OUT.mkdir(exist_ok=True)
    paths=[Path(__file__),GROUPS,ROOT/'overview/FORECAST_OBJECTIVES_V1.json']
    paths += [ROOT/'model_lab'/n for n in ['common.py','forecast.py','probabilistic.py','probability_experiment.py']]
    paths += [ROOT/'datasets/fpl_model_pipeline_v1'/n for n in ['loader.py','pipeline.py','manifest.json','schema.json','operational_proxy_v1.csv.xz']]
    paths += [ROOT/'datasets/fpl_2026_27_best_effort_v1'/n for n in ['manifest.json','player_rounds.csv.xz']]
    for s in SEASONS:
        for gw in range(1,39):
            paths += [CACHE/s/f'gw{gw:02d}'/n for n in ['manifest.json','pool.csv.gz','features.csv.gz']]
    frozen=ROOT/'reports/forecast_freeze_2026_10_16'
    paths += list(p for p in frozen.rglob('*') if p.is_file())
    paths += [ROOT/'reports/temporal_2026_27_2026_10_16/gw07_lock.json']
    spec=dict(id=ID,hypothesis='Chronological recalibration can reduce threshold Brier loss; residual loss must not be identified as irreducible randomness.',
      change='New coherent bins <6,6-7,8-9,10-11,12+; separate research classifier, prior-season out-of-sample calibration and exact grouped Brier diagnostic. No frozen point-model changes.',
      related_work=['probability-pilot-20261015-v1','forecast-freeze-20261016-v1'],dataset_id='fpl_2026_27_best_effort_v1',
      input_hashes={str(p.relative_to(ROOT)):sha(p) for p in paths},clock='operational_proxy_v1',features='Same numeric extended features and position indicators as probability pilot.',
      candidate_id='coherent_threshold_recalibration_v1',model_parameters={'classifier':PARAMS,'calibrator':'LogisticRegression on five log class probabilities, C=1, max_iter=1000; no tuning'},
      decision_policy={'forecast_only':True,'frozen_model_unchanged':True},benchmark_id='fixture_full_h3_adaptive_tc_harmonized_causal_v1',seasons=SEASONS,
      resources={'threads':1,'maximum_classifier_fits':3,'maximum_calibrator_fits':2,'bootstrap_replicates':1000},maximum_runs=1,
      success_criterion='Recalibration research gate: strictly lower Brier at EACH of four thresholds in BOTH 2023-24 and 2024-25. No promotion. Report all outcomes, logloss, AUC, AP, fixed candidates and descriptive uncertainty.',
      stop_rule='Stop on chronology/hash/invalid probabilities. No tuning or automatic retry.',
      evaluation_contract={'forecast_objectives_id':'forecast-objectives-v1-20261015','target':'H1 harmonized round points, including negatives and doubles',
       'training':'Preseason expanding causal training via existing loader; 2022-23 is calibration warm-up only; weights fixed within season, features updated each deadline.',
       'calibration':'Only buyable scored OOS predictions from earlier seasons, with labels available before new preseason cutoff. Fit multiclass log-probability calibration. All four tails coherent.',
       'controls':'Raw distribution; constant class frequencies from the same earlier OOS calibration pool, Laplace +1 per class.',
       'evaluation':'2023-24 and 2024-25; known point labels only; unknown not zero-filled. Fixed candidate mask from archived predeadline file. No 2026-27 or prospective outcomes.',
       'decomposition':'Ten fixed bins with edges 0,.01,.025,.05,.075,.10,.15,.20,.30,.50,1. Brier(raw)=uncertainty-resolution+reliability+within_bin_remainder. Descriptive reliability is not causal recoverable error or noise floor.',
       'uncertainty':'1000 paired circular 4-round blocks per season; 2.5/97.5 percentiles for calibrated minus raw Brier; unadjusted exploratory intervals.',
       'evidence_role':'Already studied development seasons; new chronological research outputs, not probabilities from the frozen full point model.'})
    atomic_json(OUT/'proposal.json',spec)

def run():
    spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes'])
    atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json')})
    loader,_=pipeline_modules();rows,schema=loader.load_rows()
    cols=[c for c in schema['extended_features'] if c not in schema['categorical_features']]
    labels=rows[KEY+['target_total_points','target_h1_available_at']].copy()
    assert not labels.duplicated(KEY).any()
    previous=[];audits=[];coverage=[]
    groups=pd.read_csv(GROUPS,usecols=KEY+['team_candidates'])
    assert not groups.duplicated(KEY).any()
    for season in SEASONS:
        cutoff=pd.Timestamp(read(CACHE/season/'gw01/manifest.json')['forecast_at'])
        train,_=causal_training(rows,cutoff,1)
        with threadpool_limits(limits=1):
            model=Head(5).fit(features(train,cols),classes(train.target_total_points))
        cal=None;hist=None;prior=None
        if previous:
            hist=pd.concat(previous,ignore_index=True)
            hist=hist[hist.target_h1_available_at.lt(cutoff)].copy()
            assert hist.forecast_at.max()<cutoff
            with threadpool_limits(limits=1):
                cal=LogisticRegression(C=1,max_iter=1000).fit(np.log(np.clip(hist[[f'raw_c{i}' for i in range(5)]],1e-12,1)),classes(hist.target_total_points))
            assert cal.n_iter_.max()<1000 and list(cal.classes_)==list(range(5))
            prior=(np.bincount(classes(hist.target_total_points),minlength=5)+1)/(len(hist)+5)
        frames=[]
        for gw in range(1,39):
            folder=CACHE/season/f'gw{gw:02d}';man=read(folder/'manifest.json')
            pool=pd.read_csv(folder/'pool.csv.gz');f=pd.read_csv(folder/'features.csv.gz')
            assert not f.code.duplicated().any() and not pool.code.duplicated().any()
            f=f.set_index('code').loc[pool.code].reset_index()
            assert pd.to_datetime(f.forecast_at,utc=True).eq(pd.Timestamp(man['forecast_at'])).all()
            with threadpool_limits(limits=1):
                raw=model.predict(features(f,cols))
                calibrated=check(cal.predict_proba(np.log(np.clip(raw,1e-12,1)))) if cal else None
            q=pool[['code','can_buy','position']].copy();q['season']=season;q['round']=gw;q['forecast_at']=man['forecast_at']
            for arm,prob in [('raw',raw),('calibrated',calibrated),('prior',np.tile(prior,(len(q),1)) if prior is not None else None)]:
                if prob is None:continue
                for i in range(5):q[f'{arm}_c{i}']=prob[:,i]
                for i,t in enumerate(THRESHOLDS):q[f'{arm}_p{t}']=prob[:,i+1:].sum(axis=1)
            frames.append(q)
        pred=pd.concat(frames,ignore_index=True)
        path=OUT/f'{season}_predictions.csv.gz';pred.to_csv(path,index=False)
        audit={'season':season,'fit_cutoff':str(cutoff),'training_n':len(train),'max_training_origin':str(train.forecast_at.max()),'max_training_label':str(train.target_h1_available_at.max()),
            'calibration_n':0 if hist is None else len(hist),'max_calibration_label':None if hist is None else str(hist.target_h1_available_at.max()),'predictions_sha256':sha(path)}
        atomic_json(OUT/f'{season}_prediction_lock.json',audit);audits.append(audit)
        z=pred.merge(labels,on=KEY,how='left',validate='one_to_one')
        known=z.can_buy & z.target_total_points.notna()
        coverage.append({'season':season,'requested':int(z.can_buy.sum()),'known':int(known.sum()),'missing':int((z.can_buy&~known).sum())})
        z=z[known].copy();z['forecast_at']=pd.to_datetime(z.forecast_at,utc=True)
        if season!='2022-23':
            z=z.merge(groups,on=KEY,how='left',validate='one_to_one');assert z.team_candidates.notna().all()
        z.to_csv(OUT/f'{season}_scored.csv.gz',index=False)
        previous.append(z)
        print('Completed',season,audit,flush=True)
    pd.DataFrame(coverage).to_csv(OUT/'coverage.csv',index=False)
    atomic_json(OUT/'prediction_complete.json',{'audits':audits,'input_hashes_unchanged':True})
    verify_files(ROOT,spec['input_hashes'])

def score():
    metrics=[];reliability=[];decomposition=[];intervals=[];ranking=[]
    edges=np.array([0,.01,.025,.05,.075,.10,.15,.20,.30,.50,1.0000001])
    rng=np.random.default_rng(20261017)
    for season in SEASONS[1:]:
        z=pd.read_csv(OUT/f'{season}_scored.csv.gz')
        rounds=np.sort(z['round'].unique())
        # Paired draws reused for every threshold and cohort in this season.
        draws=[]
        for _ in range(1000):
            starts=rng.integers(0,len(rounds),size=int(np.ceil(len(rounds)/4)))
            draws.append(rounds[np.concatenate([(start+np.arange(4))%len(rounds) for start in starts])[:len(rounds)]])
        for cohort,g in [('all',z),('team_candidates',z[z.team_candidates])]:
            for t in THRESHOLDS:
                y=g.target_total_points.ge(t).to_numpy(float)
                for arm in ['raw','calibrated','prior']:
                    p=g[f'{arm}_p{t}'].to_numpy();bs=np.mean((p-y)**2)
                    ll=-np.mean(y*np.log(np.clip(p,1e-12,1))+(1-y)*np.log(np.clip(1-p,1e-12,1)))
                    metrics.append(dict(season=season,cohort=cohort,threshold=t,arm=arm,n=len(g),events=int(y.sum()),observed=y.mean(),predicted=p.mean(),brier=bs,logloss=ll,auc=roc_auc_score(y,p),average_precision=average_precision_score(y,p)))
                    bins=np.searchsorted(edges,p,side='right')-1
                    unc=y.mean()*(1-y.mean());rel=res=bs_binned=0.
                    for b in range(len(edges)-1):
                        m=bins==b
                        if not m.any():continue
                        pb=p[m].mean();yb=y[m].mean();w=m.mean()
                        rel+=w*(pb-yb)**2;res+=w*(yb-y.mean())**2;bs_binned+=w*np.mean((pb-y[m])**2)
                        reliability.append(dict(season=season,cohort=cohort,threshold=t,arm=arm,bin=b,lower=edges[b],upper=min(edges[b+1],1),n=int(m.sum()),events=int(y[m].sum()),predicted=pb,observed=yb))
                    assert np.isclose(bs_binned,unc-res+rel,atol=1e-12)
                    decomposition.append(dict(season=season,cohort=cohort,threshold=t,arm=arm,brier=bs,uncertainty=unc,resolution=res,reliability=rel,within_bin_remainder=bs-bs_binned,reliability_pct_brier=100*rel/bs))
                d=(g[f'calibrated_p{t}'].to_numpy()-y)**2-(g[f'raw_p{t}'].to_numpy()-y)**2
                a=pd.DataFrame({'round':g['round'].to_numpy(),'d':d}).groupby('round').d.agg(['sum','count']).reindex(rounds,fill_value=0)
                boots=[a.loc[v,'sum'].sum()/a.loc[v,'count'].sum() for v in draws]
                intervals.append(dict(season=season,cohort=cohort,threshold=t,delta_brier=d.mean(),lower=np.quantile(boots,.025),upper=np.quantile(boots,.975)))
        for t in THRESHOLDS:
            for arm in ['raw','calibrated']:
                top=z.sort_values([f'{arm}_p{t}','code'],ascending=[False,True]).groupby('round',sort=False).head(10)
                ranking.append(dict(season=season,threshold=t,arm=arm,n=len(top),events=int(top.target_total_points.ge(t).sum()),predicted=top[f'{arm}_p{t}'].mean(),observed=top.target_total_points.ge(t).mean(),base_rate=z.target_total_points.ge(t).mean()))
    for name,data in [('metrics',metrics),('reliability',reliability),('decomposition',decomposition),('intervals',intervals),('top10',ranking)]:
        pd.DataFrame(data).to_csv(OUT/f'{name}.csv',index=False)
    m=pd.DataFrame(metrics);g=m[m.cohort.eq('all')].pivot(index=['season','threshold'],columns='arm',values='brier')
    atomic_json(OUT/'complete.json',{'recalibration_gate_passed':bool((g.calibrated<g.raw).all()),'classification_fits':3,'calibration_fits':2,'frozen_model_unchanged':True,'no_irreducible_noise_estimate':True})
    verify_files(ROOT,read(OUT/'proposal.json')['input_hashes'])

if __name__=='__main__':
    {'prepare':prepare,'run':run,'score':score}[sys.argv[1]]()
