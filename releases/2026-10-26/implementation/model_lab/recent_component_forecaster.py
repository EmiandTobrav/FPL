"""Operational325-feature component with fixed180-day residual loss weights.

The original runtime and its sealed predictions remain immutable. Only the
calibration loss changes; transforms, teachers, cadence and hard guards stay.
"""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[key]='1'
from pathlib import Path
import sys,numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab import component_forecaster as core
from model_lab.common import sha,atomic_json,verify_files
P=Path(os.environ.get('FPL_COMPONENT_RELEASE',str(R/'reports/component_recent180_activation_2026_10_26')))
D=core.D;FIT=core.FIT;SEASON=core.SEASON;REFITS=core.REFITS;HALF_LIFE_DAYS=180.
MODEL_ID='common_component_h8_recent180_adaptive_v1'
read=core.read;load=core.load;save=core.save;utc=core.utc;common=core.common;projection=core.projection;hard_manager=core.hard_manager

def prepare():core.P=P;return core.prepare()
def fit_base(g):core.P=P;return core.fit_base(g)
def reuse_base(g):core.P=P;return core.reuse_base(g)

def fit_recent(tr,j,at):
    raw,anchor,names=projection.design(tr,'component',j);x,transform=projection.transform(raw)
    age=(at-tr.forecast_at).dt.total_seconds().to_numpy()/86400
    if not np.all(age>0):raise ValueError('Future calibration teacher')
    w=np.exp2(-age/HALF_LIFE_DAYS);pen=np.eye(x.shape[1])*.01;pen[0,0]=0
    y=(tr[f'y_{j}'].to_numpy(float)-anchor)/6
    beta=np.linalg.solve(x.T@(w[:,None]*x)/w.sum()+pen,x.T@(w*y)/w.sum())
    model=dict(beta=beta.tolist(),transform=transform,raw_names=names,offset=j,penalty=.01,rows=len(tr),base_model='component',half_life_days=HALF_LIFE_DAYS,transform_policy='exact same unweighted training-only transform as control; only residual objective sample weights change',effective_rows=float(w.sum()**2/(w@w)),fitted_at=str(at),teacher_keys_sha256=common.keys_hash(tr),current_season_weight=float(w[tr.season.eq(SEASON).to_numpy()].sum()/w.sum()))
    return model,w

def fit_heads():
    current=load(P/'current.pkl');info=read(P/'prepared.json');g=info['round']
    if info['previous_release']:
        prior=load(P/'prior_oof.pkl');basecols=common.KEY+['component_p1','component_m1','component_p3','component_m3'];prior=current[current['round'].lt(g)].merge(prior[basecols],on=common.KEY,how='inner',validate='one_to_one');q=pd.concat([prior,load(P/f'base_gw{g:02d}.pkl')],ignore_index=True)
    else:q=pd.concat([load(P/f'base_gw{r:02d}.pkl') for r in [1,5,g]],ignore_index=True)
    assert not q.duplicated(common.KEY).any();save(P/'current_oof.pkl',q)
    past=pd.read_pickle(FIT/'head_data.pkl');teacher=pd.concat([past,q],ignore_index=True);at=q[q['round'].eq(g)].forecast_at.iloc[0]
    complete=teacher[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=teacher[[f'y_at_{j}' for j in range(3)]].max(axis=1);out=q[q['round'].eq(g)].copy();audits=[];heads={}
    for j in range(8):
        tr=teacher[teacher.teacher_eligible&teacher.forecast_at.lt(at)&teacher[f'y_{j}'].notna()&teacher[f'y_at_{j}'].lt(at)&complete&h3.lt(at)].copy()
        if info['previous_release'] and g not in REFITS:
            model=read(R/info['previous_release']/'heads.json')[str(j)]
            if model.get('half_life_days')!=HALF_LIFE_DAYS:raise ValueError('Calibration recipe change requires an explicit refit')
            reused=True
        else:model,_=fit_recent(tr,j,at);reused=False
        heads[j]=model;out[f'xp_{j}']=projection.predict_projection(out,'component',model)
        audits.append(dict(offset=j,cutoff=str(at),fitted_at=model['fitted_at'],rows=model['rows'],current_trainable_rows=len(tr),current_rows=int(tr.season.eq(SEASON).sum()),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'y_at_{j}'].max()),max_h3_label=str(h3.loc[tr.index].max()),keys_sha256=model['teacher_keys_sha256'],reused_between_refits=reused,half_life_days=HALF_LIFE_DAYS,current_season_weight=model['current_season_weight']))
        mask=out.known_departed|(out.confirmed_out_current if j==0 else False);out.loc[mask,f'xp_{j}']=0.
    atomic_json(P/'heads.json',{str(k):v for k,v in heads.items()});atomic_json(P/'head_audit.json',audits);save(P/'live_features.pkl',out)
    out[common.KEY+['forecast_at','name','position','club','price_tenths','can_buy','confirmed_out_current','known_departed']+[f'can_start_{j}' for j in range(8)]+[f'xp_{j}' for j in range(8)]].to_csv(P/'forecasts.csv',index=False)
    assert np.isfinite(out[[f'xp_{j}' for j in range(8)]]).all().all()
    context=R/'datasets/fpl_all_competitions_context_v1/manifest.json'
    files=[P/n for n in ['forecasts.csv','live_features.pkl','heads.json','head_audit.json','prepared.json','current_oof.pkl','current.pkl','native_current.pkl','timing.csv.gz','origins.json','raw/receipts.json']]+list((P/'models').glob('*.pkl'))+[Path(__file__),R/'model_lab/component_forecaster.py',R/'scripts/common_season_comparison.py',context]
    atomic_json(P/'forecast_seal.json',dict(model=MODEL_ID,issued_at=str(at),sealed_at=str(pd.Timestamp.now(tz='UTC')),source_capture_reused=bool(info.get('source_capture_reused')),deadline=info['deadline'],round=g,prospective=True,files={str(p.relative_to(R)):sha(p) for p in files},teacher_clock='origin, offset label and all H3 teacher outcomes strictly before fit',refits=list(REFITS),expiry_hours=24,calibration_half_life_days=HALF_LIFE_DAYS,external_context_created_at=read(context)['created_at']))

class ComponentForecaster(core.ComponentForecaster):
    def __init__(self,release=P):super().__init__(release)
    def forecast(self,origin,horizon=8):
        seal=read(self.release/'forecast_seal.json')
        if seal.get('model')!=MODEL_ID or seal.get('calibration_half_life_days')!=HALF_LIFE_DAYS:raise ValueError('Wrong calibration recipe')
        now=utc(origin['forecast_at']);external=utc(seal['external_context_created_at'])
        if now<external or now-external>pd.Timedelta(hours=24):raise ValueError('Refresh and integrate external club/national feeds before recommending a team')
        frame,audit=super().forecast(origin,horizon);audit.update(model=MODEL_ID,calibration_half_life_days=HALF_LIFE_DAYS);return frame,audit

if __name__=='__main__':
    action=sys.argv[1]
    if action=='prepare':prepare()
    elif action=='base':fit_base(int(sys.argv[2]))
    elif action=='heads':fit_heads()
    elif action=='reuse-base':reuse_base(int(sys.argv[2]))
    else:raise SystemExit('prepare | base ROUND | heads | reuse-base ROUND')
