"""Prequential expanding calibration; locked raw model and preseason control."""
from pathlib import Path
import sys,hashlib,time
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from model_lab.common import ROOT,read,sha,atomic_json,verify_files,runtime

OUT=ROOT/'reports/rolling_threshold_calibration_2026_10_17'
OLD=ROOT/'reports/grouped_threshold_calibration_2026_10_17_attempt2'
ID='rolling-threshold-calibration-20261017-v1'
KEY=['season','round','code'];TS=[6,8,10,12];SEASONS=['2023-24','2024-25']
LABELS=ROOT/'datasets/fpl_model_pipeline_v1/operational_proxy_v1.csv.xz'
def xmatrix(q):
    return np.column_stack([np.log(np.clip(q[[f'raw_c{i}' for i in range(5)]].to_numpy(),1e-12,1)),q.team_candidates.to_numpy(float)])
def keyhash(q):return hashlib.sha256(q[KEY].to_csv(index=False).encode()).hexdigest()
def prepare():
    OUT.mkdir(exist_ok=True)
    prior=read(OLD/'proposal.json')
    paths=[Path(__file__),ROOT/'model_lab/common.py',OLD/'predeadline_context.csv.gz',OLD/'proposal.json',OLD/'verification.json',OLD/'metrics.csv',LABELS,ROOT/'overview/FORECAST_OBJECTIVES_V1.json',ROOT/'datasets/fpl_2026_27_best_effort_v1/manifest.json']
    paths += [OLD/f'{s}_{n}' for s in SEASONS for n in ['predictions.csv.gz','lock.json']]
    inputs={str(p.relative_to(ROOT)):sha(p) for p in paths}
    inputs.update({k:v for k,v in prior['input_hashes'].items() if k.startswith('reports/forecast_freeze_') or k.endswith('gw07_lock.json')})
    spec=dict(id=ID,hypothesis='Updating candidate-aware calibration every deadline reduces Brier loss and improves within-season stability versus the identical preseason-locked calibrator.',
      change='Only calibration refresh changes: expanding prior OOS history plus available current-season OOS outcomes, refit each deadline. Same five log class probabilities, candidate flag, C=1; no role additions, raw refits or window tuning.',related_work=['grouped-threshold-calibration-20261017-v2','threshold-diagnosis-20261017-v1'],
      dataset_id='fpl_2026_27_best_effort_v1',input_hashes=inputs,clock='operational_proxy_v1',features='Five log raw class probabilities plus predeadline team_candidates flag, exact previous candidate_only design.',candidate_id='expanding_deadline_candidate_calibration_v1',
      model_parameters={'C':1,'max_iter':1000,'refresh':'each deadline after GW1','window':'expanding; equal row weights; no decay','GW1':'exact cached preseason output','no_tuning':True},decision_policy={'forecast_only':True,'primary_control':'cached candidate_only preseason calibration','secondary_control':'cached raw probabilities','frozen_model_unchanged':True},benchmark_id=prior['benchmark_id'],seasons=['2022-23']+SEASONS,
      resources={'maximum_new_calibration_fits':74,'raw_model_fits':0,'threads':1,'bootstrap':2000},maximum_runs=1,
      success_criterion='Refresh gate: strictly lower candidate Brier at all 4 thresholds in BOTH seasons, no worse all-pool Brier, versus fixed candidate_only (16 checks). Raw guard: same candidate strict/all no-worse against raw (16). Stability gate: no worse candidate Brier in BOTH fixed halves (GW1-19/20-38), each threshold/year, versus fixed (16). Retain only if all three gates pass; report 6+ separately; no switching variants.',
      stop_rule='Stop on causal/hash/key/probability/convergence violation. No tuning, altered cadence or adaptive restart after results.',
      evaluation_contract={'forecast_objectives_id':'forecast-objectives-v1-20261015','target':'H1 harmonized round points; coherent <6,6-<8,8-<10,10-<12,>=12; same rows as previous study',
       'training':'2022-23 onwards, only buyable raw OOS predictions with forecast_at AND target_h1_available_at strictly before current forecast_at. Include earlier seasons and available current-season rows. Missing labels excluded, never zero-filled. Future target labels never used for fit.',
       'inference':'Same unchanged raw predictors. Save each round and hash/coefficients/training-key/time audit before scoring test outcomes. GW1 exact cached fixed calibration; other rounds refit from scratch with unchanged parameters. Skip fit only when identical training-key hash to previous refresh.',
       'controls':'Exact cached candidate_only from prior experiment for entire season, plus raw; verify common keys and frozen probability inputs; no need to reproduce an old optimizer fit.',
       'candidate':'Existing verified predeadline top5GK20DEF20MID10FWD proxy shortlist; ranking before outcomes, unchanged across arms.',
       'metrics':'Separate threshold Brier primary; logloss, AUC, mean probability, frequency; annual and equal-season summaries. Fixed halves and round diagnostics; per-contrast leave-one-round-out differences.',
       'uncertainty':'2000 paired circular 4-round block resamples, same per-season draws across cohorts/thresholds/controls; descriptive 95%, no multiplicity correction.',
       'limits':'Previously inspected development seasons; hypothesis motivated by earlier results. Proxy timing and best-effort targets remain. No prospective claim or estimate of irreducible noise. No 2026-27 outcomes.'})
    atomic_json(OUT/'proposal.json',spec)

def load_data():
    q=pd.read_csv(OLD/'predeadline_context.csv.gz');q['forecast_at']=pd.to_datetime(q.forecast_at,utc=True)
    labels=pd.read_csv(LABELS,usecols=KEY+['target_total_points','target_h1_available_at']);labels['target_h1_available_at']=pd.to_datetime(labels.target_h1_available_at,utc=True)
    history=q.merge(labels,on=KEY,how='left',validate='one_to_one')
    return q,labels,history

def run():
    spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes'])
    atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_hash':sha(OUT/'proposal.json')})
    q,labels,history=load_data();all_audits=[];fits=0
    for season in SEASONS:
        fixed=pd.read_csv(OLD/f'{season}_predictions.csv.gz');frames=[];last_hash=None;model=None
        for gw in range(1,39):
            t=time.monotonic();test=q[q.season.eq(season)&q['round'].eq(gw)].copy();assert test.forecast_at.nunique()==1
            at=test.forecast_at.iloc[0]
            train=history[history.can_buy&history.target_total_points.notna()&history.forecast_at.lt(at)&history.target_h1_available_at.lt(at)].copy()
            assert train.season.le(season).all();h=keyhash(train)
            f=fixed[fixed['round'].eq(gw)].set_index('code').loc[test.code].reset_index()
            assert np.allclose(test[[f'raw_c{i}' for i in range(5)]],f[[f'raw_c{i}' for i in range(5)]],atol=1e-14)
            audit={'season':season,'round':gw,'forecast_at':str(at),'n_train':len(train),'current_season_train_n':int(train.season.eq(season).sum()),'max_train_origin':str(train.forecast_at.max()),'max_label_available':str(train.target_h1_available_at.max()),'training_key_sha256':h}
            if gw==1:
                p=f[[f'candidate_only_c{i}' for i in range(5)]].to_numpy();audit['mode']='reuse_exact_preseason'
            else:
                if model is None or h!=last_hash:
                    with threadpool_limits(limits=1):model=LogisticRegression(C=1,max_iter=1000).fit(xmatrix(train),np.searchsorted(TS,train.target_total_points,side='right'))
                    assert model.n_iter_.max()<1000 and list(model.classes_)==list(range(5))
                    fits+=1;assert fits<=74;audit['mode']='refit'
                else:audit['mode']='reuse_unchanged_training'
                with threadpool_limits(limits=1):p=model.predict_proba(xmatrix(test))
                audit.update(coefficients=model.coef_.tolist(),intercept=model.intercept_.tolist(),iterations=int(model.n_iter_.max()))
            last_hash=h
            assert np.isfinite(p).all() and (p>=0).all() and np.allclose(p.sum(axis=1),1)
            z=test[KEY+['forecast_at','can_buy','team_candidates','position','role']].copy()
            for arm,probs in [('rolling',p),('fixed',f[[f'candidate_only_c{i}' for i in range(5)]].to_numpy()),('raw',f[[f'raw_c{i}' for i in range(5)]].to_numpy())]:
                for i in range(5):z[f'{arm}_c{i}']=probs[:,i]
                for i,n in enumerate(TS):z[f'{arm}_p{n}']=probs[:,i+1:].sum(axis=1)
            path=OUT/f'{season}_gw{gw:02d}.csv.gz';z.to_csv(path,index=False);audit.update(prediction_sha256=sha(path),seconds=time.monotonic()-t)
            atomic_json(OUT/f'{season}_gw{gw:02d}.lock.json',audit);all_audits.append(audit);frames.append(z)
            if gw%5==0 or gw==1:print('Locked',season,gw,'train',len(train),'current season',audit['current_season_train_n'],'fits',fits,flush=True)
        pred=pd.concat(frames,ignore_index=True);pred.to_csv(OUT/f'{season}_predictions.csv.gz',index=False)
        scored=pred.merge(labels,on=KEY,how='left',validate='one_to_one');scored=scored[scored.can_buy&scored.target_total_points.notna()];scored.to_csv(OUT/f'{season}_scored.csv.gz',index=False)
    pd.DataFrame([{k:v for k,v in r.items() if k not in ['coefficients','intercept']} for r in all_audits]).to_csv(OUT/'fit_audit.csv',index=False)
    atomic_json(OUT/'predictions_complete.json',{'fits':fits,'origins':len(all_audits),'raw_model_fits':0})
    verify_files(ROOT,spec['input_hashes'])

def score():
    records=[];intervals=[];round_records=[];rng=np.random.default_rng(20261017)
    for season in SEASONS:
        z=pd.read_csv(OUT/f'{season}_scored.csv.gz')
        starts=rng.integers(0,38,size=(2000,10));draws=((starts[:,:,None]+np.arange(4))%38).reshape(2000,40)[:,:38]
        cohorts={'all':z,'team_candidates':z[z.team_candidates]}
        for half,mask in [('first_half',z['round'].le(19)),('second_half',z['round'].gt(19))]:cohorts['candidates_'+half]=z[z.team_candidates&mask]
        for cohort,g in cohorts.items():
            for t in TS:
                y=g.target_total_points.ge(t).to_numpy(float)
                for arm in ['raw','fixed','rolling']:
                    p=g[f'{arm}_p{t}'].to_numpy();ll=-np.mean(y*np.log(np.clip(p,1e-12,1))+(1-y)*np.log(np.clip(1-p,1e-12,1)))
                    records.append(dict(season=season,cohort=cohort,threshold=t,arm=arm,n=len(g),events=int(y.sum()),predicted=p.mean(),observed=y.mean(),brier=np.mean((p-y)**2),logloss=ll,auc=roc_auc_score(y,p)))
                if cohort not in ['all','team_candidates']:continue
                for ctrl in ['fixed','raw']:
                    delta=(g[f'rolling_p{t}'].to_numpy()-y)**2-(g[f'{ctrl}_p{t}'].to_numpy()-y)**2
                    a=pd.DataFrame({'round':g['round'].to_numpy(),'delta':delta}).groupby('round').delta.agg(['sum','count']).reindex(range(1,39),fill_value=0)
                    sums=a['sum'].to_numpy();counts=a['count'].to_numpy();boot=sums[draws].sum(axis=1)/counts[draws].sum(axis=1)
                    loo=(sums.sum()-sums)/(counts.sum()-counts)
                    intervals.append(dict(season=season,cohort=cohort,threshold=t,control=ctrl,delta_brier=delta.mean(),lower=np.quantile(boot,.025),upper=np.quantile(boot,.975),leave_one_round_min=loo.min(),leave_one_round_max=loo.max(),rounds_better=int((sums<-1e-12).sum()),rounds_worse=int((sums>1e-12).sum())))
                    for gw,r in a.iterrows():round_records.append(dict(season=season,round=gw,cohort=cohort,threshold=t,control=ctrl,n=int(r['count']),delta_sum=r['sum'],delta_brier=r['sum']/r['count'] if r['count'] else np.nan))
    m=pd.DataFrame(records);m.to_csv(OUT/'metrics.csv',index=False);pd.DataFrame(intervals).to_csv(OUT/'intervals.csv',index=False);pd.DataFrame(round_records).to_csv(OUT/'per_round.csv',index=False)
    m.groupby(['cohort','threshold','arm'])[['brier','logloss','predicted','observed','auc']].mean().reset_index().to_csv(OUT/'equal_season_metrics.csv',index=False)
    gates=[]
    for (s,c,t),g in m.groupby(['season','cohort','threshold']):
        a=g.set_index('arm').brier
        for ctrl in ['fixed','raw'] if c in ['all','team_candidates'] else ['fixed']:
            d=a.rolling-a[ctrl];category='stability' if c.startswith('candidates_') else 'refresh' if ctrl=='fixed' else 'raw_guard'
            gates.append(dict(season=s,cohort=c,threshold=int(t),control=ctrl,category=category,delta_brier=float(d),passed=bool(d<0 if c=='team_candidates' else d<=0)))
    counts={k:dict(passed=sum(r['passed'] for r in gates if r['category']==k),total=sum(r['category']==k for r in gates)) for k in ['refresh','raw_guard','stability']}
    atomic_json(OUT/'complete.json',{'passed':all(r['passed'] for r in gates),'categories':counts,'gates':gates,'fits':read(OUT/'predictions_complete.json')['fits'],'frozen_model_unchanged':True})
    verify_files(ROOT,read(OUT/'proposal.json')['input_hashes']);print(counts,flush=True)

if __name__=='__main__':{'prepare':prepare,'run':run,'score':score}[sys.argv[1]]()
