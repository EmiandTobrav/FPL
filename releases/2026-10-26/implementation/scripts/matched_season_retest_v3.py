"""New retrospective experiment: carry archived calendars, matched rolling teachers.

Never writes source archives or operational artifacts. No target-weather input.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']: os.environ[k]='1'
import sys,json,lzma,pickle,copy,hashlib,subprocess,concurrent.futures,shutil
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import common_model_retest as common
from scripts import common_season_comparison as method
from scripts import common_season_inputs as inputs
from model_lab.common import atomic_json,sha,verify_files
from model_lab import fixed_season_forecaster as fixed
from model_lab.simulation import backend
from model_lab.manager_learning import Environment,settle
P=R/'reports/matched_season_retest_2026_10_25_v3';PREVIOUS=R/'reports/matched_season_retest_2026_10_25_v2';D=common.D;KEY=common.KEY
SEASONS=['2022-23','2023-24','2024-25','2025-26'];EVAL=SEASONS[1:];REFITS=list(range(1,39,4));ARMS=['component','operational_matched']
CTX=R/'datasets/fpl_all_competitions_context_v1'
native=common.module('_matched_native',R/'reports/fpl_simulator_2026_10_13/benchmark_forecaster.py')

def dump(name,obj):
    with (P/name).open('wb') as f:pickle.dump(obj,f,protocol=5)
def load(name):
    with (P/name).open('rb') as f:return pickle.load(f)
def cache(s):return R/('reports/fpl_simulator_2026_10_13/cache_manager' if s=='2025-26' else 'reports/fpl_improvement_2026_10_14/cache')
def pool(s,g):return pd.read_csv(cache(s)/s/f'gw{g:02d}/pool.csv.gz')
def status(stage,**kw):(P/'status.json').write_text(json.dumps(dict(stage=stage,at=str(pd.Timestamp.now(tz='UTC')),**kw),indent=2)+'\n')

def build():
    P.mkdir(exist_ok=True);assert not (P/'inputs.json').exists();status('building_inputs');deps={}
    def bind(p):deps[str(p.relative_to(R))]=sha(p)
    # Commit author and committer must BOTH precede the query. Inventory is
    # pooled before selection; an old per-origin selection cannot hide a source.
    versions={};meta={}
    for path in sorted((CTX/'raw').glob('calendar_commits_*.json')):
        bind(path);s=path.name[len('calendar_commits_'):len('calendar_commits_')+7]
        for v in json.loads(path.read_text()):
            if isinstance(v,dict) and 'commit' in v:meta[(s,v['sha'])]=max(pd.Timestamp(v['commit'][k]['date']) for k in ['author','committer'])
    sourcepath=R/'FPL_training_dataset/research/current/calendar_audit/source_commits.json';bind(sourcepath)
    for s,vs in json.loads(sourcepath.read_text()).items():
        for v in vs:meta[(s,v['sha'])]=max(pd.Timestamp(v[k]) for k in ['author_time','committer_time'])
    selection=R/'reports/calendar_dataset_2026_10_16/old_selection.json';bind(selection)
    for v in json.loads(selection.read_text()):
        if v.get('sha'):meta[(v['season'],v['sha'])]=max(pd.Timestamp(v[k]) for k in ['author_time','committer_time'])
    for (s,commit),t in meta.items():
        paths=[CTX/'raw'/f'calendar_{s}_{commit}.csv',R/f'FPL_training_dataset/research/current/calendar_audit/portable/{s}_{commit}.csv',R/f'reports/calendar_dataset_2026_10_16/raw/old_{s}_{commit}.csv']
        path=next((v for v in paths if v.exists()),None)
        if path is not None:
            f=pd.read_csv(path);assert len(f)==380 and not f.id.duplicated().any();bind(path);versions[(s,commit)]=dict(time=t,file=str(path.relative_to(R)),frame=f)
    # Source bootstrap carries the official deadline; no later actual-kickoff
    # proxy is used to reconstruct an earlier decision.
    sel=R/'datasets/fpl_availability_all_seasons_v1/selected_sources.json';bind(sel);origins={};metadata={};originrows=[]
    for v in json.loads(sel.read_text()):
        s=v['season'];g=int(v['round'])
        if v['format']!='bootstrap' or s>'2025-26':continue
        path=R/v['source_file'];bind(path)
        j=json.loads(lzma.open(path,'rt').read() if path.suffix=='.xz' else path.read_text());ev=next(e for e in j['events'] if e['id']==g);at=pd.Timestamp(ev['deadline_time']);receipt=pd.Timestamp(v['source_time']);assert receipt<at
        teams={int(t['id']):int(t['code']) for t in j['teams']};m=pd.DataFrame([dict(code=int(e['code']),pos=int(e['element_type']),club=teams[e['team']],last_price=float(e['now_cost'])/10) for e in j['elements']]);assert not m.code.duplicated().any()
        origins[(s,g)]=at;metadata[(s,g)]=m
        originrows.append(dict(season=s,round=g,forecast_at=str(at),deadline_source=v['source_file'],source_time=str(receipt)))
    raw=pd.read_pickle(D/'training.pkl');bind(D/'training.pkl');bind(D/'schema.json');schema=common.read(D/'schema.json');cols=schema['features']
    old=R/'reports/common_season_comparison_2026_10_25/pool_features.pkl';new=R/'reports/component_confirmation_2026_10_25_v2/pool_features.pkl'
    bind(old);bind(new);views=pd.concat([pd.read_pickle(old),pd.read_pickle(new)],ignore_index=True);assert not views.duplicated(KEY).any()
    for (s,g),q in views.groupby(['season','round']):
        if (s,g)==('2022-23',7):continue
        assert (s,g) in origins and q.forecast_at.eq(origins[(s,g)]).all()
        p=pool(s,g)
        for c in ['price_available_at','position_available_at','club_available_at']:assert pd.to_datetime(p[c],utc=True).lt(origins[(s,g)]).all()
        for n in ['pool.csv.gz','manifest.json']:bind(cache(s)/s/f'gw{g:02d}'/n)
    maps={}
    for s in sorted({k[0] for k in origins}):
        path=R/f'FPL_training_dataset/research/current/project/data/{s}_teams.csv.gz';bind(path);t=pd.read_csv(path);maps[s]=dict(zip(t.id,t.code))
    calendars={};calrows=[];reconciliations=[]
    observedpath=R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz';bind(observedpath)
    observed=pd.read_csv(observedpath,usecols=['season','fixture','fixture_event','fixture_kickoff_time','kickoff_time']).drop_duplicates(['season','fixture']);observed['observed_available']=pd.to_datetime(observed.fixture_kickoff_time.fillna(observed.kickoff_time),utc=True)+pd.Timedelta(hours=24)
    for (s,g),at in sorted(origins.items()):
        vs=[(key,z) for key,z in versions.items() if key[0]==s and z['time']<at]
        if not vs:continue
        key,z=max(vs,key=lambda x:x[1]['time']);f=z['frame'][['id','event','team_h','team_a','kickoff_time']].copy();f['home']=f.team_h.map(maps[s]);f['away']=f.team_a.map(maps[s]);assert f[['home','away']].notna().all().all()
        past=observed[observed.season.eq(s)&observed.observed_available.lt(at)].set_index('fixture')
        for ix,v in f.iterrows():
            if v.id not in past.index:continue
            r=past.loc[v.id];ko=r.fixture_kickoff_time if pd.notna(r.fixture_kickoff_time) else r.kickoff_time
            if pd.isna(v.event) or v.event!=r.fixture_event or pd.to_datetime(v.kickoff_time,utc=True,errors='coerce')!=pd.Timestamp(ko):
                reconciliations.append(dict(season=s,round=g,fixture=int(v.id),source_available=str(r.observed_available),forecast_at=str(at),old_event=None if pd.isna(v.event) else int(v.event),observed_event=int(r.fixture_event),old_kickoff=v.kickoff_time,observed_kickoff=ko))
            f.at[ix,'event']=r.fixture_event;f.at[ix,'kickoff_time']=ko
        calendars[(s,g)]=dict(frame=f,source_time=z['time'],source_sha=key[1],file=z['file'],age=(at-z['time']).total_seconds()/86400)
        calrows.append(dict(season=s,round=g,forecast_at=str(at),source_time=str(z['time']),source_sha=key[1],file=z['file'],age_days=calendars[(s,g)]['age'],fixtures=len(f),unassigned=int(f.event.isna().sum())))
    assert all((s,g) in calendars for s in SEASONS for g in range(1,39) if (s,g) in origins)
    # Generate the same as-of strength map once for every season/origin.
    role=inputs.isolated_module('_matched_strength',R/'datasets/fpl_role_strength_v1/build.py',('common',));gamepath=R/'datasets/fpl_role_strength_v1/fixture_strength_audit.csv';bind(gamepath)
    games=pd.read_csv(gamepath);strength={}
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
    cup=[c for c in cols if c.startswith('cal_announced_cup_')]
    def context(s,g,club):
        at=origins[(s,g)];ca=calendars.get((s,g));states=strength[(s,g)];own=states.get(int(club)) if pd.notna(club) else None
        x={c:np.nan for c in schema['feature_groups']['calendar']+schema['feature_groups']['strength']};f=None if ca is None else ca['frame'];ownfs=f[(f.home.eq(club)|f.away.eq(club))] if f is not None else pd.DataFrame();bound=len(ownfs)==38 and ownfs.event.notna().all();x['cal_PL_round_bindings_complete']=float(bound)
        if own:
            x.update({'ds_own_'+k:float(v) if v is not None else np.nan for k,v in own.items() if 'ds_own_'+k in x});x.update(u_own_attack=own['attack_index'],u_own_concession=own['concession_index'])
        else:x.update(u_own_attack=np.nan,u_own_concession=np.nan)
        for h in [1,3,6]:
            fs=ownfs[ownfs.event.between(g,min(38,g+h-1))] if bound else pd.DataFrame();n=[int(ownfs.event.eq(r).sum()) for r in range(g,min(39,g+h))] if bound else []
            x[f'cal_PL_fixtures_next_{h}_rounds']=len(fs) if bound else np.nan;x[f'cal_PL_blank_rounds_next_{h}']=sum(v==0 for v in n) if bound else np.nan;x[f'cal_PL_double_rounds_next_{h}']=sum(v>1 for v in n) if bound else np.nan
            if h in [1,3]:
                ops=[states[int(v.away if v.home==club else v.home)] for v in fs.itertuples()];x[f'ds_known_matches_h{h}']=len(fs) if bound else np.nan
                for k in ['attack_index','concession_index']:x[f'ds_opponent_{k}_h{h}']=np.mean([v[k] for v in ops]) if ops else np.nan
        upcoming=ownfs[pd.to_datetime(ownfs.kickoff_time,utc=True,errors='coerce').ge(at)] if len(ownfs) else ownfs
        times=pd.to_datetime(upcoming.kickoff_time,utc=True,errors='coerce') if len(upcoming) else pd.Series([],dtype='datetime64[ns, UTC]')
        x['cal_hours_until_next_known_club_fixture']=(times.min()-at).total_seconds()/3600 if len(times) else np.nan
        for days in [7,14,28]:x[f'cal_PL_registered_fixtures_next_{days}d']=int(times.lt(at+pd.Timedelta(days=days)).sum()) if len(ownfs) else np.nan
        for j in range(8):
            fs=ownfs[ownfs.event.eq(g+j)] if bound else pd.DataFrame();ops=[states[int(v.away if v.home==club else v.home)] for v in fs.itertuples()]
            x[f'u_count_{j}']=len(fs) if bound else np.nan;x[f'u_home_{j}']=float(fs.home.eq(club).mean()) if len(fs) else np.nan
            for kind in ['attack','concession']:x[f'u_opp_{kind}_{j}']=np.mean([v[kind+'_index'] for v in ops]) if ops else np.nan
        x['u_count3']=sum(x[f'u_count_{j}'] for j in range(min(3,39-g))) if bound else np.nan
        return x
    contexts={};meta_index={k:m.set_index('code') for k,m in metadata.items()}
    def patch(d,full):
        out=[]
        for (s,g),q in d.groupby(['season','round'],sort=False):
            key=(s,int(g))
            if key not in origins:continue
            at=origins[key]
            if not full:q=q[q.forecast_at.eq(at)&~q.excluded_origin].copy()
            if q.empty:continue
            if full:
                pp=pool(s,g).set_index('code');names=native.BenchmarkForecaster.__new__(native.BenchmarkForecaster)
                teamnames=pd.read_csv(R/f'FPL_training_dataset/research/current/project/data/{s}_teams.csv.gz');nm=dict(zip(teamnames.name,teamnames.code));nm['Ipswich Town']=nm.get('Ipswich');clubs=q.code.map(pp.club).map(nm)
            else:clubs=q.code.map(meta_index[key].club)
            patches=[]
            for c in clubs:
                ck=(*key,int(c)) if pd.notna(c) else (*key,None)
                if ck not in contexts:contexts[ck]=context(s,g,c)
                patches.append(contexts[ck])
            z=pd.DataFrame(patches,index=q.index)
            for c in z:q[c]=z[c]
            # Unversioned future cup web pages cannot enter the strict main arm.
            for c in cup:q[c]=np.nan
            if not full:q=q[clubs.notna()]
            out.append(q)
        return pd.concat(out,ignore_index=True)
    train=patch(raw[raw.season.between('2020-21','2025-26')],False);view=patch(views,True)
    assert view[view.season.isin(EVAL)].groupby('season')['round'].nunique().eq(38).all();assert not train.duplicated(KEY).any()
    dump('training.pkl',train);dump('pool_features.pkl',view);dump('calendars.pkl',calendars);dump('origins.pkl',origins);dump('metadata.pkl',metadata)
    pd.DataFrame(originrows).to_csv(P/'origins.csv',index=False);pd.DataFrame(calrows).to_csv(P/'calendar.csv',index=False)
    pd.DataFrame(reconciliations).to_csv(P/'observed_calendar_reconciliations.csv',index=False)
    coverage=[]
    for s,q in view.groupby('season'):
        for group,fs in schema['feature_groups'].items():
            for c in fs:coverage.append(dict(season=s,group=group,feature=c,known_share=float(q[c].notna().mean())))
    pd.DataFrame(coverage).to_csv(P/'feature_coverage.csv',index=False)
    stats=[]
    for s,q in view.groupby('season'):stats.append(dict(season=s,rows=len(q),rounds=q['round'].nunique(),calendar_h1_known=float(q.u_count_0.notna().mean()),calendar_h3_known=float(q.u_count3.notna().mean()),strict_calendar_snapshots=len([k for k in calendars if k[0]==s]),training_rows=int(train.season.eq(s).sum())))
    pd.DataFrame(stats).to_csv(P/'comparability.csv',index=False)
    for p in [Path(__file__),R/'scripts/common_model_retest.py',R/'scripts/common_season_comparison.py',R/'model_lab/fixed_season_forecaster.py',R/'reports/fpl_simulator_2026_10_13/benchmark_forecaster.py',R/'overview/ACTIVE_TEAM_BENCHMARK.json',R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',R/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz']:bind(p)
    extra=[R/'datasets/fpl_role_strength_v1'/n for n in ['build.py','common.py','contract.json']]+[fixed.RECIPE/n for n in ['season_gate.py','experiment.py','proposal.json']]+list((R/'model_lab/vendor/fpl_rules_v1').glob('*.py'))+list((R/'FPL_training_dataset/research/current/project/data').glob('*_gw.csv.gz'))+[R/'reports/fpl_simulator_2026_10_13/benchmark_audit.json',R/'model_lab/manager_learning.py',R/'model_lab/simulation.py',PREVIOUS/'proposal.json',PREVIOUS/'inputs.json',R/'scripts/matched_season_retest.py']
    for p in extra:bind(p)
    atomic_json(P/'inputs.json',dict(input_hashes=deps,files={n:sha(P/n) for n in ['training.pkl','pool_features.pkl','calendars.pkl','origins.pkl','metadata.pkl','origins.csv','calendar.csv','observed_calendar_reconciliations.csv','feature_coverage.csv','comparability.csv']}))
    atomic_json(P/'proposal.json',dict(id='matched-season-retest-20261025-v3',registered_before_new_fits=True,technical_v3='Input-quality repair before any head fits or manager outcomes: reconcile only already completed fixtures using the same +24h source-availability clock in every season. V2 base fits can be reused only when their entire training matrices/targets are identical; changed component folds refit, all forecasts regenerated. Native training-context identity independently asserted.',seasons=EVAL,arms=ARMS,calendar='latest physically archived git version with author AND committer < verified official deadline; reconcile completed fixture event/kickoff only if observed_available<deadline; carry regardless age; unassigned club calendar unknown, never zero; no backdated web amendments',teacher='same eligible OOF player/origin keys and completed H3 and target offset strictly before fit; teacher begins2022; both heads refit1,5,...37',base='fresh component H1/H3 same frozen150 depth5 parameters and325 columns; native reference architectures unchanged, new as-of match-context training; same four-round refits',calibration='component independent offset residual Ridge.01; operational fixed seasonal weighting and positional Ridge.01; same teachers, not same architecture',native_gate='prior2021 cached gate retained only for2022 teacher; later gates freshly fitted on new prior-season OOF a/b forecasts',simulation='6 full seasons; unchanged adaptive manager, common8chip/5FT rules, empty£100m1FT,8forecast/3planning; native request15 actual cap16,40calls; no outcome-driven retry',scope='historical development comparison, not untouched prospective evidence; source publication/available+24h proxies do not establish statistical vintage proof',active_model_unchanged=True,resources=dict(component_fits=80,native_refit_bundles=40,native_frozen_bundles=4,projection_heads=240,reference_positional_heads=960,season_attempts=6,workers=4),input_manifest_sha256=sha(P/'inputs.json')))
    status('inputs_ready');print(pd.DataFrame(stats).to_string(index=False),flush=True)

def check_inputs():
    m=common.read(P/'inputs.json');verify_files(R,m['input_hashes']);verify_files(P,m['files'])

def component_worker(s):
    check_inputs();d=load('training.pkl');view=load('pool_features.pkl');cols=common.read(D/'schema.json')['features'];out=view[view.season.eq(s)][KEY+['forecast_at']].copy();audit=[];old=pd.read_pickle(PREVIOUS/'training.pkl');assert sha(PREVIOUS/'training.pkl')==common.read(PREVIOUS/'inputs.json')['files']['training.pkl'];old_audit=pd.read_csv(PREVIOUS/f'component_audit_{s}.csv')
    original=common.cbreg
    def cb():
        m=original();m.set_params(allow_const_label=True);return m
    common.cbreg=cb
    for g in REFITS:
        at=view[view.season.eq(s)&view['round'].eq(g)].forecast_at.iloc[0];q=view[view.season.eq(s)&view['round'].between(g,min(g+3,38))]
        for h in [1,3]:
            ts=[f'target_{t}_{h}' for t in ['points','minutes','starts','attack','appearance','residual']];tr=d[d.train_eligible&d.forecast_at.lt(at)&d[f'label_at_{h}'].lt(at)&d[ts].notna().all(axis=1)].copy();assert len(tr)>1000
            oldtr=old[old.train_eligible&old.forecast_at.lt(at)&old[f'label_at_{h}'].lt(at)&old[ts].notna().all(axis=1)];compare=KEY+['forecast_at',f'label_at_{h}']+cols+ts;reuse=tr[compare].reset_index(drop=True).equals(oldtr[compare].reset_index(drop=True));name=f'models/component_{s}_gw{g:02d}_h{h}.pkl';(P/'models').mkdir(exist_ok=True)
            if reuse:
                aa=old_audit[old_audit['round'].eq(g)&old_audit.horizon.eq(h)].iloc[0];assert sha(PREVIOUS/name)==aa.sha256
                with (PREVIOUS/name).open('rb') as f:b=pickle.load(f)
                shutil.copy2(PREVIOUS/name,P/name)
            else:b=common.fit_arm('component',tr,cols,h);dump(name,b)
            v,_,_=common.predict_arm(b,q);out.loc[q.index,f'component_p{h}']=v[:,0];out.loc[q.index,f'component_m{h}']=v[:,1]
            audit.append(dict(season=s,round=g,horizon=h,cutoff=str(at),rows=len(tr),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'label_at_{h}'].max()),keys_sha256=common.keys_hash(tr),file=name,sha256=sha(P/name),reused_v2=bool(reuse),identical_training_matrices=bool(reuse)))
        print('COMPONENT',s,g,len(tr),flush=True)
    assert np.isfinite(out.filter(regex='component_')).all().all();out.to_pickle(P/f'component_{s}.pkl');pd.DataFrame(audit).to_csv(P/f'component_audit_{s}.csv',index=False)

class MatchedNative(native.BenchmarkForecaster):
    def load_gate_cache(self):pass
    def initialize(self):
        self.calendars=load('calendars.pkl');self.origins=load('origins.pkl');self.metadata=load('metadata.pkl')
        self.periods=pd.DataFrame([dict(season=s,event=g,cutoff=t) for (s,g),t in self.origins.items()]);parts=[];audit=[]
        # Keep historical windows only if their original query was already at
        # the verified deadline. Replace target-match metadata and matchup
        # context by the version actually known at that historical deadline.
        for (s,g),q in self.train.groupby(['season','event']):
            key=(s,int(g))
            if key not in self.origins:continue
            at=self.origins[key];q=q[q.cutoff.eq(at)].copy()
            if q.empty:continue
            md=self.metadata[key].set_index('code');q=q[q.pid.isin(md.index)].copy()
            for c in ['pos','club','last_price']:q[c]=q.pid.map(md[c])
            team=self.teams[self.teams.time.lt(at)].drop_duplicates('club',keep='last').set_index('club');ca=self.calendars.get(key);f=ca['frame'].set_index('id') if ca else None
            for c,default in [('elo',1500.),('gf',1.35),('ga',1.35)]:q['team_'+c]=q.club.map(team[c]).fillna(default);q['opp_'+c]=default
            q['home']=.5;q['opponent']=np.nan;known=0
            if f is not None:
                for ix,r in q.iterrows():
                    if r.fixture not in f.index:continue
                    v=f.loc[r.fixture]
                    if v.event!=g or r.club not in [v.home,v.away]:continue
                    opp=v.away if r.club==v.home else v.home;q.at[ix,'home']=float(r.club==v.home);q.at[ix,'opponent']=opp;known+=1
                    for c,default in [('elo',1500.),('gf',1.35),('ga',1.35)]:q.at[ix,'opp_'+c]=team.loc[opp,c] if opp in team.index else default
            q['elo_diff']=q.team_elo-q.opp_elo;parts.append(native.design(q));audit.append(dict(season=s,round=g,rows=len(q),known_match_context=known,cutoff=str(at)))
        self.train=pd.concat(parts,ignore_index=True);self.context_audit=audit
        # Reconciliation uses completed fixtures only. Demonstrate that no
        # supervised matchup feature changes before reusing a native model.
        previous=pd.read_pickle(PREVIOUS/'calendars.pkl');assert sha(PREVIOUS/'calendars.pkl')==common.read(PREVIOUS/'inputs.json')['files']['calendars.pkl']
        def matchup(f,fixture,club,g):
            a=f[f.id.eq(fixture)]
            if a.empty:return None
            v=a.iloc[0]
            return (float(v.home==club),float(v.away if v.home==club else v.home)) if v.event==g and club in [v.home,v.away] else None
        for (s,g),q in self.train.groupby(['season','event']):
            key=(s,int(g))
            if key not in previous or key not in self.calendars:continue
            oldf=previous[key]['frame'];newf=self.calendars[key]['frame']
            for v in q[['fixture','club']].drop_duplicates().itertuples():assert matchup(oldf,v.fixture,v.club,g)==matchup(newf,v.fixture,v.club,g)
        self.native_training_identity_verified=True
    def _fit(self,season,gw,frozen=False):
        assert self.native_training_identity_verified
        refresh=1 if frozen or gw<5 else 5+4*((gw-5)//4);key=(season,refresh,frozen)
        if key in self.models:return self.models[key]
        name=PREVIOUS/f'models/native_{season}_gw{refresh:02d}.pkl'
        with name.open('rb') as f:old=pickle.load(f)
        a=next(v for v in old['fit_audits'] if v['season']==season and v['refresh_gw']==refresh and v['frozen']==frozen);at=self.origins[(season,refresh)];tr=self.train[self.train.available.lt(at)&self.train.cutoff.lt(at)&self.train.target.notna()];tr=tr[tr.season.lt(season)] if frozen or refresh==1 else tr[tr.season.le(season)]
        assert len(tr)==a['rows'] and hashlib.sha256(pd.util.hash_pandas_object(tr[['season','fixture','pid']],index=False).values.tobytes()).hexdigest()==a['training_keys_sha256']
        assert pd.Timestamp(a['forecast_at'])==at and tr.available.max()<at and tr.cutoff.max()<at
        self.models[key]=old['models'][key];self.fit_audits.append(dict(a,reused_v2=True,training_context_identical=True,source_model_sha256=sha(name)))
        if frozen:self.coefficients[season]=old['coefficients'][season]
        return self.models[key]
    def _calendar(self,season,at):
        keys=[k for k,t in self.origins.items() if k[0]==season and t==at];assert len(keys)==1;ca=self.calendars.get(keys[0])
        if ca is None:return None,dict(calendar_status='missing',calendar_age_days=None)
        return ca['frame'],dict(calendar_status='carry_predeadline_git',calendar_age_days=ca['age'],calendar_time=str(ca['source_time']),calendar_sha=ca['source_sha'])
    def components(self,snapshot):
        s=snapshot['season'];g=snapshot['round'];at=pd.Timestamp(snapshot['forecast_at']);p,team=self._players(snapshot);f,audit=self._calendar(s,at);refreshed=self._fit(s,g);frozen=self._fit(s,g,True)
        neutral=p.copy();league=team.reindex(sorted(p.club.unique()));neutral['home']=.5;neutral['elo_diff']=neutral.team_elo-league.elo.fillna(1500).mean();neutral['opp_ga']=league.ga.fillna(1.35).mean();neutral['opp_gf']=league.gf.fillna(1.35).mean();neutral=native.design(neutral)
        def pred(m,x,n):return np.maximum(0,m[n].predict(x[native.RICH if n=='rich' else native.COLS]))
        nr=.5*pred(frozen,neutral,'ridge')+.5*pred(frozen,neutral,'extra');bound={}
        for club in p.club.unique():
            fs=f[f.home.eq(club)|f.away.eq(club)] if f is not None else pd.DataFrame();bound[club]=len(fs)==38 and fs.event.notna().all()
        known=p.club.map(bound).to_numpy(bool);cur={n:np.where(known,0.,pred(refreshed,neutral,n)) for n in ['ridge','extra','rich']};cur['reference']=np.where(known,0.,nr);count=np.where(known,0.,1.);effect=np.zeros(len(p));future={}
        for j in range(8):
            counts=np.where(known,0.,np.nan);effects=np.zeros(len(p));individual=[[] for _ in range(len(p))]
            for v in f[f.event.eq(g+j)].itertuples() if f is not None else []:
                for club,opp,home in [(v.home,v.away,1),(v.away,v.home,0)]:
                    mask=p.club.eq(club).to_numpy()&known
                    if not mask.any():continue
                    ef=self._effect(p,team,opp,home,s);counts[mask]+=1;effects[mask]+=ef[mask]
                    for k in np.flatnonzero(mask):individual[k].append(float(ef[k]))
                    if j==0:
                        x=p[mask].copy();x['home']=home;x['elo_diff']=x.team_elo-(team.loc[opp,'elo'] if opp in team.index else 1500.)
                        for c in ['gf','ga']:x['opp_'+c]=team.loc[opp,c] if opp in team.index else 1.35
                        x=native.design(x)
                        for n in ['ridge','extra','rich']:cur[n][mask]+=pred(refreshed,x,n)
                        cur['reference'][mask]+=.5*pred(frozen,x,'ridge')+.5*pred(frozen,x,'extra')
            future[j]=(counts,effects,individual)
            if j==0:count=np.where(known,counts,1.);effect=effects/np.maximum(count,1)
        frame=p[['code']].copy();frame['a']=.5*cur['ridge']+.5*cur['extra'];frame['b']=cur['rich'];frame['reference']=cur['reference'];frame['neutral_reference']=nr;frame['count']=count;frame['current_effect']=effect
        for j,(co,ef,individual) in future.items():
            frame[f'count_{j}']=co;frame[f'effect_{j}']=ef;frame[f'individual_effects_{j}']=individual
        audit.update(max_native=str(self.history[self.history.available.lt(at)].available.max()),max_team=str(self.teams[self.teams.time.lt(at)].time.max()))
        return frame,audit

def native_worker(s):
    check_inputs();b=MatchedNative(R);b.initialize();view=load('pool_features.pkl');parts=[];audits=[]
    for g in range(1,39):
        q=view[view.season.eq(s)&view['round'].eq(g)]
        if q.empty:continue
        at=q.forecast_at.iloc[0];pp=method.qualify(pool(s,g),s,at);f,a=b.components(dict(season=s,round=g,forecast_at=at,players=pp));assert pd.Timestamp(a['max_native'])<at and pd.Timestamp(a['max_team'])<at
        f['season']=s;f['round']=g;f['forecast_at']=at;parts.append(f);audits.append(dict(season=s,round=g,**a))
        if g in REFITS:
            name=f'models/native_{s}_gw{g:02d}.pkl';(P/'models').mkdir(exist_ok=True);dump(name,dict(models=b.models,coefficients=b.coefficients,fit_audits=b.fit_audits));print('NATIVE',s,g,flush=True)
    pd.concat(parts,ignore_index=True).to_pickle(P/f'native_{s}.pkl');pd.DataFrame(audits).to_csv(P/f'native_audit_{s}.csv',index=False);atomic_json(P/f'native_fits_{s}.json',dict(fits=b.fit_audits,training_context=b.context_audit))

def train():
    check_inputs();status('training');jobs=[(typ,s) for typ in ['component','native'] for s in SEASONS]
    def job(args):
        typ,s=args;path=P/'logs'/f'{typ}_{s}.log';path.parent.mkdir(exist_ok=True)
        with path.open('x') as f:r=subprocess.run([sys.executable,str(Path(__file__).resolve()),typ+'_worker',s],cwd=R,env=os.environ.copy(),stdout=f,stderr=subprocess.STDOUT)
        print('TRAIN ATTEMPT',typ,s,r.returncode,flush=True);return dict(kind=typ,season=s,exit_code=r.returncode)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(job,jobs))
    atomic_json(P/'training_attempts.json',rows);assert all(v['exit_code']==0 for v in rows);status('base_models_ready')

def heads():
    check_inputs();status('calibrating');d=load('pool_features.pkl');comp=pd.concat([load(f'component_{s}.pkl') for s in SEASONS],ignore_index=True);n=pd.concat([load(f'native_{s}.pkl') for s in SEASONS],ignore_index=True);d=d.merge(comp,on=KEY+['forecast_at'],validate='one_to_one').merge(n,on=KEY+['forecast_at'],validate='one_to_one');gates=[]
    for s in SEASONS:
        at=d[d.season.eq(s)&d['round'].eq(1)].forecast_at.iloc[0]
        if s==SEASONS[0]:w=float(common.read(R/'reports/fpl_simulator_2026_10_13/benchmark_audit.json')['gate_calibrations'][s]['weight_rich']);rows=0
        else:
            tr=d[d.season.lt(s)&d['round'].ge(5)&d.y_0.notna()&d.y_at_0.lt(at)&d['count'].gt(0)].copy();tr['actual']=tr.y_0;w,_=native.fit_constant_gate(tr);rows=len(tr)
        gates.append(dict(season=s,cutoff=str(at),weight_rich=w,prior_teacher_rows=rows));ix=d.season.eq(s);q=d[ix];current=q.a.to_numpy()+w*(q.b-q.a).to_numpy();count=q['count'].to_numpy();neutral=np.maximum(0,q.neutral_reference.to_numpy()+np.where(count>0,(current-q.reference.to_numpy())/np.maximum(count,1),0));per=np.where(count>0,current/np.maximum(count,1),neutral)
        for j in range(8):
            pred=current.copy() if j==0 else np.maximum(0,neutral+(per-neutral)*.5**j);fc=q[f'count_{j}'].to_numpy();known=np.isfinite(fc)
            if j:
                base=neutral+(per-neutral)*.5**j-q.current_effect.to_numpy()*.5**j
                for k in np.flatnonzero(known):pred[k]=sum(max(0.,base[k]+e) for e in q[f'individual_effects_{j}'].iloc[k])
            d.loc[ix,f'xp_{j}']=pred
    atomic_json(P/'native_gates.json',gates)
    history=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=['season','fixture','code','native_minutes','native_goals_scored','native_assists','native_clean_sheets','native_saves','target_total_points','kickoff_time']);history['available']=pd.to_datetime(history.kickoff_time,utc=True)+pd.Timedelta(hours=24);history=history.rename(columns=dict(native_minutes='minutes',native_goals_scored='goals',native_assists='assists',native_clean_sheets='clean',native_saves='saves',target_total_points='points'));history['played']=history.minutes.gt(0).astype(float);history['sixty']=history.minutes.ge(60).astype(float)
    # Same teacher view is passed to both head families. No frozen2025 archive.
    gate,recipe=fixed.recipe();rf=fixed.make_features(d[KEY+['forecast_at','position','price_tenths','can_buy']+[f'xp_{j}' for j in range(8)]],history);assert (rf.latest_feature_available.isna()|rf.latest_feature_available.lt(rf.forecast_at)).all();rf=rf.set_index(KEY);audit=[];outputs={a:[] for a in ARMS};complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=d[[f'y_at_{j}' for j in range(3)]].max(axis=1)
    for s in EVAL:
        for g in range(1,39):
            q=d[d.season.eq(s)&d['round'].eq(g)];at=q.forecast_at.iloc[0]
            if g in REFITS:
                models={}
                for j in range(8):
                    tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&h3.lt(at)].copy();assert len(tr)>1000;m=method.fit_projection(tr,'component',j);models[('component',j)]=m;name=f'heads/component_{s}_gw{g:02d}_j{j}.json';atomic_json(P/name,m)
                    ix=pd.MultiIndex.from_frame(tr[KEY]);trf=rf.reindex(ix).reset_index();assert trf[KEY].equals(tr[KEY].reset_index(drop=True));trf['target_total_points']=tr[f'y_{j}'].to_numpy();trf['xp_0']=trf[f'xp_{j}'];mm={}
                    for pos in ['GK','DEF','MID','FWD']:
                        tp=trf[trf.position.eq(pos)];assert len(tp)>=100;mm[pos]=gate.fit(tp,learned=False)
                    models[('operational_matched',j)]=mm;atomic_json(P/f'heads/operational_matched_{s}_gw{g:02d}_j{j}.json',mm);audit.append(dict(season=s,round=g,offset=j,cutoff=str(at),rows=len(tr),current_season_rows=int(tr.season.eq(s).sum()),keys_sha256=common.keys_hash(tr),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'y_at_{j}'].max()),max_h3_label=str(h3.loc[tr.index].max()),identical_teacher_keys=True))
                print('MATCHED HEADS',s,g,flush=True)
            for arm in ARMS:
                out=q[KEY+['forecast_at','can_buy']].copy()
                for j in range(8):
                    if g+j>38:out[f'xp_{j}']=0.;continue
                    if arm=='component':out[f'xp_{j}']=method.predict_projection(q,arm,models[(arm,j)])
                    else:
                        qf=rf.reindex(pd.MultiIndex.from_frame(q[KEY])).reset_index();qf['xp_0']=qf[f'xp_{j}'];v=np.zeros(len(qf))
                        for pos in ['GK','DEF','MID','FWD']:
                            mask=qf.position.eq(pos);v[mask]=gate.predict(qf[mask],models[(arm,j)][pos])[0]
                        # Both models honor exactly the same known blanks.
                        v[q[f'u_count_{j}'].eq(0).to_numpy()]=0.;out[f'xp_{j}']=v
                assert np.isfinite(out.filter(regex='^xp_')).all().all();outputs[arm].append(out)
    files={}
    for arm,parts in outputs.items():
        z=pd.concat(parts,ignore_index=True);z.to_csv(P/f'{arm}.csv.gz',index=False);files[f'{arm}.csv.gz']=sha(P/f'{arm}.csv.gz')
    dump('head_data.pkl',d);dump('reference_features.pkl',rf.reset_index());pd.DataFrame(audit).to_csv(P/'head_audit.csv',index=False)
    files.update({n:sha(P/n) for n in ['head_data.pkl','reference_features.pkl','head_audit.csv','native_gates.json']});atomic_json(P/'prediction_lock.json',dict(files=files,saved_before_manager=True));status('predictions_ready')

def verify_forecasts():
    check_inputs();verify_files(P,common.read(P/'prediction_lock.json')['files']);d=load('head_data.pkl');rf=load('reference_features.pkl').set_index(KEY);gate,_=fixed.recipe();origins=load('origins.pkl');complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=d[[f'y_at_{j}' for j in range(3)]].max(axis=1);count=0
    for a in pd.read_csv(P/'head_audit.csv').itertuples():
        at=pd.Timestamp(a.cutoff);j=a.offset;tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&h3.lt(at)].copy();assert len(tr)==a.rows and common.keys_hash(tr)==a.keys_sha256;assert tr.forecast_at.max()<at and tr[f'y_at_{j}'].max()<at and h3.loc[tr.index].max()<at
        m=common.read(P/f'heads/component_{a.season}_gw{a.round:02d}_j{j}.json');raw,anchor,_=method.design(tr,'component',j);x,_=method.transform(raw,m['transform']);b=np.array(m['beta']);pen=.01*b;pen[0]=0;assert np.max(np.abs(x.T@(x@b-(tr[f'y_{j}'].to_numpy()-anchor)/6)/len(x)+pen))<1e-7
        mm=common.read(P/f'heads/operational_matched_{a.season}_gw{a.round:02d}_j{j}.json');t=rf.reindex(pd.MultiIndex.from_frame(tr[KEY])).reset_index();t['xp_0']=t[f'xp_{j}'];t['target_total_points']=tr[f'y_{j}'].to_numpy()
        for pos in ['GK','DEF','MID','FWD']:
            q=t[t.position.eq(pos)];aa=gate.arrays(q);xx,_,_=gate.design(aa,np.array([0.,1.,0.]));bb=np.array(mm[pos]['beta']);pp=.01*bb;pp[0]=0;assert np.max(np.abs(xx.T@(aa['base']+xx@bb-q.target_total_points.to_numpy())/len(q)+pp))<1e-7
        count+=1
    for s in SEASONS:
        for a in pd.read_csv(P/f'component_audit_{s}.csv').itertuples():
            at=origins[(s,a.round)];assert pd.Timestamp(a.max_origin)<at and pd.Timestamp(a.max_label)<at and sha(P/a.file)==a.sha256
        for a in common.read(P/f'native_fits_{s}.json')['fits']:assert pd.Timestamp(a['max_label_available'])<pd.Timestamp(a['forecast_at']) and pd.Timestamp(a['max_training_forecast'])<pd.Timestamp(a['forecast_at'])
    for (s,g),ca in load('calendars.pkl').items():assert ca['source_time']<origins[(s,g)]
    recon=pd.read_csv(P/'observed_calendar_reconciliations.csv');assert pd.to_datetime(recon.source_available,utc=True).lt(pd.to_datetime(recon.forecast_at,utc=True)).all()
    # Both packages have exactly the same rows, origin and known-blank policy.
    a=pd.read_csv(P/'component.csv.gz');b=pd.read_csv(P/'operational_matched.csv.gz');assert a[KEY+['forecast_at','can_buy']].equals(b[KEY+['forecast_at','can_buy']]);assert count==240
    atomic_json(P/'forecast_verification.json',dict(passed=True,shared_teacher_offsets=240,component_normal_equations=240,reference_normal_equations=960,source_and_label_timestamps_checked=True,identical_prediction_keys=True,statistical_vintages_not_proven=True));status('forecasts_verified');print('VERIFIED MATCHED FORECASTS',flush=True)

class MatchedEnvironment(Environment):
    def inputs(self,s,g):return pool(s,g),None,common.read(cache(s)/s/f'gw{g:02d}/manifest.json'),None

def solver():
    mod,a=backend(16,40)
    # Native solver can overshoot a node request by one. Reserve that node
    # BEFORE every episode, with the identical hard16-node audit ceiling.
    a.options['node_limit']=15
    return mod,a

def manager(s,arm):
    check_inputs();verify_files(P,common.read(P/'prediction_lock.json')['files']);assert common.read(P/'forecast_verification.json')['passed'];f=pd.read_csv(P/f'{arm}.csv.gz');f=f[f.season.eq(s)].set_index(['round','code']);origins=load('origins.pkl');env=MatchedEnvironment();folder=P/'manager'/f'{s}_{arm}';folder.mkdir(parents=True,exist_ok=False);_,a=solver();state=a.engine.initial_state();net=hits=0
    atomic_json(folder/'started.json',dict(season=s,arm=arm,forecast_sha256=sha(P/f'{arm}.csv.gz'),node_request=15,node_cap=16,max_calls=40))
    for g in range(1,39):
        at=origins[(s,g)];p=method.qualify(pool(s,g),s,at);q=f.loc[g].reindex(p.code);assert pd.to_datetime(q.forecast_at,utc=True).eq(at).all() and q.can_buy.tolist()==p.can_buy.tolist();xp=q[[f'xp_{j}' for j in range(min(8,39-g))]].to_numpy(float);mod,a=solver();choice=copy.deepcopy(a.decide(p,xp,state,g)['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};after,choice=a.engine.apply_decision(state,choice,p.to_dict('records'),g)
        atomic_json(folder/f'gw{g:02d}.decision.json',mod.clean(dict(state_before=state,state_after=after,choice=choice,forecast_at=str(at),outcomes_read=False,solver_calls=a.ledger,forecast_input_sha256=hashlib.sha256(xp.tobytes()).hexdigest())))
        outcomes,result,n=settle(a,env,s,g,dict(choice=choice),p);atomic_json(folder/f'gw{g:02d}.settlement.json',mod.clean(dict(net=n,hits=4*choice['paid'],outcomes=outcomes,settlement=result)));net+=n;hits+=4*choice['paid'];state=after
        if g%8==0:print('MANAGER',s,arm,g,flush=True)
    atomic_json(folder/'summary.json',dict(season=s,arm=arm,net=net,hits=hits,rounds=38));print('COMPLETE',s,arm,net,flush=True)

def managers():
    status('simulating');jobs=[(s,a) for s in EVAL for a in ARMS]
    def job(args):
        s,a=args;path=P/'logs'/f'manager_{s}_{a}.log'
        with path.open('x') as f:r=subprocess.run([sys.executable,str(Path(__file__).resolve()),'manager',s,a],cwd=R,env=os.environ.copy(),stdout=f,stderr=subprocess.STDOUT)
        print('MANAGER ATTEMPT',s,a,r.returncode,flush=True);return dict(season=s,arm=a,exit_code=r.returncode)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(job,jobs))
    atomic_json(P/'manager_attempts.json',rows);status('simulations_finished')

def report():
    check_inputs();verify_files(P,common.read(P/'prediction_lock.json')['files']);env=MatchedEnvironment();mod,a=solver();origins=load('origins.pkl');rows=[];decisions=0
    for s in EVAL:
        for arm in ARMS:
            folder=P/'manager'/f'{s}_{arm}';state=a.engine.initial_state();net=hits=0;complete=(folder/'summary.json').exists();nround=38 if complete else len(list(folder.glob('gw*.settlement.json')));f=pd.read_csv(P/f'{arm}.csv.gz');f=f[f.season.eq(s)].set_index(['round','code'])
            for g in range(1,nround+1):
                dec=common.read(folder/f'gw{g:02d}.decision.json');saved=common.read(folder/f'gw{g:02d}.settlement.json');assert not dec['outcomes_read'] and mod.clean(state)==dec['state_before'];at=origins[(s,g)];p=method.qualify(pool(s,g),s,at);xp=f.loc[g].reindex(p.code)[[f'xp_{j}' for j in range(min(8,39-g))]].to_numpy(float);assert hashlib.sha256(xp.tobytes()).hexdigest()==dec['forecast_input_sha256'];choice=dec['choice'];choice['prices']={int(k):v for k,v in choice['prices'].items()};state,legal=a.engine.apply_decision(state,choice,p.to_dict('records'),g);assert mod.clean(state)==dec['state_after'];outcomes,result,n=settle(a,env,s,g,dict(choice=legal),p);assert outcomes==saved['outcomes'] and mod.clean(result)==saved['settlement'] and n==saved['net'];assert len(dec['solver_calls'])<=40 and all(v['nodes']<=16 and v['full_mip_feasible'] for v in dec['solver_calls']);net+=n;hits+=4*legal['paid'];decisions+=1
            if complete:assert common.read(folder/'summary.json')['net']==net
            rows.append(dict(season=s,arm=arm,complete=complete,rounds=nround,net=net if complete else None,hits=hits if complete else None))
    score=pd.DataFrame(rows);score.to_csv(P/'scores.csv',index=False);pairs=score.pivot(index='season',columns='arm',values='net');pairs['delta']=pairs.component-pairs.operational_matched;pairs.to_csv(P/'paired_scores.csv');atomic_json(P/'verification.json',dict(passed=True,decisions_replayed=decisions,full_seasons=int(score.complete.sum()),technical_stops=int((~score.complete).sum()),all_settlements_recomputed=True));status('complete' if score.complete.all() else 'technical_stops',full_seasons=int(score.complete.sum()))
    c=pd.read_csv(P/'comparability.csv');text=['# Felles kalender og løpende kalibrering – ny test','', 'Ny retrospektiv sammenligning for 2023/24, 2024/25 og 2025/26. Dagens aktive modell er ikke endret. Referansen bruker dagens modelloppskrift med de nye felles kalender- og oppdateringsreglene.','', '## Datagrunnlag','',c.to_markdown(index=False),'','Samme regel i alle sesongene: siste fysisk arkiverte Git-versjon med både forfatter- og lagringstid før dokumentert offisiell frist. Kalenderen videreføres uansett alder. Uavklarte kamper gir ukjent kalender, ikke blankrunde. Nettsideendringer uten arkivert historisk versjon og fremtidig cupkalender fra slike sider er utelatt.','', 'Begge modellene trener nye grunnprognoser og kalibrerer på fire-runders rytme. Kalibreringen bruker identiske spiller-/rundeobservasjoner fra 2022/23 og fremover, bare når hele målvinduet var ferdig og tilgjengelig før ny frist. Historiske kampdata bruker fortsatt den dokumenterte tilgjengelighetsregelen kampstart pluss24 timer; dette er ikke full dokumentasjon av alle tidligere statistikkversjoner.','', '## Resultater','',pairs.to_markdown(),'','Poengene er netto etter betalte bytter. Samme startbudsjett, spillerutvalg, priser, manager, spilleregler og chiptilgang. Alle tilgjengelige beslutninger er kontrollert og poengsummene beregnet på nytt. Ufullførte forsøk får ingen sesongsum.','', 'Dette er en utviklingstest på sesonger vi allerede har undersøkt, ikke en urørt fremtidstest. Ulikheter i faktisk spillerprestasjon eller arkivets alder er ikke gjort kunstig like. Dekning per variabel ligger i feature_coverage.csv; kalenderens kilde og alder per frist ligger i calendar.csv.']
    (P/'RESULTATER.md').write_text('\n'.join(text)+'\n');atomic_json(P/'evidence_manifest.json',dict(files={str(p.relative_to(P)):sha(p) for p in P.rglob('*') if p.is_file() and p.name not in ['evidence_manifest.json']},active_model_unchanged=True));print(pairs.to_string(),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
