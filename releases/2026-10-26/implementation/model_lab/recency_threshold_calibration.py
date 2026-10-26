"""Two preregistered recent-round weightings of past-only probability calibration."""
from pathlib import Path
import sys,hashlib,time
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from model_lab.common import ROOT,read,sha,atomic_json,verify_files,runtime
from model_lab.rolling_threshold_calibration import load_data,xmatrix,keyhash,KEY,TS,SEASONS

OUT=ROOT/'reports/recency_threshold_calibration_2026_10_17'
CONTROL=ROOT/'reports/rolling_threshold_calibration_2026_10_17'
ID='recency-threshold-calibration-20261017-v1'
ARMS={'recent3':3,'recent5':5}

def weights(train,season,k):
    current=train.season.eq(season)
    origins=sorted(train.loc[current,'forecast_at'].unique())[-k:]
    recent=current&train.forecast_at.isin(origins)
    raw=np.where(recent,4.,1.);w=raw*(len(raw)/raw.sum())
    return w,recent,origins

def prepare():
    OUT.mkdir(exist_ok=True)
    prior=read(CONTROL/'proposal.json');inputs=dict(prior['input_hashes'])
    for p in [Path(__file__),ROOT/'model_lab/rolling_threshold_calibration.py',CONTROL/'proposal.json',CONTROL/'verification.json',CONTROL/'metrics.csv']+[CONTROL/f'{s}_predictions.csv.gz' for s in SEASONS]:inputs[str(p.relative_to(ROOT))]=sha(p)
    spec={**prior,'id':ID,'candidate_id':'recent_round_weighted_candidate_calibration_v1',
      'hypothesis':'Giving the latest three or five causally available current-season rounds fourfold weight stabilizes 10+/12+ calibration versus equal-weight expanding calibration and raw probabilities.',
      'change':'Only sample weights change: two fixed 4x recent-round variants, normalized to mean one to keep total loss weight/L2 scale constant. Same causal rows, inputs, logistic C=1 and deadline refresh. No tuning or raw model changes.',
      'related_work':['rolling-threshold-calibration-20261017-v1','grouped-threshold-calibration-20261017-v2'],'input_hashes':inputs,
      'model_parameters':{'C':1,'max_iter':1000,'arms':ARMS,'recent_weight':4,'older_weight':1,'normalization':'sum(weights)=number of training rows','refresh':'each deadline','GW1':'exact cached rolling control; no available current-season outcomes','current_season_only':True},
      'resources':{'maximum_new_calibration_fits':148,'threads':1,'raw_model_fits':0,'bootstrap':2000},
      'decision_policy':{'forecast_only':True,'primary_focus':[10,12],'controls':['rolling','raw'],'no_promotion':True,'selection':'Evaluate both independently. No switching thresholds/seasons. If both pass all gates, prefer lower equal-season mean candidate Brier over10+/12+; exact tie prefer recent5. Otherwise no replacement.'},
      'success_criterion':'Each arm: tail gate strictly lower candidate Brier at10/12 in BOTH seasons versus BOTH rolling and raw (8). Guards: no worse candidate6/8 (8) and all-pool all4 (16) versus both controls. Stability: no worse candidate10/12 in each fixed half of each season versus rolling (8). All40 checks must pass. Report every threshold and both arms.',
      'stop_rule':'Stop on causal/hash/key/probability/convergence/weight violation. No tuning, extra weights, window changes or adaptive refitting after scores.',
      'evaluation_contract':{**prior['evaluation_contract'],
       'weighting':'Before each deadline select the latest K DISTINCT forecast origins in current season among causally eligible training rows, by timestamp (not row count or actual result). Only eligible labels receive weight. Recent raw weight4, all other history1; multiply all by N/sum(raw). Old seasons never receive recent boost. Early season uses up to K origins; GW1 unchanged. Partial outcome coverage possible and reported; unavailable labels excluded even from recent origins.',
       'controls':'Exact saved equal-weight rolling and raw probabilities from prior experiment. Same rows, cutoff, predeadline candidate flag and base forecasts. No recalibration of controls.',
       'training':'Same existing OOS history and two strict availability cutoffs as rolling control. Identical eligible row keys to previous round-lock audit at each origin. No replacement by fitted in-sample probabilities.',
       'metrics':'Separate Brier per threshold; logloss,AUC,mean probability/frequency; annual and equal-season. Fixed halves GW1-19/20-38 and per-round/leave-one-round diagnostics. Recent event counts and Kish effective sample size reported.',
       'uncertainty':'2000 paired circular4-round block draws per season; same draws across all thresholds/arms/cohorts/controls; descriptive95%, unadjusted for many comparisons.',
       'limits':'Two prior-studied development seasons; no prospective claim, no irreducible noise estimate. Negative result only rejects these two fixed 4x recipes, not every recency weighting.'}}
    # Bind the existing causal row receipts as well as their forecast files.
    for s in SEASONS:
        for gw in range(1,39):
            p=CONTROL/f'{s}_gw{gw:02d}.lock.json';spec['input_hashes'][str(p.relative_to(ROOT))]=sha(p)
    atomic_json(OUT/'proposal.json',spec)

def run():
    spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json')})
    q,labels,history=load_data();fits=0;audits=[]
    for s in SEASONS:
        ctrl=pd.read_csv(CONTROL/f'{s}_predictions.csv.gz');frames=[]
        for gw in range(1,39):
            start=time.monotonic();test=q[q.season.eq(s)&q['round'].eq(gw)].copy();at=test.forecast_at.iloc[0];assert test.forecast_at.nunique()==1
            train=history[history.can_buy&history.target_total_points.notna()&history.forecast_at.lt(at)&history.target_h1_available_at.lt(at)].copy()
            oldlock=read(CONTROL/f'{s}_gw{gw:02d}.lock.json');assert keyhash(train)==oldlock['training_key_sha256'] and len(train)==oldlock['n_train']
            c=ctrl[ctrl['round'].eq(gw)].set_index('code').loc[test.code].reset_index();assert np.array_equal(c.team_candidates,test.team_candidates)
            assert np.allclose(c[[f'raw_c{i}' for i in range(5)]],test[[f'raw_c{i}' for i in range(5)]],atol=1e-14,rtol=1e-14)
            z=c[KEY+['forecast_at','can_buy','team_candidates','position','role']+[f'{arm}_{v}' for arm in ['raw','rolling'] for v in [*[f'c{i}' for i in range(5)],*[f'p{t}' for t in TS]]]].copy()
            audit={'season':s,'round':gw,'forecast_at':str(at),'n_train':len(train),'training_key_sha256':keyhash(train),'max_train_origin':str(train.forecast_at.max()),'max_label_available':str(train.target_h1_available_at.max()),'arms':{}}
            for arm,k in ARMS.items():
                w,recent,origins=weights(train,s,k);assert np.isclose(w.sum(),len(train)) and (w>0).all()
                a={'window':k,'origins':[str(pd.Timestamp(o)) for o in origins],'recent_n':int(recent.sum()),'recent_candidates':int((recent&train.team_candidates).sum()),'effective_n':float(w.sum()**2/np.square(w).sum()),'recent_weight_share':float(w[recent].sum()/w.sum()),'weight_sum':float(w.sum()),'weight_min':float(w.min()),'weight_max':float(w.max()),'recent_events':{str(t):int((recent&train.target_total_points.ge(t)).sum()) for t in TS},'recent_candidate_events':{str(t):int((recent&train.team_candidates&train.target_total_points.ge(t)).sum()) for t in TS}}
                if len(origins)==0:
                    p=c[[f'rolling_c{i}' for i in range(5)]].to_numpy();a['mode']='reuse_no_current_outcomes'
                else:
                    with threadpool_limits(limits=1):
                        model=LogisticRegression(C=1,max_iter=1000).fit(xmatrix(train),np.searchsorted(TS,train.target_total_points,side='right'),sample_weight=w)
                        p=model.predict_proba(xmatrix(test))
                    assert list(model.classes_)==list(range(5)) and model.n_iter_.max()<1000
                    fits+=1;assert fits<=148
                    a.update(mode='fit',iterations=int(model.n_iter_.max()),coefficients=model.coef_.tolist(),intercept=model.intercept_.tolist())
                assert np.isfinite(p).all() and (p>=0).all() and np.allclose(p.sum(axis=1),1)
                for i in range(5):z[f'{arm}_c{i}']=p[:,i]
                for i,t in enumerate(TS):z[f'{arm}_p{t}']=p[:,i+1:].sum(axis=1)
                audit['arms'][arm]=a
            path=OUT/f'{s}_gw{gw:02d}.csv.gz';z.to_csv(path,index=False);audit.update(prediction_sha256=sha(path),seconds=time.monotonic()-start);atomic_json(OUT/f'{s}_gw{gw:02d}.lock.json',audit)
            for arm,a in audit['arms'].items():audits.append({'season':s,'round':gw,'arm':arm,**{k:v for k,v in a.items() if k not in ['coefficients','intercept','origins','recent_events','recent_candidate_events']},**{f'recent_events_{t}':a['recent_events'][str(t)] for t in TS},**{f'recent_candidate_events_{t}':a['recent_candidate_events'][str(t)] for t in TS}})
            frames.append(z)
            if gw%5==0 or gw==1:print('Locked',s,gw,'fits',fits,flush=True)
        pred=pd.concat(frames,ignore_index=True);pred.to_csv(OUT/f'{s}_predictions.csv.gz',index=False)
        z=pred.merge(labels,on=KEY,how='left',validate='one_to_one');z=z[z.can_buy&z.target_total_points.notna()];z.to_csv(OUT/f'{s}_scored.csv.gz',index=False)
    pd.DataFrame(audits).to_csv(OUT/'weight_audit.csv',index=False);atomic_json(OUT/'predictions_complete.json',{'fits':fits,'raw_model_fits':0,'origins':76});verify_files(ROOT,spec['input_hashes'])

def score():
    metrics=[];intervals=[];rounds=[];rng=np.random.default_rng(20261017)
    for s in SEASONS:
        z=pd.read_csv(OUT/f'{s}_scored.csv.gz');starts=rng.integers(0,38,size=(2000,10));draws=((starts[:,:,None]+np.arange(4))%38).reshape(2000,40)[:,:38]
        cohorts={'all':z,'team_candidates':z[z.team_candidates],'candidates_first_half':z[z.team_candidates&z['round'].le(19)],'candidates_second_half':z[z.team_candidates&z['round'].gt(19)]}
        for cohort,g in cohorts.items():
            for t in TS:
                y=g.target_total_points.ge(t).to_numpy(float)
                for arm in ['raw','rolling',*ARMS]:
                    p=g[f'{arm}_p{t}'].to_numpy();ll=-np.mean(y*np.log(np.clip(p,1e-12,1))+(1-y)*np.log(np.clip(1-p,1e-12,1)))
                    metrics.append(dict(season=s,cohort=cohort,threshold=t,arm=arm,n=len(g),events=int(y.sum()),predicted=p.mean(),observed=y.mean(),brier=np.mean((p-y)**2),logloss=ll,auc=roc_auc_score(y,p)))
                if cohort not in ['all','team_candidates']:continue
                for arm in ARMS:
                    for ctrl in ['rolling','raw']:
                        d=(g[f'{arm}_p{t}'].to_numpy()-y)**2-(g[f'{ctrl}_p{t}'].to_numpy()-y)**2
                        a=pd.DataFrame({'round':g['round'].to_numpy(),'d':d}).groupby('round').d.agg(['sum','count']).reindex(range(1,39),fill_value=0)
                        sums=a['sum'].to_numpy();counts=a['count'].to_numpy();b=sums[draws].sum(axis=1)/counts[draws].sum(axis=1);loo=(sums.sum()-sums)/(counts.sum()-counts)
                        intervals.append(dict(season=s,cohort=cohort,threshold=t,arm=arm,control=ctrl,delta_brier=d.mean(),lower=np.quantile(b,.025),upper=np.quantile(b,.975),leave_one_round_min=loo.min(),leave_one_round_max=loo.max(),rounds_better=int((sums<-1e-12).sum()),rounds_worse=int((sums>1e-12).sum())))
                        for gw,r in a.iterrows():rounds.append(dict(season=s,round=gw,cohort=cohort,threshold=t,arm=arm,control=ctrl,n=int(r['count']),delta_sum=r['sum'],delta_brier=r['sum']/r['count']))
    m=pd.DataFrame(metrics);m.to_csv(OUT/'metrics.csv',index=False);pd.DataFrame(intervals).to_csv(OUT/'intervals.csv',index=False);pd.DataFrame(rounds).to_csv(OUT/'per_round.csv',index=False)
    m.groupby(['cohort','threshold','arm'])[['brier','logloss','predicted','observed','auc']].mean().reset_index().to_csv(OUT/'equal_season_metrics.csv',index=False)
    gates=[]
    for (s,c,t),g in m.groupby(['season','cohort','threshold']):
        if c.startswith('candidates_') and t<10:continue
        a=g.set_index('arm').brier
        for arm in ARMS:
            for ctrl in ['rolling'] if c.startswith('candidates_') else ['rolling','raw']:
                d=a[arm]-a[ctrl];category='stability' if c.startswith('candidates_') else 'tail' if c=='team_candidates' and t>=10 else 'guard'
                gates.append(dict(season=s,cohort=c,threshold=int(t),arm=arm,control=ctrl,category=category,delta_brier=float(d),passed=bool(d<0 if category=='tail' else d<=0)))
    counts={arm:{k:dict(passed=sum(r['passed'] for r in gates if r['arm']==arm and r['category']==k),total=sum(r['arm']==arm and r['category']==k for r in gates)) for k in ['tail','guard','stability']} for arm in ARMS}
    atomic_json(OUT/'complete.json',{'passed':{arm:all(r['passed'] for r in gates if r['arm']==arm) for arm in ARMS},'categories':counts,'gates':gates,'fits':read(OUT/'predictions_complete.json')['fits'],'frozen_model_unchanged':True})
    verify_files(ROOT,read(OUT/'proposal.json')['input_hashes']);print(counts,flush=True)

if __name__=='__main__':{'prepare':prepare,'run':run,'score':score}[sys.argv[1]]()
