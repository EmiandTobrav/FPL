"""Locked chronological comparison of beta tails, conditional calibration and blend."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits
from model_lab.common import ROOT,read,sha,atomic_json,verify_files,runtime
from model_lab.rolling_threshold_calibration import load_data,keyhash,KEY,TS,SEASONS
from model_lab.calendar_threshold_calibration import xmatrix as calendar_x
from model_lab import recency_threshold_calibration as scoring
P=ROOT/'reports/outlier_probability_methods_2026_10_17';CTRL=ROOT/'reports/calendar_threshold_calibration_2026_10_17'
ARMS=['beta','conditional','blend'];ID='outlier-probability-methods-20261017-v1'
def beta_x(q,t):
 p=np.clip(q[f'raw_p{t}'].to_numpy(),1e-12,1-1e-12)
 return np.column_stack([np.log(p),np.log1p(-p),q.team_candidates.astype(float),q.planned_count-1.])
def conditional_x(q):
 logs=np.log(q[[f'raw_c{i}' for i in range(5)]].clip(1e-12,1).to_numpy());cand=q.team_candidates.to_numpy(float);count=q.planned_count.to_numpy(float)-1
 return np.column_stack([calendar_x(q),logs*cand[:,None],logs*count[:,None],cand*count])
def project(p):
 # Equal-weight least-squares projection onto nonincreasing thresholds.
 v=-np.asarray(p);out=np.zeros_like(v)
 for i in range(4):out[:,i]=np.max(np.column_stack([np.min(np.column_stack([v[:,a:b+1].mean(axis=1) for b in range(i,4)]),axis=1) for a in range(i+1)]),axis=1)
 return -out
def classes(p):return np.column_stack([1-p[:,0],p[:,:-1]-p[:,1:],p[:,-1]])
def prepare():
 P.mkdir(exist_ok=True)
 # Projection mechanics only, no outcomes or model selection.
 assert np.allclose(project(np.array([[.8,.2,.6,.1],[.8,.7,.2,.1]])),[[.8,.4,.4,.1],[.8,.7,.2,.1]])
 prior=read(CTRL/'proposal.json');deps=dict(prior['input_hashes'])
 paths=[Path(__file__),CTRL/'proposal.json',CTRL/'verification.json',ROOT/'model_lab/calendar_threshold_calibration.py',ROOT/'model_lab/recency_threshold_calibration.py']+[CTRL/f'{s}_{n}.csv.gz' for s in SEASONS for n in ['predictions','scored']]
 paths+=[CTRL/f'{s}_gw{g:02d}.lock.json' for s in SEASONS for g in range(1,39)]
 # Preserve the newly sealed prospective forecasts explicitly.
 paths += [ROOT/'reports/calendar_gw7_2026_10_17'/n for n in ['gw07_lock.json','gw07_predictions.csv.gz','delivery_lock.json']]
 deps.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
 spec={**prior,'id':ID,'candidate_id':'beta_conditional_calendar_outlier_probabilities_v1','hypothesis':'Direct threshold beta calibration or group/calendar-dependent probability slopes improve proper tail scores and actual outlier capture beyond main-effect calendar calibration.',
 'change':'Three fixed arms: four binary beta calibrators with monotone Euclidean projection; conditional multinomial with candidate and count interactions with log raw probabilities; equal50/50 mixture of their five-class probabilities. No raw fits, tuning, new data or alteration of prospective forecasts.',
 'related_work':['calendar-threshold-calibration-20261017-v1','grouped-threshold-calibration-20261017-v2','recency-threshold-calibration-20261017-v1'],
 'input_hashes':deps,'features':'beta: log(p),log(1-p),candidate,count-1 for each raw tail; conditional: original7 fields +5 logclass*candidate +5 logclass*(count-1) +candidate*(count-1). No roles or new features.',
 'model_parameters':{'C':1,'max_iter':1000,'equal_weights':True,'cadence':'every deadline incl GW1','blend_weights':[.5,.5],'beta_projection':'Equal-weight L2 isotonic nonincreasing tails, fixed at inference; no target access','arms':ARMS},
 'resources':{'maximum_calibration_fits':380,'raw_model_fits':0,'threads':1,'bootstrap':2000},
 'decision_policy':{'primary':'probability quality','secondary':'outlier capture at fixed selection budget','controls':['calendar','raw'],'no_promotion':True},
 'success_criterion':'Per arm52 gates: candidate annual Brier strictly lower at all4 thresholds in both years vs calendar and raw(16); all-pool no worse vs both(16); candidate fixed-half Brier no worse vs calendar(16); top10 observed10+/12+ hits no lower in each year vs calendar(4), with unknown outcomes and equal budgets reported. Retain only all52. Logloss,AUC,top55,within-position capture descriptive; no selection of threshold/year/arm based on results.',
 'stop_rule':'Stop on causal/hash/key/convergence/probability violation; no result-driven changes or extra variants.',
 'evaluation_contract':{**prior['evaluation_contract'],'controls':'Exact cached calendar and raw outputs. Same unchanged predeadline fixed candidates and known labels.','ranking':'Choose top10 and top55 buyable forecasts per threshold and round BEFORE label join, descending probability then code; report unknown selected outcomes separately. Count actual hits, precision among known and recall of all known events; fixed equal budgets, no excluded-outcome replacement. Also report top3 per position separately, descriptive.','uncertainty':'2000 paired circular4-round bootstrap for Brier and capture differences; descriptive and unadjusted. Leave-one-round Brier and ranking differences.','limits':'Already studied2023/24 and2024/25 development seasons. Hypotheses informed by existing diagnostics. No prospective scores or modification of sealed GW7. Role-only/combined calibration already failed; new interaction is conditional on probabilities and calendar, not repetition of role flags.'}}
 atomic_json(P/'proposal.json',spec)
def run():
 spec=read(P/'proposal.json');verify_files(ROOT,spec['input_hashes']);atomic_json(P/'started.json',{'runtime':runtime(),'proposal_sha256':sha(P/'proposal.json')})
 q,labels,history=load_data();fits=0
 for s in SEASONS:
  control=pd.read_csv(CTRL/f'{s}_predictions.csv.gz');frames=[]
  for gw in range(1,39):
   test=q[q.season.eq(s)&q['round'].eq(gw)];at=test.forecast_at.iloc[0];train=history[history.can_buy&history.target_total_points.notna()&history.forecast_at.lt(at)&history.target_h1_available_at.lt(at)]
   receipt=read(CTRL/f'{s}_gw{gw:02d}.lock.json');assert keyhash(train)==receipt['training_key_sha256'] and len(train)==receipt['n_train']
   c=control[control['round'].eq(gw)].set_index('code').loc[test.code].reset_index();assert np.array_equal(c.team_candidates,test.team_candidates) and np.array_equal(c.planned_count,test.planned_count)
   assert np.allclose(c[[f'raw_c{i}' for i in range(5)]],test[[f'raw_c{i}' for i in range(5)]],atol=1e-14,rtol=1e-14)
   z=c.copy();audit={'season':s,'round':gw,'forecast_at':str(at),'n_train':len(train),'training_key_sha256':keyhash(train),'max_train_origin':str(train.forecast_at.max()),'max_label_available':str(train.target_h1_available_at.max()),'models':{}}
   tails=[]
   for t in TS:
    with threadpool_limits(limits=1):model=LogisticRegression(C=1,max_iter=1000).fit(beta_x(train,t),train.target_total_points.ge(t));p=model.predict_proba(beta_x(test))[:,1]
    assert model.n_iter_.max()<1000 and len(model.classes_)==2;fits+=1;tails.append(p);audit['models'][f'beta{t}']={'coefficients':model.coef_.tolist(),'intercept':model.intercept_.tolist(),'iterations':int(model.n_iter_.max())}
   unprojected=np.column_stack(tails);bt=project(unprojected);probs={'beta':classes(bt)};audit['crossing_rows_before_projection']=int((np.diff(unprojected,axis=1)>0).any(axis=1).sum())
   with threadpool_limits(limits=1):model=LogisticRegression(C=1,max_iter=1000).fit(conditional_x(train),np.searchsorted(TS,train.target_total_points,side='right'));probs['conditional']=model.predict_proba(conditional_x(test))
   assert model.n_iter_.max()<1000 and list(model.classes_)==list(range(5));fits+=1;assert fits<=380
   audit['models']['conditional']={'coefficients':model.coef_.tolist(),'intercept':model.intercept_.tolist(),'iterations':int(model.n_iter_.max())}
   probs['blend']=.5*(probs['beta']+probs['conditional'])
   for arm,p in probs.items():
    assert np.isfinite(p).all() and (p>=-1e-14).all() and np.allclose(p.sum(axis=1),1)
    for i in range(5):z[f'{arm}_c{i}']=p[:,i]
    for i,t in enumerate(TS):z[f'{arm}_p{t}']=p[:,i+1:].sum(axis=1)
   path=P/f'{s}_gw{gw:02d}.csv.gz';z.to_csv(path,index=False);audit['prediction_sha256']=sha(path);atomic_json(P/f'{s}_gw{gw:02d}.lock.json',audit);frames.append(z)
   if gw==1 or gw%5==0:print('Locked',s,gw,'fits',fits,flush=True)
  pred=pd.concat(frames,ignore_index=True);pred.to_csv(P/f'{s}_predictions.csv.gz',index=False);z=pred.merge(labels,on=KEY,how='left',validate='one_to_one');z=z[z.can_buy&z.target_total_points.notna()];z.to_csv(P/f'{s}_scored.csv.gz',index=False)
 atomic_json(P/'predictions_complete.json',{'fits':fits,'raw_model_fits':0});verify_files(ROOT,spec['input_hashes'])
def score():
 # Reuse metric implementation, mapping its control name rolling to calendar in temporary in-memory reads.
 original=pd.read_csv
 def reader(path,*a,**kw):
  z=original(path,*a,**kw)
  if str(path).startswith(str(P)) and str(path).endswith('_scored.csv.gz'):
   for suffix in [*[f'c{i}' for i in range(5)],*[f'p{t}' for t in TS]]:z['rolling_'+suffix]=z['calendar_'+suffix]
  return z
 scoring.OUT=P;scoring.ARMS={a:None for a in ARMS};pd.read_csv=reader
 try:scoring.score()
 finally:pd.read_csv=original
 # Relabel this module's imported control name explicitly in result tables.
 for name in ['metrics','intervals','per_round','equal_season_metrics']:
  z=pd.read_csv(P/f'{name}.csv')
  for col in ['arm','control']:
   if col in z:z[col]=z[col].replace({'rolling':'calendar'})
  z.to_csv(P/f'{name}.csv',index=False)
 rankings=[];chosen_rows=[];intervals=[]
 for s in SEASONS:
  pred=pd.read_csv(P/f'{s}_predictions.csv.gz');labels=pd.read_csv(P/f'{s}_scored.csv.gz',usecols=KEY+['target_total_points']);pool=pred[pred.can_buy]
  for t in TS:
   total=int(labels.target_total_points.ge(t).sum())
   for arm in ['raw','calendar',*ARMS]:
    for label,n,group in [('top10',10,['round']),('top55',55,['round']),('top3_position',3,['round','position'])]:
     pick=pool.sort_values(['round',f'{arm}_p{t}','code'],ascending=[True,False,True]).groupby(group,sort=False).head(n)
     z=pick.merge(labels,on=KEY,how='left',validate='one_to_one');known=z.target_total_points.notna();hit=z.target_total_points.ge(t)
     rankings.append(dict(season=s,threshold=t,arm=arm,selection=label,selected=len(z),known=int(known.sum()),missing=int((~known).sum()),hits=int(hit.sum()),precision=float(hit.sum()/known.sum()),recall=float(hit.sum()/total)))
     for gw,g in z.groupby('round'):chosen_rows.append(dict(season=s,round=int(gw),threshold=t,arm=arm,selection=label,hits=int(g.target_total_points.ge(t).sum()),known=int(g.target_total_points.notna().sum())))
  rng=np.random.default_rng(20261017);starts=rng.integers(0,38,size=(2000,10));draws=((starts[:,:,None]+np.arange(4))%38).reshape(2000,40)[:,:38]
  cr=pd.DataFrame(chosen_rows);cr=cr[cr.season.eq(s)]
  for (t,sel),g in cr.groupby(['threshold','selection']):
   piv=g.pivot(index='round',columns='arm',values='hits').reindex(range(1,39),fill_value=0)
   for arm in ARMS:
    d=(piv[arm]-piv['calendar']).to_numpy();b=d[draws].sum(axis=1);intervals.append(dict(season=s,threshold=t,selection=sel,arm=arm,delta_hits=int(d.sum()),lower=float(np.quantile(b,.025)),upper=float(np.quantile(b,.975)),leave_one_round_min=int((d.sum()-d).min()),leave_one_round_max=int((d.sum()-d).max())))
 r=pd.DataFrame(rankings);r.to_csv(P/'ranking.csv',index=False);pd.DataFrame(chosen_rows).to_csv(P/'ranking_rounds.csv',index=False);pd.DataFrame(intervals).to_csv(P/'ranking_intervals.csv',index=False)
 m=pd.read_csv(P/'metrics.csv');gates=[]
 for (s,c,t),g in m.groupby(['season','cohort','threshold']):
  a=g.set_index('arm').brier
  for arm in ARMS:
   for ctrl in ['calendar'] if c.startswith('candidates_') else ['calendar','raw']:
    d=a[arm]-a[ctrl];gates.append(dict(arm=arm,season=s,cohort=c,threshold=int(t),control=ctrl,category='probability',delta=float(d),passed=bool(d<0 if c=='team_candidates' else d<=0)))
 for (s,t),g in r[r.selection.eq('top10')&r.threshold.ge(10)].groupby(['season','threshold']):
  a=g.set_index('arm').hits
  for arm in ARMS:gates.append(dict(arm=arm,season=s,threshold=int(t),category='capture',delta=int(a[arm]-a['calendar']),passed=bool(a[arm]>=a['calendar'])))
 result={a:{'passed':all(g['passed'] for g in gates if g['arm']==a),'passed_count':sum(g['passed'] for g in gates if g['arm']==a),'total':sum(g['arm']==a for g in gates)} for a in ARMS}
 atomic_json(P/'decision.json',{'arms':result,'gates':gates});verify_files(ROOT,read(P/'proposal.json')['input_hashes']);print(result,flush=True)
if __name__=='__main__':{'prepare':prepare,'run':run,'score':score}[sys.argv[1]]()
