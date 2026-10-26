"""Registered factorial fourth cell: qualified xG bases plus fixed recent180 heads.

No new base fits, data changes, parameter search or live activation.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[k]='1'
import sys,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import test_xg_adaptation as t
t.P=R/'reports/combined_xg_adaptation_2026_10_26';t.D=R/'datasets/fpl_common_training_v5'
t.ARMS=['xg_only','recent_only','combined']
P=t.P;D=t.D;OLD=R/'reports/xg_adaptation_2026_10_26_v2';ID='component-xg-recent-combined-20261026-v1'
import numpy as np,pandas as pd
from model_lab.common import atomic_json,sha,verify_files

def prepare():
    P.mkdir(exist_ok=False)
    parent=t.read(OLD/'proposal.json');spec={k:v for k,v in parent.items() if k not in ['input_hashes','id','candidate_id','fingerprint','registered_at_utc']}
    deps=dict(parent['input_hashes'])
    for path in [Path(__file__),OLD/'proposal.json',OLD/'result.json',OLD/'final_verification.json',OLD/'head_data_xg_only.pkl',OLD/'prediction_verification_xg_only.json',D/'release.json',R/'scripts/report_xg_adaptation.py',R/'scripts/verify_xg_adaptation.py']+list(OLD.glob('base_*.pkl'))+list(OLD.glob('base_audit_*.csv'))+list(OLD.glob('scores_*.csv'))+[OLD/n for n in ['xg_only.csv.gz','recent_only.csv.gz','dataset_verification.json','population_verification.json','interval_verification.json','manager_verification_control.json','manager_verification_xg_only.json','manager_verification_recent_only.json']]:deps[str(path.relative_to(R))]=sha(path)
    for s in t.S:
        for row in pd.read_csv(OLD/f'base_audit_{s}.csv').itertuples():
            assert sha(R/row.file)==row.sha256;deps[row.file]=row.sha256
    spec.update(id=ID,candidate_id='component_qualified_xg_and_recent180_combined_v1',input_hashes=deps,
        hypothesis='Combining the already qualified xG bases with the unchanged180-day residual calibration weights improves full-season utility beyond the current component and shows whether the two separately measured effects reinforce each other.',
        change='Fourth factorial cell only: exact frozen341-feature xG base forecasts from qualifiedV2 plus the exact recent180 sample-weight formula and unweighted train-only transformations. Teacher IDs, completed-H3 filters, quarterly updates, Ridge.01 and all manager resources unchanged. No combined models previously scored; no tuning, base refits or live activation.',
        related_work=['component-xg-adaptation-20261026-v2','component-h1-calibration-probe-20261026-v1'],
        features=dict(combined=341,control=325,xg_only=341,recent_only=325,dataset='qualifiedV5; identical targets and keys'),
        resources=dict(new_base_fits=0,reused_verified_base_packages=80,new_projection_heads=240,new_season_attempts=3,new_manager_decisions=114,preflight_decisions=2,workers=3,threads=1),
        success_criterion='Primary: combined strictly higher net-after-hits than frozen current component in every one of3 seasons. Separately report combined vs each single variant and the descriptive factorial interaction C-X-R+B for each season. Claim improvement over both singles only if strictly better than each in every season. Point/minute MSE and candidate rank remain distinct claims and require yearly improvement for any broad forecast improvement claim.',
        stop_rule='One fixed combined candidate, no score-driven reruns, source relaxation, half-life tuning or activation. Stop on any hash, clock, legality or resource failure; preserve all outputs.',
        evaluation_contract=dict(primary_metric='net full-season points after hits, each year',secondary_metrics='four-arm H1/H3 points and minute MSE, common candidate rank and premium bias; descriptive factorial interaction',evidence_role='Retrospective development comparison; all3seasons already inspected; prospective2026 forecasts untouched'))
    atomic_json(P/'proposal.json',spec)
    for name in ['dataset_verification.json','population_verification.json','interval_verification.json','xg_only.csv.gz','recent_only.csv.gz']+[f'base_{s}.pkl' for s in t.S]+[f'base_audit_{s}.csv' for s in t.S]+[f'scores_{a}.csv' for a in ['control','xg_only','recent_only']]:shutil.copyfile(OLD/name,P/name)
    print('COMBINED PLAN PREPARED; no new training',flush=True)

def heads():
    t.check();d=t.load(OLD/'head_data_xg_only.pkl');complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=d[[f'y_at_{j}' for j in range(3)]].max(axis=1);teacher=pd.read_csv(t.F/'head_audit.csv');out=[];audits=[]
    for s in t.EVAL:
        for g in range(1,39):
            q=d[d.season.eq(s)&d['round'].eq(g)];at=q.forecast_at.iloc[0]
            if g in t.REFITS:
                models={}
                for j in range(8):
                    tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&h3.lt(at)].copy();control=teacher[teacher.season.eq(s)&teacher['round'].eq(g)&teacher.offset.eq(j)].iloc[0];assert len(tr)==control.rows and t.common.keys_hash(tr)==control.keys_sha256
                    model,w=t.fit_recent(tr,j,at);model['current_season_weight']=float(w[tr.season.eq(s).to_numpy()].sum()/w.sum());models[j]=model;path=P/f'heads/combined_{s}_gw{g:02d}_j{j}.json';atomic_json(path,model)
                    audits.append(dict(arm='combined',season=s,round=g,offset=j,cutoff=str(at),rows=len(tr),keys_sha256=t.common.keys_hash(tr),same_keys_as_control=True,current_rows=int(tr.season.eq(s).sum()),current_weight=model['current_season_weight'],max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'y_at_{j}'].max()),max_h3_label=str(h3.loc[tr.index].max()),file=str(path.relative_to(R)),sha256=sha(path)))
                print('COMBINED HEADS',s,g,flush=True)
            z=q[t.KEY+['forecast_at','can_buy']].copy()
            for j in range(8):z[f'xp_{j}']=t.projection.predict_projection(q,'component',models[j]) if g+j<=38 else 0.
            out.append(z)
    f=pd.concat(out,ignore_index=True);av=pd.read_csv(t.F/'availability.csv.gz');f=f.merge(av[t.KEY+['model_can_buy','known_departed','confirmed_out_current']],on=t.KEY,validate='one_to_one');f.can_buy=f.model_can_buy
    for j in range(8):f.loc[f.known_departed|(f.confirmed_out_current if j==0 else False),f'xp_{j}']=0.
    f.drop(columns=['model_can_buy','known_departed','confirmed_out_current']).to_csv(P/'combined.csv.gz',index=False);pd.DataFrame(audits).to_csv(P/'head_audit_combined.csv',index=False);t.save(P/'head_data_combined.pkl',d);atomic_json(P/'prediction_lock_combined.json',dict(sealed_before_manager=True,files={n:sha(P/n) for n in ['combined.csv.gz','head_audit_combined.csv','head_data_combined.pkl']}))

def verify():
    t.check();verify_files(P,t.read(P/'prediction_lock_combined.json')['files']);parent=t.read(OLD/'final_verification.json');assert parent['passed'];verify_files(R,parent['files']);assert t.read(OLD/'prediction_verification_xg_only.json')['base_fits_replayed']==80
    d=t.load(P/'head_data_combined.pkl');pd.testing.assert_frame_equal(d,t.load(OLD/'head_data_xg_only.pkl'));a=pd.read_csv(P/'head_audit_combined.csv');f=pd.read_csv(P/'combined.csv.gz').set_index(t.KEY);av=pd.read_csv(t.F/'availability.csv.gz').set_index(t.KEY);teacher=pd.read_csv(t.F/'head_audit.csv');complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=d[[f'y_at_{j}' for j in range(3)]].max(axis=1);grad=[];count=0
    for row in a.itertuples():
        at=pd.Timestamp(row.cutoff);j=row.offset;tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&h3.lt(at)];old=teacher[teacher.season.eq(row.season)&teacher['round'].eq(row.round)&teacher.offset.eq(j)].iloc[0];assert len(tr)==row.rows==old.rows and t.common.keys_hash(tr)==row.keys_sha256==old.keys_sha256
        assert tr.forecast_at.max()<at and tr[f'y_at_{j}'].max()<at and h3.loc[tr.index].max()<at
        model=t.read(R/row.file);assert sha(R/row.file)==row.sha256;raw,anchor,names=t.projection.design(tr,'component',j);x,transform=t.projection.transform(raw)
        for field in ['median','mean','std']:np.testing.assert_allclose(model['transform'][field],transform[field],atol=1e-10,rtol=1e-10)
        age=(at-tr.forecast_at).dt.total_seconds().to_numpy()/86400;assert np.all(age>0);w=2.**(-age/180.);res=(tr[f'y_{j}'].to_numpy()-anchor)/6;beta=np.array(model['beta']);pen=.01*beta;pen[0]=0;gradient=x.T@(w*(x@beta-res))/w.sum()+pen;assert abs(gradient).max()<1e-8;grad.append(float(abs(gradient).max()))
        q=d[d.season.eq(row.season)&d['round'].between(row.round,min(row.round+3,38))];q=q[q['round']+j<=38];v=t.projection.predict_projection(q,'component',model);blocked=av.reindex(pd.MultiIndex.from_frame(q[t.KEY]));mask=blocked.known_departed.to_numpy()|(blocked.confirmed_out_current.to_numpy() if j==0 else False);v[mask]=0;np.testing.assert_allclose(v,f.reindex(pd.MultiIndex.from_frame(q[t.KEY]))[f'xp_{j}'].to_numpy(),atol=1e-9,rtol=1e-10);count+=len(q)
    assert len(a)==240 and np.isfinite(f[[f'xp_{j}' for j in range(8)]]).all().all()
    atomic_json(P/'prediction_verification_combined.json',dict(passed=True,heads_checked=240,replayed_forecast_values=count,identical_qualified_xg_bases=True,verified_parent_base_packages=80,all_teacher_keys_and_clocks_checked=True,same_unweighted_xg_transforms_only_weights_changed=True,half_life_days=180,max_normal_equation_gradient=max(grad),parent_verification_sha256=sha(OLD/'final_verification.json')));print('COMBINED PREDICTIONS INDEPENDENTLY VERIFIED',flush=True)

def preflight():
    from scripts import verify_xg_adaptation as v
    v.preflight('combined')

def replay():
    from scripts import report_xg_adaptation as r
    r.managers('combined')

def metrics():
    from scripts import report_xg_adaptation as r
    r.metrics()

def finish():
    t.check()
    for n in ['prediction_verification_combined.json','preflight_combined.json','manager_verification_combined.json']:assert t.read(P/n)['passed']
    scores=pd.concat([pd.read_csv(P/f'scores_{a}.csv') for a in ['control']+t.ARMS]);scores.to_csv(P/'scores.csv',index=False);w=scores.pivot(index='season',columns='arm',values='net');w['combined_vs_control']=w.combined-w.control;w['combined_vs_xg']=w.combined-w.xg_only;w['combined_vs_recent']=w.combined-w.recent_only;w['interaction']=w.combined-w.xg_only-w.recent_only+w.control;w.to_csv(P/'comparison.csv')
    m=pd.read_csv(P/'forecast_metrics.csv');assert m.groupby(['season','scope','target','horizon']).n.nunique().eq(1).all();assert len(m)==192
    gate=bool((w.combined>w.control).all());singles=bool(((w.combined>w.xg_only)&(w.combined>w.recent_only)).all())
    artifacts=list(P.glob('*.csv'))+[P/n for n in ['prediction_verification_combined.json','preflight_combined.json','manager_verification_combined.json','prediction_lock_combined.json']]
    atomic_json(P/'final_verification.json',dict(passed=True,new_full_episodes=3,new_decisions_independently_replayed=114,reused_verified_reference_episodes=9,reference_decisions_verified_in_parent=342,new_base_fits=0,reused_qualified_base_packages=80,new_projection_heads=240,net_gate=gate,beats_both_singles_each_year=singles,all_matched_denominators=True,active_model_unchanged=True,files={str(p.relative_to(R)):sha(p) for p in artifacts}));print(w.to_string(),flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='prepare':prepare()
    elif action=='heads':heads()
    elif action=='verify':verify()
    elif action=='preflight':preflight()
    elif action=='manager':t.manager(sys.argv[2],'combined')
    elif action=='replay':replay()
    elif action=='metrics':metrics()
    elif action=='finish':finish()
    else:raise ValueError(action)
