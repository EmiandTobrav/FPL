"""Prepare, check and publish explicit user selection of recent180 component."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,shutil,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab import recent_component_forecaster as c
from model_lab.common import sha,atomic_json,verify_files
import numpy as np,pandas as pd
P=c.P;OLD=R/'reports/component_operational_activation_2026_10_26';RESEARCH=R/'reports/xg_adaptation_2026_10_26_v2';ID='component-recent180-operational-20261026-v1'

def prepare():
    previous=c.read(P/'previous_overview_ACTIVE_TEAM_BENCHMARK.json');source=c.read(RESEARCH/'proposal.json')
    deps=[Path(__file__),R/'model_lab/recent_component_forecaster.py',R/'model_lab/component_forecaster.py',R/'scripts/common_season_comparison.py',R/'scripts/common_model_retest.py',P/'proposed_active.py',P/'proposed_refresh_component_release.py',P/'previous_model_lab_active.py',P/'previous_scripts_refresh_component_release.py',P/'previous_overview_ACTIVE_TEAM_BENCHMARK.json',R/'datasets/fpl_2026_27_best_effort_v1/manifest.json',c.D/'manifest.json',RESEARCH/'scores_recent_only.csv',RESEARCH/'scores_control.csv',RESEARCH/'head_audit_recent_only.csv',RESEARCH/'head_data_recent_only.pkl',RESEARCH/'prediction_verification_recent_only.json',OLD/'forecast_seal.json',OLD/'prepared.json',OLD/'current.pkl',OLD/'current_oof.pkl']+[R/p for p in c.read(OLD/'forecast_seal.json')['files']]+[R/p for p in c.read(R/'reports/matched_season_retest_2026_10_26_v8/policy_backend_hashes.json')]
    # Backend hash file is also checked by its existing solver factory.
    deps=[p for p in deps if p.is_file()]
    backend=R/'reports/matched_season_retest_2026_10_26_v8'
    deps+=[backend/'policy_backend_hashes.json']+[backend/'policy_backend'/name for name in c.read(backend/'policy_backend_hashes.json')]
    spec=dict(id=ID,candidate_id='operational_component_recent180_v1',dataset_id=source['dataset_id'],benchmark_id=previous['id'],hypothesis='Explicit user selection prefers the existing recent180-only candidate based on newer-season gains, accepting the2023 loss; operational implementation must match the frozen research recipe exactly.',change='No new model selection, xG, base fit, hyperparameter change or season replay. Reuse exact325-feature qualified current/base sources, fit8 operational weighted heads, independently reproduce240 historical heads, retain original cadence and hard guards. Publish selected recipe after checks. Existing source capture keeps original receipts/cutoff; stale external feeds block new recommendations.',related_work=['component-xg-adaptation-20261026-v2','component-xg-recent-combined-20261026-v1'],clock=source['clock'],features=dict(operational=325,xg=False,unchanged_base=True),model_parameters=source['model_parameters'],decision_policy=source['decision_policy'],seasons=source['seasons'],resources=dict(new_base_fits=0,live_heads=8,historical_parity_solves=240,manager_preflights=2,new_season_replays=0,threads=1),maximum_runs=1,input_hashes={str(p.relative_to(R)):sha(p) for p in deps},success_criterion='All operational numerical/clock/source/availability and dispatcher checks pass; live weights match frozen recent180-only heads and same four-round reuse policy. User explicitly waives previous all-three-season strict-win selection gate; it remains failed in original research. Current recommendations must fail closed if feeds are expired.',stop_rule='No tuning, score-driven rerun or freshness bypass. Preserve old runtime/seal/source times and exact previous routing/descriptor. An expired data capture may support recipe activation only with refresh_required status, never an actionable current team recommendation.',user_authority='2026-10-26: user explicitly asks to make faster calibration the standard despite2023/24 loss, prioritizing2024/25 and2025/26 gains. Combined xG variant not selected.')
    atomic_json(P/'proposal.json',spec);print('Operational selection plan prepared',flush=True)

def check_inputs():verify_files(R,c.read(P/'proposal.json')['input_hashes'])

def build():
    check_inputs();verify_files(R,c.read(OLD/'forecast_seal.json')['files']);verify_files(c.D,c.read(c.D/'manifest.json')['files'])
    names=['current.pkl','native_current.pkl','timing.csv.gz','origins.json','history_audit.json','history_rejected.csv','live_feature_coverage.csv']+[f'base_gw{g:02d}.pkl' for g in [1,5,9]]+[f'base_audit_gw{g:02d}.json' for g in [1,5,9]]
    for n in names:shutil.copyfile(OLD/n,P/n)
    shutil.copytree(OLD/'models',P/'models');shutil.copytree(OLD/'raw',P/'raw')
    info=c.read(OLD/'prepared.json');info.update(source_capture_reused=True,source_release=str(OLD.relative_to(R)),recipe_transition_only=True);atomic_json(P/'prepared.json',info)
    c.fit_heads();print('8 live recent180 heads sealed on unchanged source capture',flush=True)

def verify():
    check_inputs();info=c.read(P/'prepared.json');seal=c.read(P/'forecast_seal.json');verify_files(R,seal['files']);verify_files(P,info['files']);issued=c.utc(info['issued_at']);now=pd.Timestamp.now(tz='UTC');assert info['features']==325 and seal['calibration_half_life_days']==180
    out=c.load(P/'live_features.pkl');prior=c.load(OLD/'live_features.pkl');pd.testing.assert_frame_equal(out.drop(columns=[f'xp_{j}' for j in range(8)]),prior.drop(columns=[f'xp_{j}' for j in range(8)]));assert np.isfinite(out[[f'xp_{j}' for j in range(8)]]).all().all()
    for n in ['current.pkl','native_current.pkl','timing.csv.gz']+[f'base_gw{g:02d}.pkl' for g in [1,5,9]]:assert sha(P/n)==sha(OLD/n)
    for n in (OLD/'models').glob('*.pkl'):assert sha(n)==sha(P/'models'/n.name)
    teacher=pd.concat([c.load(c.FIT/'head_data.pkl'),c.load(P/'current_oof.pkl')],ignore_index=True);complete=teacher[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=teacher[[f'y_at_{j}' for j in range(3)]].max(axis=1);heads=c.read(P/'heads.json');grads=[]
    for j in range(8):
        tr=teacher[teacher.teacher_eligible&teacher.forecast_at.lt(issued)&teacher[f'y_{j}'].notna()&teacher[f'y_at_{j}'].lt(issued)&complete&h3.lt(issued)];model=heads[str(j)];assert model['teacher_keys_sha256']==c.common.keys_hash(tr) and len(tr)==model['rows'];assert tr[f'y_at_{j}'].max()<issued and h3.loc[tr.index].max()<issued
        raw,anchor,names=c.projection.design(tr,'component',j);x,transform=c.projection.transform(raw)
        for field in ['median','mean','std']:np.testing.assert_allclose(model['transform'][field],transform[field],atol=1e-10,rtol=1e-10)
        age=(issued-tr.forecast_at).dt.total_seconds().to_numpy()/86400;w=2.**(-age/180);beta=np.array(model['beta']);pen=.01*beta;pen[0]=0;grad=x.T@(w*(x@beta-(tr[f'y_{j}'].to_numpy()-anchor)/6))/w.sum()+pen;assert abs(grad).max()<1e-8;grads.append(float(abs(grad).max()))
        prediction=c.projection.predict_projection(out,'component',model);prediction[out.known_departed|(out.confirmed_out_current if j==0 else False)]=0;np.testing.assert_allclose(prediction,out[f'xp_{j}'],atol=1e-9,rtol=1e-10)
    # Replay every already-scored historical recent180 head numerically, using
    # the new operational fitter, without changing or rerunning season choices.
    data=c.load(RESEARCH/'head_data_recent_only.pkl');audit=pd.read_csv(RESEARCH/'head_audit_recent_only.csv');complete=data[[f'y_{j}' for j in range(3)]].notna().all(axis=1);last=data[[f'y_at_{j}' for j in range(3)]].max(axis=1);errors=[]
    for row in audit.itertuples():
        at=c.utc(row.cutoff);j=row.offset;tr=data[data.teacher_eligible&data.forecast_at.lt(at)&data[f'y_{j}'].notna()&data[f'y_at_{j}'].lt(at)&complete&last.lt(at)];model,_=c.fit_recent(tr,j,at);old=c.read(R/row.file);assert len(tr)==row.rows and model['teacher_keys_sha256']==row.keys_sha256;np.testing.assert_allclose(model['beta'],old['beta'],atol=1e-9,rtol=1e-10);errors.append(float(np.max(np.abs(np.array(model['beta'])-old['beta']))))
    assert len(errors)==240
    runtime=c.ComponentForecaster(P);runtime.forecast(dict(season=c.SEASON,round=9,forecast_at=issued))
    rejected=[]
    for at,g in [(issued+pd.Timedelta(hours=25),9),(issued,10),(pd.Timestamp('2026-10-26'),9)]:
        try:runtime.forecast(dict(season=c.SEASON,round=g,forecast_at=at))
        except ValueError:rejected.append(True)
        else:raise AssertionError('Invalid origin accepted')
    try:runtime.forecast(dict(season=c.SEASON,round=9,forecast_at=now));refresh=False;reason=None
    except ValueError as e:
        reason=str(e);assert 'external club/national feeds' in reason or 'Refresh official data' in reason;refresh=True
    assert out.loc[~out.can_start_0,'xp_0'].eq(0).all() and not out.loc[~out.can_start_0,'can_buy'].any();assert out.loc[out.known_departed,[f'xp_{j}' for j in range(8)]].eq(0).all().all()
    pool=out.copy();pool['market']=pool.price_tenths;hostile=pool[[f'xp_{j}' for j in range(8)]].to_numpy(float);hostile[~pool.can_start_0.to_numpy()]=10000;mod,a=c.hard_manager();state=a.engine.initial_state(start_gw=9);choice=copy.deepcopy(a.decide(pool,hostile,state,9)['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};after,choice=a.engine.apply_decision(state,choice,pool.to_dict('records'),9);assert not set(pool.loc[~pool.can_start_0,'pid'])&set(choice['squad']);assert len(a.ledger)<=40
    blocked=pool[~pool.can_start_0].iloc[0];same=next(i for i in choice['squad'] if pool.set_index('pid').at[i,'pos']==blocked.pos);state=copy.deepcopy(after);state['next_gw']=9;state['owned'][int(blocked.pid)]=state['owned'].pop(int(same));state['ownership_clubs'].pop(int(same),None);state['ownership_clubs'][int(blocked.pid)]=blocked.club;mod,b=c.hard_manager();second=copy.deepcopy(b.decide(pool,hostile,state,9)['choice']);second['prices']={int(k):v for k,v in second['prices'].items()};b.engine.apply_decision(state,second,pool.to_dict('records'),9);assert int(blocked.pid) not in second['starters']+[second['captain'],second['vice']];assert len(b.ledger)<=40
    assert c.REFITS==tuple(range(1,39,4));assert all(not x['reused_between_refits'] for x in c.read(P/'head_audit.json'))
    atomic_json(P/'verification.json',dict(passed=True,verified_at=str(now),live_heads_verified=8,historical_heads_numerically_reproduced=240,max_historical_beta_error=max(errors),max_live_gradient=max(grads),same325_features_base_outputs_sources_targets_and_teacher_rows=True,no_xg=True,half_life_days=180,refits=list(c.REFITS),invalid_origins_rejected=True,hard_eligibility_preflights_passed=2,manager_calls=[len(a.ledger),len(b.ledger)],source_capture_at=str(issued),current_recommendation_refresh_required=refresh,current_refresh_reason=reason,original_three_season_gate_still_failed=True,user_override_explicit=True,files={str(p.relative_to(R)):sha(p) for p in [P/'forecast_seal.json',P/'heads.json',P/'head_audit.json',P/'forecasts.csv',R/'model_lab/recent_component_forecaster.py']}));print('RECENT180 OPERATIONAL CHECKS PASSED; refresh_required=',refresh,flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='build':build()
    elif sys.argv[1]=='verify':verify()
    else:raise ValueError(sys.argv[1])
