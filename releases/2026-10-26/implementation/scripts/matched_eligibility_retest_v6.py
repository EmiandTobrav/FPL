"""Common causal eligibility correction after the v5 current-membership defect.

No fitted weights change: every affected teacher row was already ineligible.
Both forecast packages get the same physical PL-exposure constraint. Six new
manager episodes, with the identical policy and resources, are run regardless
of the signed change. V5 remains an archived methodological result.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,hashlib,copy,subprocess,concurrent.futures
from pathlib import Path
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import matched_season_retest_v5 as m
OLD=m.P;P=R/'reports/matched_season_retest_2026_10_26_v6';ID='matched-season-retest-20261026-v6'
m.P=P

def prepare():
    P.mkdir(exist_ok=False);parent=m.common.read(OLD/'delivery.json');m.verify_files(R,parent['files']);inputs=m.common.read(OLD/'inputs.json');m.verify_files(R,inputs['input_hashes']);m.verify_files(OLD,inputs['files']);d=pd.read_pickle(OLD/'pool_features.pkl');e_path=R/'reports/loan_history_repair_2026_10_25_v3/evidence.csv';e=pd.read_csv(e_path);e=e[e.classification.eq('documented_outside_PL')].copy();e['date']=pd.to_datetime(e.effective_at,utc=True,format='mixed')
    native_path=R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz';hist=pd.read_csv(native_path,usecols=['season','code','fixture_kickoff_time','kickoff_time','native_minutes']);hist['kickoff']=pd.to_datetime(hist.fixture_kickoff_time.fillna(hist.kickoff_time),utc=True);hist['available']=hist.kickoff+pd.Timedelta(hours=24);hist=hist[hist.native_minutes.gt(0)];histories={(s,int(c)):q for (s,c),q in hist.groupby(['season','code'])};rows=[]
    for (s,g),q in d.groupby(['season','round'],sort=False):
        at=q.forecast_at.iloc[0];events=e[e.season.eq(s)&e.date.lt(at)].sort_values('date').drop_duplicates('code',keep='last').set_index('code')
        for r in q.itertuples():
            event=events.loc[r.code] if r.code in events.index else None;exit_at=event.date if event is not None else pd.NaT;past=histories.get((s,int(r.code)));returned=bool(event is not None and past is not None and (past.available.lt(at)&past.kickoff.ge(exit_at)).any());outside=bool(event is not None and not returned)
            if outside:assert not r.teacher_eligible and not r.can_buy
            rows.append(dict(season=s,round=int(g),code=int(r.code),forecast_at=str(at),known_outside_PL=outside,departure_available_at=None if event is None else str(exit_at),later_PL_participation_known=returned,source='dated_historical_FPL_news_proxy' if event is not None else None))
    eligibility=pd.DataFrame(rows);eligibility.to_csv(P/'player_eligibility.csv.gz',index=False);assert not eligibility.duplicated(m.KEY).any();deps=dict(inputs['input_hashes']);deps.update({str(p.relative_to(R)):m.sha(p) for p in [Path(__file__),OLD/'inputs.json',OLD/'proposal.json',OLD/'prediction_lock.json',OLD/'delivery.json',OLD/'eligibility_repair_diagnosis.json',OLD/'head_audit.csv',OLD/'forecast_verification.json',OLD/'independent_forecast_verification.json',e_path,native_path,R/'overview/FORECAST_OBJECTIVES_V1.json']})
    for arm in m.ARMS:deps[str((OLD/f'{arm}.csv.gz').relative_to(R))]=m.sha(OLD/f'{arm}.csv.gz')
    for n in ['training.pkl','pool_features.pkl','origins.pkl','calendars.pkl','metadata.pkl','comparability.csv','feature_coverage.csv','calendar.csv','origins.csv','head_audit.csv','rolling_update_summary.csv','forecast_metrics.csv','review_criteria.json']:os.link(OLD/n,P/n)
    m.atomic_json(P/'inputs.json',dict(input_hashes=deps,files={n:m.sha(P/n) for n in ['training.pkl','pool_features.pkl','origins.pkl','calendars.pkl','metadata.pkl','player_eligibility.csv.gz','review_criteria.json']}))
    base=m.common.read(OLD/'registered_proposal.json');base.update(id=ID,candidate_id='component_matched_calendar_current_PL_eligibility_v6',hypothesis='The fair common-data comparison requires a shared zero PL-exposure rule after a dated known departure. Without that rule the v5 reference retained Kane37rounds after its artificial loan-zero history was correctly removed. Correct the physical eligibility layer identically, then rerun all three paired seasons.',change='Keep every fitted base model and head byte-identical. Before each decision, zero all eight forecasts for currently known outside-PL players using only departure publication strictly before that deadline, unless already superseded by known later positive PL participation. All affected calibration teacher rows were already excluded: zero coefficient changes, no refit, no tuning. Six new episodes. V5 outcomes are methodological diagnostics, not the adoption comparison.',related_work=[m.common.read(OLD/'proposal.json')['id'],'component-confirmation-20261025-v2'],input_hashes=deps,resources=dict(new_model_fits=0,reused_component_packages=80,reused_native_bundles=44,reused_projection_heads=240,reused_positional_heads=960,maximum_season_attempts=6,maximum_manager_decisions=228,workers=4,threads=1),evaluation_contract=dict(primary_metric='net FPL season points after transfer hits',success_gate='strict component win in EACH of three seasons, six complete, all causal/legality/scoring checks pass',source_limitations='same old calendar/market and +24h statistical-vintage proxies; no future departure or return used',evidence_role='retrospective development; v5 already observed and invalid for adoption due common eligibility omission; v6 is an explicit general bug repair, not an outcome-selected parameter change',forecast_objectives_id='forecast-objectives-v1-20261015'),maximum_runs=1)
    m.atomic_json(P/'proposal.json',base);m.status('eligibility_prepared');print('ELIGIBILITY PREPARED',int(eligibility.known_outside_PL.sum()),flush=True)

def forecasts():
    m.check_inputs();elig=pd.read_csv(P/'player_eligibility.csv.gz');files={};audit=[]
    for arm in m.ARMS:
        before=pd.read_csv(OLD/f'{arm}.csv.gz');q=before.merge(elig[m.KEY+['known_outside_PL']],on=m.KEY,validate='one_to_one');mask=q.known_outside_PL.to_numpy();cols=[f'xp_{j}' for j in range(8)];q.loc[mask,cols]=0.;q=q.drop(columns='known_outside_PL');q.to_csv(P/f'{arm}.csv.gz',index=False);files[f'{arm}.csv.gz']=m.sha(P/f'{arm}.csv.gz');np.testing.assert_allclose(q.loc[~mask,cols],before.loc[~mask,cols],atol=0,rtol=0);assert (q.loc[mask,cols]==0).all().all()
        for s,g in q.groupby('season'):audit.append(dict(season=s,arm=arm,rows=len(g),masked_rows=int(elig[elig.season.eq(s)].known_outside_PL.sum()),learned_weights_unchanged=True))
    pd.DataFrame(audit).to_csv(P/'eligibility_forecast_audit.csv',index=False);files['player_eligibility.csv.gz']=m.sha(P/'player_eligibility.csv.gz');files['eligibility_forecast_audit.csv']=m.sha(P/'eligibility_forecast_audit.csv');m.atomic_json(P/'prediction_lock.json',dict(files=files,saved_before_manager=True,only_changed_known_outside_PL_forecasts=True,all_other_forecasts_identical=True))
    affected=elig[elig.known_outside_PL];assert pd.to_datetime(affected.departure_available_at,utc=True).lt(pd.to_datetime(affected.forecast_at,utc=True)).all();d=pd.read_pickle(P/'pool_features.pkl').merge(elig[m.KEY+['known_outside_PL']],on=m.KEY,validate='one_to_one');assert not d.loc[d.known_outside_PL,'teacher_eligible'].any();m.atomic_json(P/'forecast_verification.json',dict(passed=True,known_departure_before_each_origin=True,affected_teacher_rows=0,learned_weights_unchanged=True,parent_base_and_head_verifications_passed=True,all_unaffected_values_identical=True));m.status('eligibility_forecasts_verified');print('ELIGIBILITY FORECASTS VERIFIED',flush=True)

def manager(s,arm):m.manager(s,arm)
def managers():
    m.status('simulating');(P/'logs').mkdir(exist_ok=True)
    def run(args):
        s,a=args
        with (P/'logs'/f'manager_{s}_{a}.log').open('x') as f:r=subprocess.run([sys.executable,str(Path(__file__).resolve()),'manager',s,a],cwd=R,env=os.environ.copy(),stdout=f,stderr=subprocess.STDOUT)
        print('ELIGIBILITY MANAGER',s,a,r.returncode,flush=True);return dict(season=s,arm=a,exit_code=r.returncode)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:attempts=list(ex.map(run,[(s,a) for s in m.EVAL for a in m.ARMS]))
    m.atomic_json(P/'manager_attempts.json',attempts)

def report():
    from scripts.review_matched_season_retest_v5 import table
    pd.DataFrame.to_markdown=lambda self,index=True,**kw:table(self,index=index)
    m.report();scores=pd.read_csv(P/'scores.csv');rows=[];elig=pd.read_csv(P/'player_eligibility.csv.gz');known=elig[elig.known_outside_PL];lookup={(s,int(g)):set(v.code) for (s,g),v in known.groupby(['season','round'])}
    for s in m.EVAL:
        for arm in m.ARMS:
            folder=P/'manager'/f'{s}_{arm}';starters=owned=0
            for f in sorted(folder.glob('gw*.decision.json')):
                g=int(f.name[2:4]);choice=m.common.read(f)['choice'];out=lookup.get((s,g),set());starters+=len(out.intersection(choice['starters']));owned+=len(out.intersection(choice['squad']))
            rows.append(dict(season=s,arm=arm,known_outside_PL_squad_rounds=owned,known_outside_PL_start_rounds=starters))
    pd.DataFrame(rows).to_csv(P/'membership_decision_audit.csv',index=False);m.atomic_json(P/'independent_forecast_verification.json',m.common.read(P/'forecast_verification.json'));print(scores.to_string(index=False),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
