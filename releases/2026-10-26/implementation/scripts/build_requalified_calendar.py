"""Qualify immutable predeadline FPL calendars; patch calendar context only."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS']:os.environ[k]='1'
import sys,json,pickle,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import pandas as pd,numpy as np
from scripts import matched_season_retest_v5 as m
from model_lab.common import sha,atomic_json
D=R/'datasets/fpl_calendar_requalified_v1';OLD=R/'datasets/fpl_common_training_v5';F=R/'reports/matched_season_retest_2026_10_26_v8';read=lambda p:json.loads(Path(p).read_text())
def save(name,obj):
 with (D/name).open('xb') as f:pickle.dump(obj,f,protocol=5)
def run():
 origins=pd.read_pickle(F/'origins.pkl');calendars=pd.read_pickle(F/'calendars.pkl');metadata=pd.read_pickle(F/'metadata.pkl');schema=read(OLD/'schema.json');old_schema=read(R/'datasets/fpl_common_training_v3/schema.json');cols=old_schema['features'];oldcal=pd.read_csv(F/'calendar.csv');records=read(D/'commit_queries_completed.json');receipts=read(D/'download_receipts.json');versions={};qualification=[]
 maps={s:pd.read_csv(R/f'FPL_training_dataset/research/current/project/data/{s}_teams.csv.gz').set_index('id').code.to_dict() for s in m.SEASONS}
 for row in receipts:
  path=R/row['file'];raw=path.read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['blob_sha'];j=json.loads(raw);df=pd.DataFrame(j);s='2025-26';assert len(df)==380 and df.id.nunique()==380 and not df[['team_h','team_a']].duplicated().any();old=next(v['frame'] for (ss,g),v in calendars.items() if ss==s).set_index('id');a=df.set_index('id').reindex(old.index);assert a.team_h.equals(old.team_h) and a.team_a.equals(old.team_a);assert df.event.dropna().between(1,38).all();assert set(df.team_h)|set(df.team_a)==set(maps[s]);at=max(pd.Timestamp(row['author_time']),pd.Timestamp(row['committer_time']));frame=df[['id','event','team_h','team_a','kickoff_time']].copy();frame['home']=frame.team_h.map(maps[s]);frame['away']=frame.team_a.map(maps[s]);versions[(s,row['commit'])]=dict(frame=frame,source_time=at,source_sha=row['commit'],file=row['file'],repo=row['repo'],blob_sha=row['blob_sha']);qualification.append(dict(**row,sha256=sha(path),qualified=True,season=s,fixture_count=380,fixture_identity_matches_existing_preseason_universe=True,performance_fields_excluded=True))
 observed=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=['season','fixture','fixture_event','fixture_kickoff_time','kickoff_time']).drop_duplicates(['season','fixture']);observed['observed_available']=pd.to_datetime(observed.fixture_kickoff_time.fillna(observed.kickoff_time),utc=True)+pd.Timedelta(hours=24);selected={};selection=[];changed_origins=[];past_reconciliations=[]
 for (s,g),at in sorted(origins.items()):
  old=calendars[(s,g)];assert old['source_time']<at;candidates=[v for (ss,key),v in versions.items() if ss==s and v['source_time']<at and v['source_time']>old['source_time']];new=max(candidates,key=lambda v:v['source_time']) if candidates else None
  if new is None:selected[(s,g)]=old;selection.append(dict(season=s,round=g,forecast_at=str(at),source_time=str(old['source_time']),source_sha=old['source_sha'],file=old['file'],age_days=old['age'],changed_source=False,repo='vaastav/Fantasy-Premier-League'));continue
  f=new['frame'].copy();past=observed[observed.season.eq(s)&observed.observed_available.lt(at)].set_index('fixture')
  for ix,v in f.iterrows():
   if v.id not in past.index:continue
   r=past.loc[v.id];ko=r.fixture_kickoff_time if pd.notna(r.fixture_kickoff_time) else r.kickoff_time
   if pd.isna(v.event) or v.event!=r.fixture_event or pd.to_datetime(v.kickoff_time,utc=True,errors='coerce')!=pd.Timestamp(ko):past_reconciliations.append(dict(season=s,round=g,fixture=int(v.id),available=str(r.observed_available),forecast_at=str(at)))
   f.at[ix,'event']=r.fixture_event;f.at[ix,'kickoff_time']=ko
  v=dict(new,frame=f,age=(at-new['source_time']).total_seconds()/86400);selected[(s,g)]=v;changed_origins.append((s,g));selection.append(dict(season=s,round=g,forecast_at=str(at),source_time=str(v['source_time']),source_sha=v['source_sha'],file=v['file'],age_days=v['age'],changed_source=True,repo=v['repo']))
 # Same predeadline strength states as the original context generator.
 role=m.inputs.isolated_module('_calendar_requalified_strength',R/'datasets/fpl_role_strength_v1/build.py',('common',));games=pd.read_csv(R/'datasets/fpl_role_strength_v1/fixture_strength_audit.csv');strength={}
 for s in sorted(maps):
  st=role.Strength();events={};pre={}
  for v in games[games.season.eq(s)].to_dict('records'):
   v['home']=str(int(v['home']));v['away']=str(int(v['away']))
   for typ,col in [('kick','kickoff'),('release','available')]:events.setdefault(pd.Timestamp(v[col]),{'kick':[],'release':[],'query':[]})[typ].append(v)
  for key,at in origins.items():
   if key[0]==s:events.setdefault(at,{'kick':[],'release':[],'query':[]})['query'].append(key)
  for at,e in sorted(events.items()):
   for key in e['query']:strength[key]={int(c):st.state(str(int(c))) for c in maps[s].values()}
   for v in e['kick']:pre[v['fixture']]=st.pre(v)
   for v in e['release']:st.add(v,pre[v['fixture']])
 # Exact original context rule; own strength and unrelated cup/history fields stay fixed.
 def context(s,g,club,source):
  at=origins[(s,g)];states=strength[(s,g)];f=source['frame'];ownfs=f[(f.home.eq(club)|f.away.eq(club))];bound=len(ownfs)==38 and ownfs.event.notna().all();x={'cal_PL_round_bindings_complete':float(bound)}
  for h in [1,3,6]:
   fs=ownfs[ownfs.event.between(g,min(38,g+h-1))];n=[int(ownfs.event.eq(r).sum()) for r in range(g,min(39,g+h))] if bound else [];x[f'cal_PL_fixtures_next_{h}_rounds']=len(fs) if len(ownfs) else np.nan;x[f'cal_PL_blank_rounds_next_{h}']=sum(v==0 for v in n) if bound else np.nan;x[f'cal_PL_double_rounds_next_{h}']=sum(v>1 for v in n) if bound else np.nan
   if h in [1,3]:
    ops=[states[int(v.away if v.home==club else v.home)] for v in fs.itertuples()];x[f'ds_known_matches_h{h}']=len(fs) if len(ownfs) else np.nan
    for k in ['attack_index','concession_index']:x[f'ds_opponent_{k}_h{h}']=np.mean([v[k] for v in ops]) if ops else np.nan
  times=pd.to_datetime(ownfs.kickoff_time,utc=True,errors='coerce');times=times[times.ge(at)];x['cal_hours_until_next_known_club_fixture']=(times.min()-at).total_seconds()/3600 if len(times) else np.nan
  for days in [7,14,28]:x[f'cal_PL_registered_fixtures_next_{days}d']=int(times.lt(at+pd.Timedelta(days=days)).sum()) if len(ownfs) else np.nan
  for j in range(8):
   fs=ownfs[ownfs.event.eq(g+j)];ops=[states[int(v.away if v.home==club else v.home)] for v in fs.itertuples()];x[f'u_count_{j}']=len(fs) if len(fs) or bound else np.nan;x[f'u_home_{j}']=float(fs.home.eq(club).mean()) if len(fs) else np.nan
   for kind in ['attack','concession']:x[f'u_opp_{kind}_{j}']=np.mean([v[kind+'_index'] for v in ops]) if ops else np.nan
  counts=[x[f'u_count_{j}'] for j in range(min(3,39-g))];x['u_count3']=sum(counts) if all(np.isfinite(v) for v in counts) else np.nan;return x
 contexts={};oldcontexts={};meta={k:v.set_index('code') for k,v in metadata.items()};stats=[];changed_columns=set()
 for name in ['training.pkl','pool_features.pkl']:
  d=pd.read_pickle(OLD/name);out=d.copy();updates=0
  for s,g in changed_origins:
   mask=d.season.eq(s)&d['round'].eq(g);q=d[mask]
   if not len(q):continue
   if name=='training.pkl':clubs=q.code.map(meta[(s,g)].club)
   else:
    pp=m.pool(s,g).set_index('code');teams=pd.read_csv(R/f'FPL_training_dataset/research/current/project/data/{s}_teams.csv.gz');nm=dict(zip(teams.name,teams.code));nm['Ipswich Town']=nm.get('Ipswich');clubs=q.code.map(pp.club).map(nm)
   for ix,c in clubs.items():
    if pd.isna(c):continue
    k=(s,g,int(c))
    if k not in contexts:contexts[k]=context(s,g,int(c),selected[(s,g)]);oldcontexts[k]=context(s,g,int(c),calendars[(s,g)])
    for col,val in contexts[k].items():
     before=d.at[ix,col];expected=oldcontexts[k][col];assert (pd.isna(before) and pd.isna(expected)) or np.isclose(before,expected,rtol=1e-5,atol=1e-5),(name,k,col,before,expected)
     if not ((pd.isna(before) and pd.isna(val)) or (pd.notna(before) and pd.notna(val) and np.isclose(before,val,rtol=0,atol=1e-10))):out.at[ix,col]=val;updates+=1;changed_columns.add(col)
  pd.testing.assert_frame_equal(d.drop(columns=sorted(changed_columns)),out.drop(columns=sorted(changed_columns)));save(name,out);stats.append(dict(file=name,rows=len(d),changed_cells=updates));print('CALENDAR PATCHED',name,len(d),updates,flush=True)
 pd.DataFrame(selection).to_csv(D/'calendar.csv',index=False);pd.DataFrame(past_reconciliations).to_csv(D/'past_reconciliations.csv',index=False);save('calendars.pkl',selected);save('origins.pkl',origins);save('contexts.pkl',contexts);atomic_json(D/'qualification.json',dict(passed=True,snapshots=qualification,new_origin_sources=len(changed_origins),selection='Latest complete qualified source strictly before official origin; authors AND committers before origin; no outcome-based selection.',original_predeadline_calendar_and_past24h_rule_retained=True,changed_columns=sorted(changed_columns),patches=stats));atomic_json(D/'schema.json',schema)
 paths=[D/'training.pkl',D/'pool_features.pkl',D/'calendar.csv',D/'calendars.pkl',D/'origins.pkl',D/'contexts.pkl',D/'qualification.json',D/'schema.json',D/'commit_queries_completed.json',D/'download_receipts.json',D/'blob_verification.json'];atomic_json(D/'manifest.json',dict(files={p.name:sha(p) for p in paths},source_hashes={x['file']:sha(R/x['file']) for x in receipts},code_sha256=sha(Path(__file__)),active_dataset_pointer_unchanged=True));print('CALENDAR DATASET QUALIFIED',len(changed_origins),flush=True)
if __name__=='__main__':run()
