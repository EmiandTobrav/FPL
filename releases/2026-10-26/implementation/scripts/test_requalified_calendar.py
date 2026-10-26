"""Current component, only qualified calendar inputs corrected; no promotion."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import pandas as pd,numpy as np
from catboost import CatBoostRegressor
from model_lab.common import atomic_json,sha,verify_files
from scripts import base_recency_study as b
P=R/'reports/calendar_requalification_2026_10_26';D=R/'datasets/fpl_calendar_requalified_v1';O=R/'datasets/fpl_common_training_v5';B=R/'reports/base_cadence_2026_10_26';F=b.F;t=b.t;ID='current-component-qualified-calendar-20261026-v1';ARMS=['calendar'];b.P=P;b.D=D;b.CONFIG={'standard':4,'calendar':4};b.ARMS=ARMS;b.cal.P=P;b.cal.ARMS=ARMS;t.P=P;t.D=D;t.ARMS=ARMS

def teacher(arm):
 d=t.load(F/'head_data.pkl');new=t.load(D/'pool_features.pkl').set_index(t.KEY)
 if arm=='calendar':
  for c in t.read(D/'qualification.json')['changed_columns']:d[c]=new.reindex(pd.MultiIndex.from_frame(d[t.KEY]))[c].to_numpy()
 pred=pd.concat([t.load(P/arm/f'base_{s}.pkl') for s in t.S],ignore_index=True);return d.drop(columns=['component_p1','component_m1','component_p3','component_m3']).merge(pred,on=t.KEY+['forecast_at'],validate='one_to_one')
b.teacher_data=teacher

def setup():
 assert not (P/'proposal.json').exists();parent=t.read(B/'proposal.json');deps=dict(parent['input_hashes']);verify_files(R,deps);deps.pop('overview/ACTIVE_TEAM_BENCHMARK.json',None);deps['overview/ACTIVE_TEAM_BENCHMARK.json']=sha(R/'overview/ACTIVE_TEAM_BENCHMARK.json')
 paths=[Path(__file__),R/'scripts/verify_requalified_calendar.py',R/'scripts/build_requalified_calendar.py',D/'manifest.json',D/'qualification.json',D/'commit_queries_completed.json',D/'download_receipts.json',D/'blob_verification.json',B/'final_verification.json',B/'prediction_verification_standard.json',B/'standard.csv.gz',B/'scores_standard.csv',B/'control_bundle_inventory.csv']+list((B/'standard').glob('base_*.pkl'))+[D/name for name in t.read(D/'manifest.json')['files']]+[R/name for name in t.read(D/'manifest.json')['source_hashes']]
 deps.update({str(p.relative_to(R)):sha(p) for p in paths});old=t.load(O/'training.pkl');new=t.load(D/'training.pkl');cols=b.columns();allowed=sorted(set(cols+t.read(D/'qualification.json')['changed_columns']));pd.testing.assert_frame_equal(old.drop(columns=allowed),new.drop(columns=allowed));changed=(~(old[cols].eq(new[cols])|(old[cols].isna()&new[cols].isna()))).any(axis=1);plans=[]
 for s in t.S:
  for g in t.REFITS:
   for h in [1,3]:
    control=b.control_row(s,g,h);at=pd.Timestamp(control.cutoff);tr=b.select(new,at,h);assert len(tr)==control.rows and t.common.keys_hash(tr)==control.keys_sha256;n=int(changed.loc[tr.index].sum());path=P/f'models/calendar_{s}_gw{g:02d}_h{h}.pkl' if n else b.control_path(control);plans.append(dict(season=s,round=g,horizon=h,cutoff=str(at),rows=len(tr),keys_sha256=control.keys_sha256,changed_training_rows=n,new_fit=n>0,file=str(path.relative_to(R)),original_file=str(b.control_path(control).relative_to(R)),original_sha256=control.sha256))
 plan=pd.DataFrame(plans);assert len(plan)==80;plan.to_csv(P/'fit_plan.csv',index=False);deps[str((P/'fit_plan.csv').relative_to(R))]=sha(P/'fit_plan.csv');n=int(plan.new_fit.sum());shutil.copytree(B/'standard',P/'standard');shutil.copyfile(B/'standard.csv.gz',P/'standard.csv.gz');shutil.copyfile(B/'scores_standard.csv',P/'scores_standard.csv');shutil.copyfile(R/'overview/ACTIVE_TEAM_BENCHMARK.json',P/'reference_ACTIVE_TEAM_BENCHMARK.json')
 spec=dict(parent);spec.update(id=ID,candidate_id='component_qualified_predeadline_calendar_v1',hypothesis='Fresh complete official-API fixture archives may improve2025/26 decisions and exposure. Requalify all114 evaluation deadlines by same strict rule; keep all model, calibration and manager settings fixed.',change='Only archived calendar and dependent home/opponent/context fields change, for30 origins in2025/26. Same325 features, teacher keys/targets, training eligibility, median method, uniform base weights, CatBoost150/depth5/lr.05/L2=5/seed20261025, four-round base and180day/Ridge.01four-round calibration. Refit base only when exact past training features change; reconstruct all4year base streams and own calibration teachers. Full3candidate seasons,3verified control seasons reused. No future schedule backfill, no source-statistics/market/rule/manager changes, no automatic activation.',related_work=['current-player-decision-diagnosis-20261026-v2',parent['id']],input_hashes=deps,model_parameters=dict(base=b.PARAMS,base_refits=list(t.REFITS),base_weights='uniform',calibration_half_life=180,calibration_ridge=.01,calibration_refits=list(t.REFITS),features=325,calendar_only=True),resources=dict(new_unique_base_fits=n,reused_base_fits=80-n,independent_new_fit_replay=1,new_calibration_heads=240,new_manager_seasons=3,new_decisions=114,reused_control_seasons=3,preflight_decisions=2,workers=4,threads=1),success_criterion='Report each season net-after-hits, latest2/all3means, forecast accuracy and fixture-exposure correction. Same qualified calendar rule for all seasons; no point-driven source selection or new search. No automatic promotion.',stop_rule='Complete fixed3episodes; stop on source/clock/matrix/teacher/target/legality mismatch; no parameter changes or score-driven reruns.',maximum_runs=1)
 atomic_json(P/'proposal.json',spec);atomic_json(P/'dataset_verification.json',dict(passed=True,source_qualified=True,only_calendar_context_changed=True,features325=True,all_targets_and_teacher_eligibility_unchanged=True));print('CALENDAR TEST PREPARED',n,'new fits',80-n,'reused',flush=True)

def fit(s,g,h):
 t.check();row=pd.read_csv(P/'fit_plan.csv').query('season==@s and round==@g and horizon==@h').iloc[0];assert row.new_fit;d=t.load(D/'training.pkl');tr=b.select(d,pd.Timestamp(row.cutoff),h);x,imp=b.matrix(tr,b.columns());model=CatBoostRegressor(**b.PARAMS);model.fit(x,b.labels(tr,h));t.save(R/row.file,dict(name='component',columns=b.columns(),imputer=imp,models=[model],horizon=h,fit_cutoff=row.cutoff,uniform_base_training=True,trained_from_scratch=True));print('FITTED',s,g,h,flush=True)

def assemble(s):
 t.check();view=t.load(D/'pool_features.pkl');plan=pd.read_csv(P/'fit_plan.csv');plan=plan[plan.season.eq(s)];out=view[view.season.eq(s)][t.KEY+['forecast_at']].copy();rows=[]
 for row in plan.itertuples():
  q=view[view.season.eq(s)&view['round'].between(row.round,min(38,row.round+3))];bundle=t.load(R/row.file);assert bundle['models'][0].get_params()==b.PARAMS;v=b.predict(bundle,q,row.horizon)
  for c in v:out.loc[q.index,c]=v[c]
  rows.append(dict(**row._asdict(),sha256=sha(R/row.file)))
 folder=P/'calendar';folder.mkdir(exist_ok=True);t.save(folder/f'base_{s}.pkl',out);pd.DataFrame(rows).drop(columns='Index').to_csv(folder/f'base_audit_{s}.csv',index=False);print('BASE STREAM',s,flush=True)

def finish():
 t.check()
 for name in ['base_verification_calendar','prediction_verification_calendar','preflight_calendar','manager_verification_calendar','outcome_verification']:assert t.read(P/f'{name}.json')['passed']
 a=pd.read_csv(P/'scores_calendar.csv');c=pd.read_csv(P/'scores_standard.csv');scores=pd.concat([c,a]);assert len(scores)==6 and scores.complete.all();scores.to_csv(P/'scores.csv',index=False);w=scores.pivot(index='season',columns='arm',values='net');w['delta']=w.calendar-w.standard;w.to_csv(P/'comparison.csv');files=list(P.glob('*.csv'))+list((P/'models').glob('*.pkl'))+list((P/'calendar').glob('*.csv'))+[P/f'{name}.json' for name in ['base_verification_calendar','prediction_verification_calendar','preflight_calendar','manager_verification_calendar','outcome_verification']];atomic_json(P/'final_verification.json',dict(passed=True,all3seasons_complete=True,new_models=int(pd.read_csv(P/'fit_plan.csv').new_fit.sum()),new_calibration_heads=240,new_decisions_replayed=114,only_calendar_context_and_its_learned_consequences_changed=True,active_model_unchanged=True,files={str(p.relative_to(R)):sha(p) for p in files}));print(w.to_string(),flush=True)
if __name__=='__main__':
 a=sys.argv[1]
 if a=='setup':setup()
 elif a=='fit':fit(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]))
 elif a=='assemble':assemble(sys.argv[2])
 elif a=='heads':b.heads('calendar')
 elif a=='preflight':b.cal.preflight('calendar')
 elif a=='manager':t.manager(sys.argv[2],'calendar')
 elif a=='replay':b.cal.replay('calendar')
 elif a=='finish':finish()
 else:raise ValueError(a)
