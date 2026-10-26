"""Operational component recipe: strict clocks, common features and hard eligibility.

No target-match observed weather, unpublished outcome or stale-status fallback.
Historical replay is reconstructed evidence, never a prospective forecast receipt.
"""
import os
for _key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[_key]='1'
import collections, datetime, hashlib, json, lzma, pickle, sys
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R))
from scripts import common_model_retest as common
from scripts import common_season_inputs as inputs
from scripts import common_season_comparison as projection
from model_lab.common import sha, atomic_json, verify_files
D=R/'datasets/fpl_common_training_v3'
P=Path(os.environ.get('FPL_COMPONENT_RELEASE',str(R/'reports/component_operational_activation_2026_10_26')))
FIT=R/'reports/matched_season_retest_2026_10_25_v5'
SEASON='2026-27'
REFITS=tuple(range(1,39,4))
STATS={'minutes':'native_minutes','points':'target_total_points','goals':'native_goals_scored','assists':'native_assists','clean':'native_clean_sheets','starts':'native_starts','saves':'saves'}
WEATHER={'temperature':'weather_temperature_2m_mean','wind':'weather_wind_speed_10m_mean','rain':'weather_precipitation_sum','sun':'weather_sunshine_minutes_daylight_capped'}

def read(path): return json.loads(Path(path).read_text())
def save(path,value):
    with Path(path).open('wb') as f:pickle.dump(value,f)
def load(path):
    with Path(path).open('rb') as f:return pickle.load(f)
def utc(value):
    at=pd.Timestamp(value)
    if at.tzinfo is None:raise ValueError('Timezone required')
    return at.tz_convert('UTC')

def verify_snapshot(folder,now=None):
    folder=Path(folder);receipts=read(folder/'receipts.json')
    for receipt in receipts:
        if sha(R/receipt['file'])!=receipt['sha256']:raise ValueError('Changed official source')
    boot=read(folder/'bootstrap.json');fs=pd.DataFrame(read(folder/'fixtures.json'))
    now=utc(now or pd.Timestamp.now(tz='UTC'));times=[utc(r['retrieved_at']) for r in receipts]
    if max(times)>=now or now-min(times)>pd.Timedelta(hours=24):raise ValueError('Stale or future official receipt')
    event=next(e for e in boot['events'] if e['is_next'])
    if not now<utc(event['deadline_time']):raise ValueError('Deadline already passed')
    if len(fs)!=380 or fs.id.duplicated().any() or len(boot['teams'])!=20:raise ValueError('Incomplete official calendar')
    if len(receipts)!=len(boot['elements'])+2:raise ValueError('Missing player histories')
    return boot,fs,event,now,times

def observations(folder,boot,fixtures,at):
    """Every actual released official player/fixture row, including zero minutes."""
    teams={e['id']:e for e in boot['teams']};fixtures=fixtures.set_index('id');rows=[];omitted=0
    for e in boot['elements']:
        for h in read(Path(folder)/f'element_{e["id"]}.json')['history']:
            f=fixtures.loc[h['fixture']];ko=utc(h['kickoff_time']);available=ko+pd.Timedelta(hours=24)
            if not f['finished'] or available>=at:omitted+=1;continue
            club=int(f.team_h if h['was_home'] else f.team_a);opp=int(f.team_a if h['was_home'] else f.team_h)
            row=dict(season=SEASON,round=int(h['round']),fixture=int(h['fixture']),code=int(e['code']),club_code=int(teams[club]['code']),opponent_club_code=int(teams[opp]['code']),historical_team=teams[club]['name'],was_home=bool(h['was_home']),fixture_kickoff_time=ko.isoformat(),kickoff_time=ko.isoformat(),observation_available_after_proxy=available.isoformat(),available=available,kickoff=ko,position={1:'GK',2:'DEF',3:'MID',4:'FWD'}[e['element_type']],value=h['value'],history_eligible=True,target_total_points=float(h['total_points']),native_minutes=float(h['minutes']),native_starts=float(h['starts']),saves=float(h['saves']),native_total_points=float(h['total_points']),native_yellow_cards=h['yellow_cards'],native_red_cards=h['red_cards'],team_h_score=f.team_h_score,team_a_score=f.team_a_score)
            for name in ['goals_scored','assists','clean_sheets']:row['native_'+name]=float(h[name])
            row['start_qualified']=True;row['role']='start' if h['starts'] else 'sub' if h['minutes'] else 'none'
            rows.append(row)
    d=pd.DataFrame(rows);assert not d.duplicated(['season','fixture','code']).any()
    correction=inputs.isolated_module('_component_history_guard',R/'datasets/fpl_loan_history_repair_v3/loader.py')
    good=correction.history_mask(d);rejected=d[~good].copy();d=d[good].copy()
    # Current departure reports do not erase valid earlier history. Without a
    # dated departure interval, suspicious post-report observations fail closed.
    (P/'history_rejected.csv').parent.mkdir(exist_ok=True)
    rejected.to_csv(P/'history_rejected.csv',index=False)
    audit=dict(rows=len(d),zero_minutes=int(d.native_minutes.eq(0).sum()),omitted_unreleased_or_unfinished=omitted,excluded_dated_departure_rows=len(rejected),latest_available=str(d.available.max()),rounds=d.groupby('round').size().to_dict())
    return d,audit

def calendar_context(frame,states,club,g,at,groups):
    x={c:np.nan for c in groups['calendar']+groups['strength']};own=states[int(club)]
    ownfs=frame[frame.home.eq(club)|frame.away.eq(club)];bound=len(ownfs)==38 and ownfs.event.notna().all()
    x['cal_PL_round_bindings_complete']=float(bound)
    x.update({'ds_own_'+k:float(v) if v is not None else np.nan for k,v in own.items() if 'ds_own_'+k in x})
    x.update(u_own_attack=own['attack_index'],u_own_concession=own['concession_index'])
    for h in [1,3,6]:
        fs=ownfs[ownfs.event.between(g,min(38,g+h-1))];counts=[int(ownfs.event.eq(r).sum()) for r in range(g,min(39,g+h))] if bound else []
        x[f'cal_PL_fixtures_next_{h}_rounds']=len(fs) if len(ownfs) else np.nan
        x[f'cal_PL_blank_rounds_next_{h}']=sum(v==0 for v in counts) if bound else np.nan;x[f'cal_PL_double_rounds_next_{h}']=sum(v>1 for v in counts) if bound else np.nan
        if h in [1,3]:
            ops=[states[int(v.away if v.home==club else v.home)] for v in fs.itertuples()]
            x[f'ds_known_matches_h{h}']=len(fs) if len(ownfs) else np.nan
            for k in ['attack_index','concession_index']:x[f'ds_opponent_{k}_h{h}']=np.mean([v[k] for v in ops]) if ops else np.nan
    times=pd.to_datetime(ownfs.kickoff_time,utc=True,errors='coerce');times=times[times.ge(at)]
    x['cal_hours_until_next_known_club_fixture']=(times.min()-at).total_seconds()/3600 if len(times) else np.nan
    for days in [7,14,28]:x[f'cal_PL_registered_fixtures_next_{days}d']=int(times.lt(at+pd.Timedelta(days=days)).sum()) if len(ownfs) else np.nan
    for j in range(8):
        fs=ownfs[ownfs.event.eq(g+j)];ops=[states[int(v.away if v.home==club else v.home)] for v in fs.itertuples()]
        x[f'u_count_{j}']=len(fs) if len(fs) or bound else np.nan;x[f'u_home_{j}']=float(fs.home.eq(club).mean()) if len(fs) else np.nan
        for kind in ['attack','concession']:x[f'u_opp_{kind}_{j}']=np.mean([v[kind+'_index'] for v in ops]) if ops else np.nan
    counts=[x[f'u_count_{j}'] for j in range(min(3,39-g))];x['u_count3']=sum(counts) if all(np.isfinite(v) for v in counts) else np.nan
    # Future unversioned cup announcements are absent in the tested main arm.
    for c in groups['calendar']:
        if c.startswith('cal_announced_cup_'):x[c]=np.nan
    return x

def historical_requests():
    ctx=R/'datasets/fpl_all_competitions_context_v1';versions={};meta={}
    for path in sorted((ctx/'raw').glob('calendar_commits_2026-27*.json')):
        for v in read(path):
            if isinstance(v,dict) and 'commit' in v:meta[v['sha']]=max(utc(v['commit'][k]['date']) for k in ['author','committer'])
    for v in read(R/'FPL_training_dataset/research/current/calendar_audit/source_commits.json').get(SEASON,[]):meta[v['sha']]=max(utc(v[k]) for k in ['author_time','committer_time'])
    for commit,t in meta.items():
        paths=[ctx/'raw'/f'calendar_{SEASON}_{commit}.csv',R/f'FPL_training_dataset/research/current/calendar_audit/portable/{SEASON}_{commit}.csv']
        path=next((p for p in paths if p.exists()),None)
        if path:versions[commit]=(t,path)
    requests=[]
    for v in sorted(read(R/'datasets/fpl_availability_all_seasons_v1/selected_sources.json'),key=lambda v:int(v['round'])):
        if v['season']!=SEASON or v['format']!='bootstrap':continue
        boot=json.loads(lzma.open(R/v['source_file'],'rt').read());g=int(v['round']);event=next(e for e in boot['events'] if e['id']==g);at=utc(event['deadline_time']);source=utc(v['source_time'])
        if g>7:continue
        assert source<at and at-source<=pd.Timedelta(hours=24)
        selected=[(commit,t,path) for commit,(t,path) in versions.items() if t<at]
        if not selected:raise ValueError(f'No archived predeadline calendar for GW{g}')
        commit,t,path=max(selected,key=lambda v:v[1]);f=pd.read_csv(path);teams={e['id']:e['code'] for e in boot['teams']};f['home']=f.team_h.map(teams);f['away']=f.team_a.map(teams)
        requests.append(dict(g=g,at=at,boot=boot,frame=f,source=source,calendar_source=t,bootstrap_file=v['source_file'],calendar_file=str(path.relative_to(R)),prospective=False))
    if {q['g'] for q in requests}!=set(range(1,8)):raise ValueError('Incomplete current season predeadline archive')
    return requests

def feature_views(native,requests):
    schema=read(D/'schema.json');cols=schema['features'];groups=schema['feature_groups']
    role=inputs.isolated_module('_operational_component_role',R/'datasets/fpl_role_strength_v1/build.py',('common',))
    work=inputs.isolated_module('_operational_component_work',R/'datasets/fpl_all_competitions_context_v1/build_context.py',('common','workload_store','build_calendar'))
    pilot=inputs.isolated_module('_operational_component_av',R/'datasets/fpl_availability_pilot_2023_24_v1/build.py')
    sp=inputs.isolated_module('_operational_component_sp',R/'datasets/fpl_set_piece_roles_v1/build.py',('common',))
    master=pd.read_csv(common.MASTER,low_memory=False);master['available']=pd.to_datetime(master.observation_available_after_proxy,utc=True);master['kickoff']=pd.to_datetime(master.fixture_kickoff_time,utc=True)
    master=master[master.history_eligible].copy();old_weather=master[master.season.eq(SEASON)].set_index(['fixture','code'])
    for c in WEATHER.values():native[c]=[old_weather.at[(f,code),c] if (f,code) in old_weather.index else np.nan for f,code in zip(native.fixture,native.code)]
    hist=pd.concat([master[master.season.ne(SEASON)],native],ignore_index=True);histories={int(k):q.sort_values(['available','fixture']) for k,q in hist.groupby('code',sort=False)}
    ah=pd.read_csv(R/'datasets/fpl_role_strength_v1/player_history_audit.csv.gz',low_memory=False);ah=ah[ah.history_eligible&ah.season.ne(SEASON)]
    ah=pd.concat([ah,native],ignore_index=True);rh={(s,int(c)):q.sort_values(['fixture_kickoff_time','fixture']).to_dict('records') for (s,c),q in ah.groupby(['season','code'])}
    seasons,_,_,pl,plfs,cups,cupfs,rosters,nationals=work.inputs();z=dict(seasons[SEASON]);z["end"]=datetime.datetime(2027,7,1,tzinfo=datetime.timezone.utc)
    pl=[e for e in pl if not e['key'].startswith(SEASON+':')];plfs=[e for e in plfs if e['season']!=SEASON];fixture_rows={}
    for r in native.itertuples():
        key=f'{SEASON}:{r.fixture}';t=r.kickoff.to_pydatetime();pl.append(dict(code=str(r.code),key=key,kickoff=t,available=r.available.to_pydatetime(),end=t+datetime.timedelta(minutes=120),team=r.historical_team,minutes=r.native_minutes,starts=r.native_starts,competition='Premier League',extra_time=False));fixture_rows.setdefault(key,dict(key=key,kickoff=t,available=r.available.to_pydatetime(),teams=set(),season=SEASON))['teams'].add(r.historical_team)
    plfs+=list(fixture_rows.values());inside=lambda a:[e for e in a if z['history_start']<=e['kickoff']<z['end']]
    store=work.Store(inside(pl),inside(cups),inside(plfs),inside(cupfs),rosters,{});store.season_start=z['start'];intl=collections.defaultdict(list)
    for r in nationals[SEASON]:intl[r['code']].append(r)
    minute_events=[dict(code=e['code'],team=e['team'],kickoff=e['kickoff'],available=e['available'],minutes=e['minutes']) for e in pl];minute_history=pilot.History(minute_events)
    games=[]
    for fixture,q in native.groupby('fixture'):
        a=q.iloc[0];home=int(a.club_code if a.was_home else a.opponent_club_code);away=int(a.opponent_club_code if a.was_home else a.club_code)
        games.append(dict(fixture=str(fixture),home=str(home),away=str(away),home_goals=float(a.team_h_score),away_goals=float(a.team_a_score),kickoff=a.kickoff,available=a.available))
    allviews=[];audits=[];previous={}
    for req in requests:
        at=req['at'];g=req['g'];boot=req['boot'];teams={e['id']:e for e in boot['teams']};frame=req['frame'].copy()
        # Completed outcomes can reconcile old fixture bindings only after +24h.
        for game in games:
            if game['available']<at:
                rows=native[native.fixture.eq(int(game['fixture']))];frame.loc[frame.id.eq(int(game['fixture'])),'event']=rows['round'].iloc[0];frame.loc[frame.id.eq(int(game['fixture'])),'kickoff_time']=game['kickoff'].isoformat()
        strength=role.Strength();pre={};events={}
        for game in games:
            for typ,col in [('kick','kickoff'),('release','available')]:events.setdefault(game[col],{'kick':[],'release':[]})[typ].append(game)
        for time,event in sorted(events.items()):
            if time>=at:break
            for game in event['kick']:pre[game['fixture']]=strength.pre(game)
            for game in event['release']:strength.add(game,pre[game['fixture']])
        states={t['code']:strength.state(str(t['code'])) for t in teams.values()};contexts={c:calendar_context(frame,states,c,g,at,groups) for c in states}
        av={};spframe={};event=next(e for e in boot['events'] if e['id']==g);binding='next' if event['is_next'] else 'this' if event['is_current'] else None
        assert binding and req['source']<at and at-req['source']<=pd.Timedelta(hours=24)
        for e in boot['elements']:
            code=str(e['code']);news=e.get('news') or '';added=utc(e['news_added']) if e.get('news_added') else None;valid=added is None or added<=req['source'];status=e.get('status') or '';why=pilot.reason(news);departed=status=='u' or (status=='n' and why=='transfer_or_loan');prior=previous.get(code);consecutive=bool(prior and prior['round']==g-1 and prior['known']);chance=e.get('chance_of_playing_next_round' if binding=='next' else 'chance_of_playing_this_round')
            person=dict(code=code,round=g,element=str(e['id']),name=e['web_name'],team_name=teams[e['team']]['name'],position=e['element_type'],forecast_at=at.isoformat(),snapshot_at_proxy=req['source'].isoformat(),source_commit='',source_url='https://fantasy.premierleague.com/api/bootstrap-static/',source_blob_sha='',known=valid,status=status,reason=why,news=news,news_added=added.isoformat() if added else '',chance=chance if valid else None,chance_binding=binding,news_age_days=(at-added).total_seconds()/86400 if added and valid else None,previous_status=prior['status'] if consecutive else '',previous_snapshot_consecutive=consecutive,reported_return_to_available=bool(consecutive and prior['status'] in ['i','s','n'] and status=='a') if valid else None,expected_return_text='',core=valid and status in ['a','d','i','s','n'] and not departed,departure=departed)
            av[code]=person
            roles={}
            for name,prefix in sp.ROLES.items():
                rank,good=sp.order(e.get(prefix+'_order'));roles[name]=dict(known=valid and prefix+'_order' in e and good,order=rank,text=e.get(prefix+'_text') or '')
            spframe[code]=dict(code=code,element=str(e['id']),team=person['team_name'],status=status,status_known=valid,departure=departed,roles=roles)
        weights={(p['code'],days):minute_history.minutes(p['code'],p['team_name'],at.to_pydatetime(),days) for p in av.values() for days in [28,90]}
        teamav=collections.defaultdict(list);teamsp=collections.defaultdict(list)
        for p in av.values():teamav[p['team_name']].append(p)
        for p in spframe.values():teamsp[p['team']].append(p)
        rows=[]
        for e in boot['elements']:
            code=int(e['code']);own=av[str(code)];q=histories.get(code,hist.iloc[:0]);q=q[q.available.lt(at)];cur=q[q.season.eq(SEASON)];old=q[q.season.lt(SEASON)]
            if len(old):old=old[old.season.eq(old.season.max())]
            x={c:np.nan for c in cols};x.update(h_cur_count=len(cur),h_old_count=len(old))
            for label,a in [('cur',cur),('old',old)]:
                for w in [3,10]:
                    for name,c in STATS.items():x[f'h_{label}_{w}_{name}']=a[c].tail(w).mean()
            for name in STATS:
                nc=min(len(cur),10);no=min(len(old),10);x['h_fixed_'+name]=((nc*x[f'h_cur_10_{name}'] if nc else 0)+(no*x[f'h_old_10_{name}'] if no else 0))/(nc+no) if nc+no else np.nan
            x['h_last_price']=q.value.iloc[-1] if len(q) else np.nan;pos=q.position.iloc[-1] if len(q) else None
            for p in ['GK','DEF','MID','FWD']:x['h_pos_'+p]=float(pos==p) if pos else np.nan
            x['h_days_since']=(at-q.kickoff.iloc[-1]).total_seconds()/86400 if len(q) else np.nan
            for name,c in WEATHER.items():x['lag_weather_'+name]=q[c].tail(3).mean()
            oldclub=str(int(q.club_code.iloc[-1])) if len(q) else None
            current=[r for r in rh.get((SEASON,code),[]) if utc(r['observation_available_after_proxy'])<at];prior=[r for r in rh.get(('2025-26',code),[]) if utc(r['observation_available_after_proxy'])<at]
            rc=role.role_context(current,prior,at.to_pydatetime(),oldclub)
            for label in ['start','sub','none','unknown']:rc['pr_last_role_'+label]=float(rc['pr_last_role']==label) if rc['pr_last_role'] is not None else np.nan
            x.update({c:rc.get(c,np.nan) for c in groups['role']})
            base=store.calculate(str(code),at.to_pydatetime());wl=dict(base,**work.national(str(code),at.to_pydatetime(),base,intl));x.update({c:wl.get(c,np.nan) for c in groups['workload']})
            a=pilot.feature(own,[p for p in teamav[own['team_name']] if p['code']!=str(code)],weights)
            x.update({c:a.get(c,np.nan) for c in groups['availability']})
            for status in ['a','d','i','s','n','u']:x['av_status_'+status]=float(own['status']==status) if own['known'] else np.nan
            for name in sp.ROLES:x.update({c:v for c,v in sp.role_features(spframe[str(code)],teamsp[own['team_name']],name).items() if c in groups['set_piece']})
            x['sp_own_status_known']=own['known'];x.update(contexts[teams[e['team']]['code']])
            departed=own['known'] and own['departure'];blocked=departed or (own['known'] and own['chance']==0)
            # A legitimate injury zero remains a training/calibration example.
            # Selection bans are applied after prediction, as in the v8 test.
            # Removed departure observations cannot supply a complete label.
            row=dict(season=SEASON,round=g,code=code,pid=code,name=e['web_name'],pos=int(e['element_type']),position={1:'GK',2:'DEF',3:'MID',4:'FWD'}[e['element_type']],club=teams[e['team']]['name'],club_code=teams[e['team']]['code'],price_tenths=int(e['now_cost']),price=e['now_cost']/10,forecast_at=at,can_buy=not blocked,metadata_complete=True,teacher_eligible=True,eligibility_origin_round=g,status=own['status'],chance=own['chance'],known_departed=bool(departed),confirmed_out_current=bool(blocked),**x)
            for j in range(8):row[f'can_start_{j}']=not departed and (not blocked if j==0 else True)
            rows.append(row)
            audits.append(dict(round=g,code=code,forecast_at=str(at),latest_history=str(q.available.max()) if len(q) else None,latest_workload=str(wl.get('wl_latest_input_available_at')),latest_international=str(wl.get('wl_international_latest_input_available_at')),source_time=str(req['source']),calendar_time=str(req['calendar_source']),prospective=req['prospective']))
        previous=av;view=pd.DataFrame(rows)
        for c in cols:view[c]=pd.to_numeric(view[c],errors='raise').astype('float32')
        allviews.append(view);print('FEATURES',g,len(view),flush=True)
    return pd.concat(allviews,ignore_index=True),pd.DataFrame(audits)

def training_labels(native,views):
    # Targets exist only for complete finished rounds. No partial round or
    # unregistered missing player is converted into a zero label.
    boot=read(P/'raw/bootstrap.json');fixtures=pd.DataFrame(read(P/'raw/fixtures.json'));completed={e['id'] for e in boot['events'] if e['finished']}
    labels=[]
    for (g,code),q in native[native['round'].isin(completed)].groupby(['round','code']):
        allround=fixtures[fixtures.event.eq(g)];release=pd.to_datetime(allround.kickoff_time,utc=True)+pd.Timedelta(hours=24)
        if not allround.finished.all() or release.isna().any() or release.max()>=views.forecast_at.max():continue
        pos=q.position.iloc[0];attack=(q.native_goals_scored*{'GK':10,'DEF':6,'MID':5,'FWD':4}[pos]+q.native_assists*3).sum();appearance=(q.native_minutes.ge(60)*2+(q.native_minutes.gt(0)&q.native_minutes.lt(60))).sum();points=q.target_total_points.sum()
        labels.append(dict(season=SEASON,round=g,code=code,target_points_1=points,target_minutes_1=q.native_minutes.sum(),target_starts_1=q.native_starts.sum(),target_attack_1=attack,target_appearance_1=float(appearance),target_residual_1=points-attack-appearance,label_at_1=release.max(),target_history_eligible=True))
    labels=pd.DataFrame(labels);targets=['points','minutes','starts','attack','appearance','residual'];d=views.merge(labels,on=common.KEY,how='left',validate='one_to_one')
    for h in [3]:
        total={t:np.zeros(len(d)) for t in targets};times=[];complete=np.ones(len(d),bool)
        for j in range(h):
            shifted=labels.copy();shifted['round']-=j;q=d[common.KEY].merge(shifted,on=common.KEY,how='left',validate='one_to_one');complete&=q.target_history_eligible.eq(True).to_numpy()
            for t in targets:total[t]+=q[f'target_{t}_1'].to_numpy(float)
            times.append(q.label_at_1)
        for t in targets:d[f'target_{t}_{h}']=np.where(complete,total[t],np.nan)
        d[f'label_at_{h}']=pd.concat(times,axis=1).max(axis=1);d.loc[~complete,f'label_at_{h}']=pd.NaT
    d['train_eligible']=d.target_history_eligible.eq(True)
    for j in range(8):
        shifted=labels[common.KEY+['target_points_1','label_at_1']].copy();shifted['round']-=j;shifted=shifted.rename(columns={'target_points_1':f'y_{j}','label_at_1':f'y_at_{j}'});d=d.merge(shifted,on=common.KEY,how='left',validate='one_to_one')
    return d

def prepare():
    boot,fixtures,event,at,times=verify_snapshot(P/'raw');native,history_audit=observations(P/'raw',boot,fixtures,at);native.to_pickle(P/'native_current.pkl')
    registry=R/'overview/COMPONENT_RELEASES.json';previous=None
    if registry.exists():
        releases=[r for r in read(registry)['releases'] if R/r['directory']!=P]
        if releases:
            previous=R/releases[-1]['directory'];verify_files(R,read(previous/'forecast_seal.json')['files'])
    requests=[] if previous else historical_requests();teams={e['id']:e['code'] for e in boot['teams']};fixtures['home']=fixtures.team_h.map(teams);fixtures['away']=fixtures.team_a.map(teams)
    requests.append(dict(g=event['id'],at=at,boot=boot,frame=fixtures,source=times[0],calendar_source=times[1],bootstrap_file=str((P/'raw/bootstrap.json').relative_to(R)),calendar_file=str((P/'raw/fixtures.json').relative_to(R)),prospective=True))
    views,timing=feature_views(native,requests)
    if previous:
        prior=load(previous/'current.pkl');prior=prior[prior.forecast_at.lt(at)&prior['round'].lt(event['id'])];prior=prior.drop(columns=[c for c in prior if c.startswith(('target_','label_at_','y_'))]+['train_eligible'],errors='ignore')
        views=pd.concat([prior,views],ignore_index=True);save(P/'prior_oof.pkl',load(previous/'current_oof.pkl'))
    d=training_labels(native,views);save(P/'current.pkl',d);timing.to_csv(P/'timing.csv.gz',index=False)
    sources=[{k:str(v) for k,v in req.items() if k not in ['boot','frame']} for req in requests];atomic_json(P/'origins.json',sources);atomic_json(P/'history_audit.json',history_audit)
    features=read(D/'schema.json')['features'];d[d['round'].eq(event['id'])][features].notna().mean().to_csv(P/'live_feature_coverage.csv')
    atomic_json(P/'prepared.json',dict(issued_at=str(at),deadline=event['deadline_time'],round=event['id'],previous_release=str(previous.relative_to(R)) if previous else None,refit_round=1+4*((event['id']-1)//4),rows=len(d),features=len(features),history=history_audit,unreleased_outcomes_excluded=True,supervised_rounds=sorted(d.loc[d.train_eligible,'round'].unique().tolist()),historical_origins_reconstructed=True,statistical_vintage='kickoff+24h proxy; source statistics may have later corrections',new_match_weather='Unknown fresh lagged weather is NaN, never zero or a future observation',external_workload='Latest scoped observed FA/EFL/UEFA and national-team lower bounds; unknown coverage retained',files={n:sha(P/n) for n in ['current.pkl','native_current.pkl','timing.csv.gz','origins.json','history_audit.json']}))

def fit_base(g):
    info=read(P/'prepared.json');d=load(P/'current.pkl');cols=read(D/'schema.json')['features'];at=d[d['round'].eq(g)].forecast_at.iloc[0];historical=pd.read_pickle(D/'training.pkl');train=pd.concat([historical,d],ignore_index=True)
    original=common.cbreg
    def cb():
        model=original();model.set_params(allow_const_label=True);return model
    common.cbreg=cb
    q=d[d['round'].between(g,g+3)].copy();audit=[]
    for h in [1,3]:
        ts=[f'target_{t}_{h}' for t in ['points','minutes','starts','attack','appearance','residual']];tr=train[train.train_eligible&train.forecast_at.lt(at)&train[f'label_at_{h}'].lt(at)&train[ts].notna().all(axis=1)].copy();assert len(tr)>1000
        bundle=common.fit_arm('component',tr,cols,h);path=P/f'models/gw{g:02d}_h{h}.pkl';path.parent.mkdir(exist_ok=True);save(path,bundle);v,_,_=common.predict_arm(bundle,q);q[f'component_p{h}']=v[:,0];q[f'component_m{h}']=v[:,1]
        audit.append(dict(round=g,horizon=h,cutoff=str(at),rows=len(tr),current_rows=int(tr.season.eq(SEASON).sum()),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'label_at_{h}'].max()),file=str(path.relative_to(R)),sha256=sha(path),keys_sha256=common.keys_hash(tr)))
        print('FIT',g,h,len(tr),flush=True)
    save(P/f'base_gw{g:02d}.pkl',q);atomic_json(P/f'base_audit_gw{g:02d}.json',audit)

def fit_heads():
    current=load(P/'current.pkl');info=read(P/'prepared.json');g=info['round']
    if info['previous_release']:
        prior=load(P/'prior_oof.pkl');basecols=common.KEY+['component_p1','component_m1','component_p3','component_m3'];prior=current[current['round'].lt(g)].merge(prior[basecols],on=common.KEY,how='inner',validate='one_to_one');q=pd.concat([prior,load(P/f'base_gw{g:02d}.pkl')],ignore_index=True)
    else:q=pd.concat([load(P/f'base_gw{r:02d}.pkl') for r in [1,5,g]],ignore_index=True)
    assert not q.duplicated(common.KEY).any();save(P/'current_oof.pkl',q)
    past=pd.read_pickle(FIT/'head_data.pkl');teacher=pd.concat([past,q],ignore_index=True);at=q[q['round'].eq(g)].forecast_at.iloc[0];complete=teacher[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=teacher[[f'y_at_{j}' for j in range(3)]].max(axis=1);out=q[q['round'].eq(g)].copy();audits=[];heads={}
    for j in range(8):
        tr=teacher[teacher.teacher_eligible&teacher.forecast_at.lt(at)&teacher[f'y_{j}'].notna()&teacher[f'y_at_{j}'].lt(at)&complete&h3.lt(at)].copy()
        if info['previous_release'] and g not in REFITS:model=read(R/info['previous_release']/'heads.json')[str(j)]
        else:model=projection.fit_projection(tr,'component',j)
        heads[j]=model;out[f'xp_{j}']=projection.predict_projection(out,'component',model)
        audits.append(dict(offset=j,cutoff=str(at),rows=len(tr),current_rows=int(tr.season.eq(SEASON).sum()),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'y_at_{j}'].max()),max_h3_label=str(h3.loc[tr.index].max()),keys_sha256=common.keys_hash(tr)))
        mask=out.known_departed|(out.confirmed_out_current if j==0 else False);out.loc[mask,f'xp_{j}']=0
    atomic_json(P/'heads.json',{str(k):v for k,v in heads.items()});atomic_json(P/'head_audit.json',audits);save(P/'live_features.pkl',out);out[common.KEY+['forecast_at','name','position','club','price_tenths','can_buy','confirmed_out_current','known_departed']+[f'can_start_{j}' for j in range(8)]+[f'xp_{j}' for j in range(8)]].to_csv(P/'forecasts.csv',index=False)
    assert np.isfinite(out[[f'xp_{j}' for j in range(8)]]).all().all()
    atomic_json(P/'forecast_seal.json',dict(issued_at=str(at),sealed_at=str(pd.Timestamp.now(tz='UTC')),deadline=read(P/'prepared.json')['deadline'],round=g,prospective=True,files={str(p.relative_to(R)):sha(p) for p in [P/'forecasts.csv',P/'live_features.pkl',P/'heads.json',P/'head_audit.json',P/'prepared.json',Path(__file__),P/'raw/receipts.json']+list((P/'models').glob('*.pkl'))},teacher_clock='origin, offset label and all H3 teacher outcomes strictly before fit',refits=list(REFITS),expiry_hours=24))

class ComponentForecaster:
    """Default live loader. Expired inputs require a fresh capture and refit.

    A captured preview cannot silently become a fresh matchday recommendation.
    """
    def __init__(self,release=P):self.release=Path(release)
    def forecast(self,origin,horizon=8):
        seal=read(self.release/'forecast_seal.json');verify_files(R,seal['files']);now=utc(origin['forecast_at']);issued=utc(seal['issued_at'])
        if origin['season']!=SEASON or origin['round']!=seal['round'] or not 0<=horizon<=8:raise ValueError('Wrong sealed origin')
        if now<issued or now-issued>pd.Timedelta(hours=24) or now>=utc(seal['deadline']):raise ValueError('Refresh official data and component release before deciding')
        frame=pd.read_csv(self.release/'forecasts.csv');return frame,dict(model='common_component_h8_adaptive_v1',issued_at=str(issued),hard_eligibility_required=True,seal=str(self.release/'forecast_seal.json'))

    def decide(self,state,forecast_at):
        """Use the verified hard-constraint manager; never submit team changes."""
        seal=read(self.release/'forecast_seal.json');self.forecast(dict(season=SEASON,round=seal['round'],forecast_at=forecast_at))
        pool=load(self.release/'live_features.pkl');pool['market']=pool.price_tenths;mod,manager=hard_manager();xp=pool[[f'xp_{j}' for j in range(8)]].to_numpy(float)
        choice=manager.decide(pool,xp,state,seal['round'])
        return choice,dict(solver_calls=len(manager.ledger),automatic_team_changes=False)

def hard_manager():
    # Exact hash-checked backend that passed all228 historical decisions. Its
    # solver factory reads no historical roster or forecast data.
    from scripts import matched_availability_retest_v8 as guard
    return guard.solver()

def reuse_base(g):
    info=read(P/'prepared.json');previous=R/info['previous_release'];d=load(P/'current.pkl');q=d[d['round'].eq(g)].copy();audit=[]
    previous_info=read(previous/'prepared.json')
    for h in [1,3]:
        path=previous/f'models/gw{previous_info["round"]:02d}_h{h}.pkl';bundle=load(path);target=P/f'models/gw{g:02d}_h{h}.pkl';target.parent.mkdir(exist_ok=True);target.write_bytes(path.read_bytes());v,_,_=common.predict_arm(bundle,q);q[f'component_p{h}']=v[:,0];q[f'component_m{h}']=v[:,1];audit.append(dict(round=g,horizon=h,reused_same_four_round_bundle=True,refit_round=info['refit_round'],file=str(target.relative_to(R)),sha256=sha(target)))
    save(P/f'base_gw{g:02d}.pkl',q);atomic_json(P/f'base_audit_gw{g:02d}.json',audit)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='base':fit_base(int(sys.argv[2]))
    elif sys.argv[1]=='heads':fit_heads()
    elif sys.argv[1]=='reuse-base':reuse_base(int(sys.argv[2]))
    else:raise SystemExit('prepare | base ROUND | heads')
