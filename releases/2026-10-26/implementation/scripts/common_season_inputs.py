"""Outcome-blind full-pool views of the frozen common training release.

Existing common rows are reused exactly. Missing pool rows and the known early
2024/25 GW15 origin are reconstructed from strictly earlier observations.
No future observed player features are rolled into an origin.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,importlib.util,collections
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json,verify_files
from scripts import common_model_retest as common
P=R/'reports/common_season_comparison_2026_10_25'
D=common.D;CACHE=R/'reports/fpl_improvement_2026_10_14/cache';CTX=R/'datasets/fpl_all_competitions_context_v1'
EARLY=pd.Timestamp('2024-12-07T11:00:00Z')
SEASONS=['2022-23','2023-24','2024-25'];EVAL=['2023-24','2024-25'];KEY=common.KEY

def isolated_module(name,path,aliases=()):
    saved={k:sys.modules.pop(k,None) for k in aliases};sys.path.insert(0,str(path.parent))
    try:return common.module(name,path)
    finally:
        sys.path.pop(0)
        for k,v in saved.items():
            sys.modules.pop(k,None)
            if v is not None:sys.modules[k]=v

def build():
    P.mkdir(exist_ok=True);assert not (P/'pool_features.pkl').exists()
    d=pd.read_pickle(D/'training.pkl');schema=common.read(D/'schema.json');verify_files(D,common.read(D/'manifest.json')['files']);cols=schema['features'];groups=schema['feature_groups']
    m=pd.read_csv(common.MASTER,low_memory=False);m['available']=pd.to_datetime(m.observation_available_after_proxy,utc=True);m['kickoff']=pd.to_datetime(m.fixture_kickoff_time,utc=True)
    role=isolated_module('_utility_role_source',R/'datasets/fpl_role_strength_v1/build.py',('common',))
    workload=isolated_module('_utility_workload_source',CTX/'build_context.py',('common','workload_store','build_calendar'))
    seasons,_,_,pl,plfs,cup,cupfs,rosters,nationals=workload.inputs();stores={};intl={}
    for s in SEASONS:
        z=seasons[s];inside=lambda a:[e for e in a if z['history_start']<=e['kickoff']<z['end']]
        stores[s]=workload.Store(inside(pl),inside(cup),inside(plfs),inside(cupfs),rosters,{});stores[s].season_start=z['start'];intl[s]=collections.defaultdict(list)
        for row in nationals[s]:intl[s][row['code']].append(row)
    native={int(c):q.sort_values(['available','fixture']) for c,q in m[m.history_eligible].groupby('code',sort=False)}
    audit=pd.read_csv(R/'datasets/fpl_role_strength_v1/player_history_audit.csv.gz',low_memory=False)
    rh={(s,int(c)):q.sort_values(['fixture_kickoff_time','fixture']).to_dict('records') for (s,c),q in audit[audit.history_eligible].groupby(['season','code'],sort=False)}
    snapshots=list(workload.read(CTX/'fixture_snapshots.csv.gz'));snapgroups=collections.defaultdict(list)
    for row in snapshots:snapgroups[(row['season'],int(float(row['round'])))].append(row)
    announcements=list(workload.read(CTX/'historical_announced_club_fixtures.csv'))
    games=pd.read_csv(R/'datasets/fpl_role_strength_v1/fixture_strength_audit.csv',dtype={'home':str,'away':str});games.home=games.home.map(lambda x:str(int(float(x))));games.away=games.away.map(lambda x:str(int(float(x))))
    names=m[['historical_team','club_code']].drop_duplicates();assert not names.historical_team.duplicated().any();namecodes=dict(zip(names.historical_team,names.club_code.map(lambda x:str(int(x)))))
    source=d.set_index(KEY);teacher_labels=d[KEY+['target_points_1','target_history_eligible','label_at_1']].copy();profiles=[];forecasts=[];timing=[];deps={};cases=[]
    evidence=pd.read_csv(R/'reports/loan_history_repair_2026_10_25_v3/evidence.csv');evidence=evidence[evidence.classification.eq('documented_outside_PL')].copy();evidence['effective']=pd.to_datetime(evidence.effective_at,utc=True,format='mixed')
    stats={'minutes':'native_minutes','points':'target_total_points','goals':'native_goals_scored','assists':'native_assists','clean':'native_clean_sheets','starts':'native_starts','saves':'saves'}
    weather={'temperature':'weather_temperature_2m_mean','wind':'weather_wind_speed_10m_mean','rain':'weather_precipitation_sum','sun':'weather_sunshine_minutes_daylight_capped'}
    def history(code,s,at):
        allrows=native.get(int(code),m.iloc[:0]);q=allrows[allrows.available.lt(at)];cur=q[q.season.eq(s)];old=q[q.season.lt(s)]
        if len(old):old=old[old.season.eq(old.season.max())]
        x={'h_cur_count':len(cur),'h_old_count':len(old)}
        for label,a in [('cur',cur),('old',old)]:
            for w in [3,10]:
                for name,c in stats.items():x[f'h_{label}_{w}_{name}']=a[c].tail(w).mean()
        for name in stats:
            nc=min(len(cur),10);no=min(len(old),10);den=nc+no;a=x[f'h_cur_10_{name}'];b=x[f'h_old_10_{name}'];x['h_fixed_'+name]=((nc*a if nc else 0)+(no*b if no else 0))/den if den else np.nan
        x['h_last_price']=q.value.iloc[-1] if len(q) else np.nan;pos=q.position.iloc[-1] if len(q) else None
        for p in ['GK','DEF','MID','FWD']:x['h_pos_'+p]=float(pos==p) if pos else np.nan
        x['h_days_since']=(at-q.kickoff.iloc[-1]).total_seconds()/86400 if len(q) else np.nan
        for name,c in weather.items():x['lag_weather_'+name]=q[c].tail(3).mean()
        club=str(int(q.club_code.iloc[-1])) if len(q) else None
        return x,q,club
    for s in SEASONS:
        # All query timestamps are fixed from dated pool manifests. No outcomes.
        requests=[]
        for gw in range(1,39):
            folder=CACHE/s/f'gw{gw:02d}';man=common.read(folder/'manifest.json');path=folder/'pool.csv.gz';assert sha(path)==man['files']['pool.csv.gz'];p=pd.read_csv(path);at=EARLY if (s,gw)==('2024-25',15) else pd.Timestamp(man['forecast_at'])
            for c in ['price_available_at','position_available_at','club_available_at']:assert pd.to_datetime(p[c],utc=True).lt(at).all()
            p.loc[p.code.isin(evidence.loc[evidence.season.eq(s)&evidence.effective.le(at),'code']),'can_buy']=False
            assert set(p.club)<=set(namecodes);requests.append((gw,at,p,man));deps[str(path.relative_to(R))]=sha(path);deps[str((folder/'manifest.json').relative_to(R))]=sha(folder/'manifest.json')
        state=role.Strength();events={};pre={}
        for g in games[games.season.eq(s)].to_dict('records'):
            events.setdefault(pd.Timestamp(g['kickoff']),{'kick':[],'release':[],'query':[]})['kick'].append(g);events.setdefault(pd.Timestamp(g['available']),{'kick':[],'release':[],'query':[]})['release'].append(g)
        for req in requests:events.setdefault(req[1],{'kick':[],'release':[],'query':[]})['query'].append(req)
        for at,event in sorted(events.items()):
            for gw,_,pool,man in event['query']:
                snapshots_at=[v for v in snapgroups.get((s,gw),[]) if v['source_time'] and pd.Timestamp(v['source_time'])<at]
                fresh=bool(snapshots_at and workload.truth(snapshots_at[0]['calendar_usable']) and (at-pd.Timestamp(snapshots_at[0]['source_time'])).total_seconds()<=14*86400)
                cal_by_club={};future_by_club={}
                for club in pool.club.unique():
                    code=namecodes[club];own=state.state(code);ownfixtures=[v for v in snapshots_at if club in [v['home_team'],v['away_team']]];bound=bool(ownfixtures and all(v['event'] for v in ownfixtures));known=fresh and bound
                    f=dict(u_own_attack=own['attack_index'],u_own_concession=own['concession_index'],u_calendar_source=str(snapshots_at[0]['source_time']) if snapshots_at else None)
                    for j in range(8):
                        fs=[v for v in ownfixtures if v['event'] and int(float(v['event']))==gw+j] if known else []
                        op=[state.state(namecodes[v['away_team'] if v['home_team']==club else v['home_team']]) for v in fs]
                        f[f'u_count_{j}']=float(len(fs)) if known else np.nan;f[f'u_home_{j}']=float(np.mean([v['home_team']==club for v in fs])) if fs else np.nan;f[f'u_opp_attack_{j}']=float(np.mean([v['attack_index'] for v in op])) if op else np.nan;f[f'u_opp_concession_{j}']=float(np.mean([v['concession_index'] for v in op])) if op else np.nan
                    f['u_count3']=sum(f[f'u_count_{j}'] for j in range(min(3,39-gw))) if known else np.nan
                    future_by_club[club]=f
                for r in pool.itertuples():
                    key=(s,gw,int(r.code));present=key in source.index;old=source.loc[key] if present else None;rebuild=not present or bool(old.excluded_origin)
                    x={c:old[c] if present else np.nan for c in cols};native_max=None;wl_max=None
                    if rebuild:
                        hx,q,oldclub=history(r.code,s,at);x.update(hx);native_max=str(q.available.iloc[-1]) if len(q) else None
                        current=[v for v in rh.get((s,int(r.code)),[]) if pd.Timestamp(v['observation_available_after_proxy'])<at];year=int(s[:4])-1;previous=f'{year}-{str(year+1)[-2:]}';prior=[v for v in rh.get((previous,int(r.code)),[]) if pd.Timestamp(v['observation_available_after_proxy'])<at]
                        rc=role.role_context(current,prior,at.to_pydatetime(),oldclub)
                        for label in ['start','sub','none','unknown']:rc['pr_last_role_'+label]=float(rc['pr_last_role']==label) if rc['pr_last_role'] is not None else np.nan
                        x.update({c:rc.get(c,np.nan) for c in groups['role']})
                        b=stores[s].calculate(str(int(r.code)),at.to_pydatetime());w=dict(b,**workload.national(str(int(r.code)),at.to_pydatetime(),b,intl[s]));x.update({c:w.get(c,np.nan) for c in groups['workload']});wl_max=max([pd.Timestamp(v) for v in [w.get('wl_latest_input_available_at'),w.get('wl_international_latest_input_available_at')] if v],default=None)
                        team=b['wl_last_observed_club'];ck=(gw,team)
                        if ck not in cal_by_club:cal_by_club[ck]=workload.calendar(team,s,gw,at.to_pydatetime(),snapshots_at,announcements)
                        x.update({c:cal_by_club[ck].get(c,np.nan) for c in groups['calendar']})
                        own=state.state(oldclub);ds={'ds_own_'+k:v for k,v in own.items() if k!='latest_available'}
                        name=q.historical_team.iloc[-1] if len(q) else None
                        for h in [1,3]:
                            fs=[v for v in snapshots_at if name and name in [v['home_team'],v['away_team']] and v['event'] and gw<=int(float(v['event']))<gw+h] if fresh else []
                            op=[state.state(namecodes[v['away_team'] if v['home_team']==name else v['home_team']]) for v in fs]
                            for kind in ['attack_index','concession_index']:ds[f'ds_opponent_{kind}_h{h}']=float(np.mean([v[kind] for v in op])) if op else np.nan
                            ds[f'ds_known_matches_h{h}']=len(fs) if fresh and oldclub is not None else np.nan
                        x.update({c:ds.get(c,np.nan) for c in groups['strength']})
                        if present:
                            # AV/SP were originally calculated at the actual11UTC
                            # deadline. Preserve only their timestamp-qualified data.
                            assert (s,gw)==('2024-25',15)
                        cases.append(dict(season=s,round=gw,code=int(r.code),reason='earlier_deadline' if present else 'pool_row_missing_from_observation_table'))
                    if native_max:assert pd.Timestamp(native_max)<at
                    if wl_max is not None:assert wl_max<at
                    row=dict(season=s,round=gw,code=int(r.code),row_id=f'{s}:{gw}:{int(r.code)}',forecast_at=at,position=r.position,price_tenths=r.price_tenths,can_buy=bool(r.can_buy),metadata_complete=bool(r.metadata_complete),native_current_history_eligible=bool(old.target_history_eligible) if present else True,source_row_present=present,reconstructed=rebuild,**x,**future_by_club[r.club]);profiles.append(row)
                    timing.append(dict(season=s,round=gw,code=int(r.code),forecast_at=str(at),reconstructed=rebuild,latest_native=native_max,latest_workload=str(wl_max) if wl_max is not None else None,strength_latest=max((g['available'] for g in state.games),default=None),calendar_latest=future_by_club[r.club]['u_calendar_source']))
                print('FULL POOL',s,gw,len(pool),'reconstructed',sum(v['season']==s and v['round']==gw for v in cases),flush=True)
            for g in event['kick']:pre[g['fixture']]=state.pre(g)
            for g in event['release']:state.add(g,pre[g['fixture']])
    frame=pd.DataFrame(profiles);assert not frame.duplicated(KEY).any()
    for c in cols:frame[c]=pd.to_numeric(frame[c],errors='raise').astype('float32')
    frame['teacher_eligible']=frame.can_buy&frame.metadata_complete&frame.native_current_history_eligible
    for j in range(8):
        lab=teacher_labels.copy();lab['round']-=j;lab=lab.rename(columns={'target_points_1':f'y_{j}','target_history_eligible':f'y_eligible_{j}','label_at_1':f'y_at_{j}'});frame=frame.merge(lab,on=KEY,how='left',validate='one_to_one');frame.loc[~frame[f'y_eligible_{j}'].eq(True),f'y_{j}']=np.nan
    frame.to_pickle(P/'pool_features.pkl');pd.DataFrame(timing).to_csv(P/'feature_timing.csv.gz',index=False);pd.DataFrame(cases).to_csv(P/'reconstructed_rows.csv',index=False)
    dependencies=[Path(__file__),common.MASTER,D/'manifest.json',D/'schema.json',D/'training.pkl',R/'datasets/fpl_role_strength_v1/build.py',R/'datasets/fpl_role_strength_v1/common.py',R/'datasets/fpl_role_strength_v1/contract.json',R/'datasets/fpl_role_strength_v1/player_history_audit.csv.gz',R/'datasets/fpl_role_strength_v1/fixture_strength_audit.csv',CTX/'build_context.py',CTX/'common.py',CTX/'workload_store.py',CTX/'build_calendar.py',CTX/'manifest.json',CTX/'fixture_snapshots.csv.gz',CTX/'historical_announced_club_fixtures.csv',CTX/'player_minutes.csv.gz',CTX/'matches.csv.gz',R/'reports/loan_history_repair_2026_10_25_v3/evidence.csv']
    deps.update({str(p.relative_to(R)):sha(p) for p in dependencies});atomic_json(P/'input_view_manifest.json',dict(rows=len(frame),core_features=len(cols),parent_dataset='fpl_common_training_v1',input_hashes=deps,files={n:sha(P/n) for n in ['pool_features.pkl','feature_timing.csv.gz','reconstructed_rows.csv']},reconstructed_rows=len(cases),effective_earlier_deadline=str(EARLY),missing_target_not_zero=True,manager_outcomes_read=False))
    print('POOL VIEW SEALED',len(frame),len(cases),flush=True)

if __name__=='__main__':build()
