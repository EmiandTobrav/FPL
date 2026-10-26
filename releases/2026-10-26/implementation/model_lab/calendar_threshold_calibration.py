"""Past-only expanding calendar/candidate calibration of unchanged probabilities."""
from pathlib import Path
import sys,time
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits
from model_lab.common import ROOT,read,sha,atomic_json,verify_files,runtime
from model_lab.rolling_threshold_calibration import load_data,xmatrix as base_x,keyhash,KEY,TS,SEASONS
from model_lab import recency_threshold_calibration as scoring
OUT=ROOT/'reports/calendar_threshold_calibration_2026_10_17'
CONTROL=ROOT/'reports/rolling_threshold_calibration_2026_10_17'
ID='calendar-threshold-calibration-20261017-v1'
def xmatrix(q):
    assert q.planned_count.notna().all() and q.planned_count.ge(0).all() and q.planned_count.eq(q.planned_count.round()).all()
    return np.column_stack([base_x(q),q.planned_count.to_numpy(float)-1.])
def prepare():
    OUT.mkdir(exist_ok=True)
    prior=read(CONTROL/'proposal.json');inputs=dict(prior['input_hashes'])
    for p in [Path(__file__),ROOT/'model_lab/rolling_threshold_calibration.py',ROOT/'model_lab/recency_threshold_calibration.py',CONTROL/'proposal.json',CONTROL/'verification.json']+[CONTROL/f'{s}_predictions.csv.gz' for s in SEASONS]:inputs[str(p.relative_to(ROOT))]=sha(p)
    q,_,_=load_data();receipts=[]
    for (s,gw),g in q.groupby(['season','round']):
        folder=ROOT/'reports/fpl_improvement_2026_10_14/cache'/s/f'gw{gw:02d}'
        p=folder/'minutes_hurdle_fixture_v1.json';m=folder/'manifest.json';man=read(m)
        assert sha(p)==man['files'][p.name]
        a=read(p);counts=pd.Series(0,index=g.code) if a.get('official_all_blank_forced_wait') else pd.Series([v[0] for v in a['match_counts_by_player']],index=a['player_codes'])
        assert np.array_equal(g.code.map(counts),g.planned_count)
        assert g.forecast_at.eq(pd.Timestamp(man['forecast_at'])).all()
        for f in [p,m]:inputs[str(f.relative_to(ROOT))]=sha(f)
        receipts.append(dict(season=s,round=int(gw),n=len(g),count_values=sorted(g.planned_count.unique().tolist())))
    for s in SEASONS:
        for gw in range(1,39):
            p=CONTROL/f'{s}_gw{gw:02d}.lock.json';inputs[str(p.relative_to(ROOT))]=sha(p)
    spec={**prior,'id':ID,'candidate_id':'calendar_count_expanding_candidate_calibration_v1',
      'hypothesis':'Known planned fixture count added to expanding candidate calibration reduces threshold Brier consistently by correcting double-round underprediction.',
      'change':'One added main-effect covariate planned_count-1; existing five log raw probabilities and candidate flag unchanged. No interaction, recency weights, tuning or raw refits. Fit also at GW1 using only prior eligible history.',
      'related_work':['rolling-threshold-calibration-20261017-v1','recency-threshold-calibration-20261017-v1','calendar-probabilities-20261016-v1'],
      'input_hashes':inputs,'features':'log raw five-bin probabilities; candidate flag; planned_count-1 from archived predeadline proxy, never realized match count',
      'model_parameters':{'C':1,'max_iter':1000,'refresh':'each deadline including GW1','window':'expanding equal weights','interactions':False,'no_tuning':True},
      'resources':{'maximum_new_calibration_fits':76,'raw_model_fits':0,'threads':1,'bootstrap':2000},
      'decision_policy':{'forecast_only':True,'controls':['rolling','raw'],'no_promotion':True},
      'success_criterion':'48 checks: candidate Brier strictly better for all four thresholds in both seasons versus both controls (16); all-pool Brier no worse at each threshold/year/control (16); candidate Brier no worse in both fixed halves at all thresholds/year versus rolling (16). Retain for research only if all pass; otherwise reject this recipe as general replacement.',
      'stop_rule':'Stop on chronology, calendar reconstruction, hash, key, finite/coherent probability or convergence failure. No result-driven tuning or extra variants.',
      'evaluation_contract':{**prior['evaluation_contract'],'inference':'76 deadline fits including GW1 from strictly earlier eligible OOS history. Save forecasts and receipts before scoring. Same training keys as rolling control.',
       'controls':'Exact cached rolling and raw; equal weight, same candidates and labels.',
       'calendar':'Numeric planned_count-1, main effect only. Reconstruct against archived minute model match_counts_by_player and origin manifest for all 114 origins. Historical calendar remains existing operational proxy, not guaranteed perfect contemporaneous knowledge.',
       'subgroups':'Report single/double/blank separately, all and candidates, Brier/logloss/mean probability/frequency. Secondary descriptive diagnostics; no subgroup-based selection.',
       'limits':'2023/24 and2024/25 are previously studied development seasons; hypothesis motivated by their diagnostic. No prospective claim, no production promotion or manager benefit claim.'}}
    atomic_json(OUT/'calendar_preflight.json',{'passed':True,'origins':receipts,'rows':len(q)})
    atomic_json(OUT/'proposal.json',spec)
def run():
    spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json')})
    q,labels,history=load_data();fits=0;audits=[]
    for s in SEASONS:
        ctrl=pd.read_csv(CONTROL/f'{s}_predictions.csv.gz');frames=[]
        for gw in range(1,39):
            test=q[q.season.eq(s)&q['round'].eq(gw)].copy();at=test.forecast_at.iloc[0];assert test.forecast_at.nunique()==1
            train=history[history.can_buy&history.target_total_points.notna()&history.forecast_at.lt(at)&history.target_h1_available_at.lt(at)].copy()
            old=read(CONTROL/f'{s}_gw{gw:02d}.lock.json');assert keyhash(train)==old['training_key_sha256'] and len(train)==old['n_train']
            c=ctrl[ctrl['round'].eq(gw)].set_index('code').loc[test.code].reset_index();assert np.array_equal(c.team_candidates,test.team_candidates)
            assert np.allclose(c[[f'raw_c{i}' for i in range(5)]],test[[f'raw_c{i}' for i in range(5)]],atol=1e-14,rtol=1e-14)
            z=c[KEY+['forecast_at','can_buy','team_candidates','position','role']+[f'{arm}_{v}' for arm in ['raw','rolling'] for v in [*[f'c{i}' for i in range(5)],*[f'p{t}' for t in TS]]]].copy();z['planned_count']=test.planned_count.to_numpy()
            with threadpool_limits(limits=1):
                model=LogisticRegression(C=1,max_iter=1000).fit(xmatrix(train),np.searchsorted(TS,train.target_total_points,side='right'))
                p=model.predict_proba(xmatrix(test))
            assert list(model.classes_)==list(range(5)) and model.n_iter_.max()<1000
            fits+=1;assert fits<=76
            assert np.isfinite(p).all() and (p>=0).all() and np.allclose(p.sum(axis=1),1)
            for i in range(5):z[f'calendar_c{i}']=p[:,i]
            for i,t in enumerate(TS):z[f'calendar_p{t}']=p[:,i+1:].sum(axis=1)
            path=OUT/f'{s}_gw{gw:02d}.csv.gz';z.to_csv(path,index=False)
            a={'season':s,'round':gw,'forecast_at':str(at),'n_train':len(train),'training_key_sha256':keyhash(train),'max_train_origin':str(train.forecast_at.max()),'max_label_available':str(train.target_h1_available_at.max()),'coefficients':model.coef_.tolist(),'intercept':model.intercept_.tolist(),'iterations':int(model.n_iter_.max()),'prediction_sha256':sha(path),'train_double_n':int(train.planned_count.ge(2).sum())}
            atomic_json(OUT/f'{s}_gw{gw:02d}.lock.json',a);audits.append({k:v for k,v in a.items() if k not in ['coefficients','intercept']});frames.append(z)
            if gw==1 or gw%5==0:print('Locked',s,gw,'fits',fits,flush=True)
        pred=pd.concat(frames,ignore_index=True);pred.to_csv(OUT/f'{s}_predictions.csv.gz',index=False)
        z=pred.merge(labels,on=KEY,how='left',validate='one_to_one');z=z[z.can_buy&z.target_total_points.notna()];z.to_csv(OUT/f'{s}_scored.csv.gz',index=False)
    pd.DataFrame(audits).to_csv(OUT/'fit_audit.csv',index=False);atomic_json(OUT/'predictions_complete.json',{'fits':fits,'raw_model_fits':0,'origins':76});verify_files(ROOT,spec['input_hashes'])
def score():
    # Reuse exact established metric/bootstrap implementation; its legacy gates are auxiliary.
    scoring.OUT=OUT;scoring.ARMS={'calendar':None};scoring.score()
    m=pd.read_csv(OUT/'metrics.csv');gates=[]
    for (s,c,t),g in m.groupby(['season','cohort','threshold']):
        a=g.set_index('arm').brier
        for ctrl in ['rolling'] if c.startswith('candidates_') else ['rolling','raw']:
            d=a['calendar']-a[ctrl];gates.append(dict(season=s,cohort=c,threshold=int(t),control=ctrl,delta_brier=float(d),passed=bool(d<0 if c=='team_candidates' else d<=0)))
    atomic_json(OUT/'decision.json',{'passed':all(g['passed'] for g in gates),'passed_count':sum(g['passed'] for g in gates),'total':len(gates),'gates':gates})
    rows=[]
    for s in SEASONS:
        z=pd.read_csv(OUT/f'{s}_scored.csv.gz')
        for cohort,g in [('all',z),('team_candidates',z[z.team_candidates])]:
            for label,mask in [('blank',g.planned_count.eq(0)),('single',g.planned_count.eq(1)),('doubleplus',g.planned_count.ge(2))]:
                h=g[mask]
                if h.empty:continue
                for t in TS:
                    y=h.target_total_points.ge(t).astype(float)
                    for arm in ['raw','rolling','calendar']:
                        p=h[f'{arm}_p{t}'];rows.append(dict(season=s,cohort=cohort,calendar_group=label,threshold=t,arm=arm,n=len(h),events=int(y.sum()),predicted=p.mean(),observed=y.mean(),brier=((p-y)**2).mean(),logloss=-(y*np.log(p.clip(1e-12,1))+(1-y)*np.log((1-p).clip(1e-12,1))).mean()))
    pd.DataFrame(rows).to_csv(OUT/'calendar_metrics.csv',index=False)
    print('Primary gates',sum(g['passed'] for g in gates),'/',len(gates),flush=True)
if __name__=='__main__':{'prepare':prepare,'run':run,'score':score}[sys.argv[1]]()
