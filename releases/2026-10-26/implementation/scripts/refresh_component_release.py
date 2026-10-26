"""Capture, update, check and publish a new immutable operational release.

Run before a recommendation when official receipts are older than24h. This
command never submits FPL team changes. A failed gate leaves the active release.
"""
import argparse,datetime,importlib,json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--directory',required=True);args=parser.parse_args();release=Path(args.directory).resolve()
    if not release.is_relative_to(R/'reports'):raise ValueError('Use a new release directory inside reports')
    release.mkdir(exist_ok=False);os.environ['FPL_COMPONENT_RELEASE']=str(release)
    from scripts import component_live_fetch as capture
    from model_lab.common import sha,verify_files,atomic_json
    import numpy as np
    import pandas as pd
    descriptor=json.loads((R/'overview/ACTIVE_TEAM_BENCHMARK.json').read_text())
    allowed={'common_component_h8_adaptive_v1':'model_lab/component_forecaster.py','common_component_h8_recent180_adaptive_v1':'model_lab/recent_component_forecaster.py', 'common_component_h8_recent180_plan5_calendar_v1':'model_lab/fresh_planned_component_forecaster.py'}
    assert allowed.get(descriptor['id'])==descriptor['runtime']
    assert sha(R/descriptor['runtime'])==descriptor['runtime_sha256']
    c=importlib.import_module(descriptor['runtime'][:-3].replace('/','.'))
    verify_files(c.D,c.read(c.D/'manifest.json')['files'])
    # A fresh FPL response cannot disguise an old external observation feed.
    # Dataset collection is versioned separately; stop until its new release is
    # integrated rather than treating weeks of missing cups/NT games as zero.
    context=getattr(c,'EXTERNAL',R/'datasets/fpl_all_competitions_context_v1');context_manifest=c.read(context/'manifest.json');now=pd.Timestamp.now(tz='UTC')
    if now-pd.Timestamp(context_manifest['created_at'])>pd.Timedelta(hours=24):raise ValueError('Refresh and integrate the external club/national observation dataset before publishing another live release')
    verify_files(context,context_manifest['files']);capture.P=release/'raw';capture.main();c.prepare();info=c.read(release/'prepared.json');g=info['round'];previous=R/info['previous_release']
    # Consecutive availability transition flags use the prior sealed snapshot,
    # never a later retrospectively reconstructed report.
    previous_info=c.read(previous/'prepared.json')
    if previous_info['round']==g-1:
        boot=c.read(previous/'raw/bootstrap.json');source=pd.Timestamp(c.read(previous/'raw/receipts.json')[0]['retrieved_at']);prior={e['code']:e for e in boot['elements']};d=c.load(release/'current.pkl');mask=d['round'].eq(g)
        for index,row in d[mask].iterrows():
            p=prior.get(row.code);known=p is not None and (not p.get('news_added') or pd.Timestamp(p['news_added'])<=source)
            d.at[index,'av_previous_snapshot_consecutive']=float(known)
            d.at[index,'av_reported_return_to_available']=float(known and p['status'] in ['i','s','n'] and row.status=='a') if pd.notna(row.av_status_a) else np.nan
        c.save(release/'current.pkl',d);info['files']['current.pkl']=sha(release/'current.pkl');(release/'prepared.json').write_text(json.dumps(info,indent=2)+'\n')
    if g in c.REFITS:c.fit_base(g)
    else:
        if previous_info['refit_round']!=info['refit_round']:raise ValueError('Missing required four-round refit; do not silently reuse old models')
        c.reuse_base(g)
    c.fit_heads();seal=c.read(release/'forecast_seal.json');verify_files(R,seal['files']);
    if hasattr(c,'configuration'):verify_files(R,c.read(release/'operational_seal.json')['files'])
    pool=c.load(release/'live_features.pkl');assert np.isfinite(pool[[f'xp_{j}' for j in range(8)]].to_numpy(float)).all();assert len(pool)==len(c.read(release/'raw/bootstrap.json')['elements'])
    times=pd.read_csv(release/'timing.csv.gz');origin=pd.to_datetime(times.forecast_at,utc=True,format='mixed')
    for name in ['latest_history','latest_workload','latest_international','source_time','calendar_time']:
        stamp=pd.to_datetime(times[name],utc=True,format='mixed',errors='coerce');assert (stamp.isna()|stamp.lt(origin)).all()
    assert pool.loc[~pool.can_start_0,'xp_0'].eq(0).all() and not pool.loc[~pool.can_start_0,'can_buy'].any()
    # Full manager legality is exercised on the fresh roster with hostile scores
    # for unavailable players, under the unchanged solver budget.
    mod,manager=c.hard_manager();pool['market']=pool.price_tenths;xp=pool[[f'xp_{j}' for j in range(8)]].to_numpy(float);xp[~pool.can_start_0.to_numpy()]=10000
    state=manager.engine.initial_state(start_gw=g);choice=manager.decide(pool,xp,state,g)['choice'];choice['prices']={int(k):v for k,v in choice['prices'].items()};manager.engine.apply_decision(state,choice,pool.to_dict('records'),g)
    atomic_json(release/'verification.json',dict(passed=True,checked_at=str(pd.Timestamp.now(tz='UTC')),same_refit_cadence=True,refit_round=info['refit_round'],models_retrained=g in c.REFITS,hard_eligibility_passed=True,solver_calls=len(manager.ledger),automatic_team_changes=False))
    # Keep the exact replaced descriptor in this release. Publish only after all
    # checks; the registry is the origin archive for subsequent calibration.
    (release/'previous_active_descriptor.json').write_bytes((R/'overview/ACTIVE_TEAM_BENCHMARK.json').read_bytes());descriptor.update(status='active_for_team_followup',release=str(release.relative_to(R)),live_round=g,forecast_seal=str((release/'forecast_seal.json').relative_to(R)),last_refresh=str(pd.Timestamp.now(tz='UTC')),forecast_at=info['issued_at'],next_deadline=info['deadline'],current_training_extension=str((release/'current.pkl').relative_to(R)),current_refit_round=info['refit_round'])
    descriptor.update(current_data_refresh_required=False,current_refresh_reason=None,source_capture_reused=False,prospective_evidence='Fresh official and external observations; no post-deadline inference; no new performance claim')
    if (release/'operational_seal.json').exists():descriptor['operational_seal']=str((release/'operational_seal.json').relative_to(R))
    registry=c.read(R/'overview/COMPONENT_RELEASES.json');registry['releases'].append(dict(directory=str(release.relative_to(R)),seal_sha256=sha(release/'forecast_seal.json'),round=g,issued_at=info['issued_at']))
    for path,value in [(R/'overview/COMPONENT_RELEASES.json',registry),(R/'overview/ACTIVE_TEAM_BENCHMARK.json',descriptor)]:
        temp=path.with_suffix('.refresh.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');os.replace(temp,path)
    print('Refreshed active component release',release,'round',g,flush=True)
if __name__=='__main__':main()
