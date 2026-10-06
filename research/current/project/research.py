"""Reproducible exploratory FPL benchmark. See REPORT.html for limitations.
Run with OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python research.py.
No earlier-than-2019/20 observations; no unshifted xP or final-season player stats.
"""
from pathlib import Path
import json, time, warnings, gzip
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, ElasticNet, BayesianRidge, PoissonRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier, ExtraTreesRegressor, RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scoring import portable_core, defensive_points, self_test

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
SEASONS=[f'{y}-{str(y+1)[-2:]}' for y in range(2019,2026)]
STATS=['historic','core','minutes','goals_scored','assists','clean_sheets','saves',
       'bonus','bps','threat','creativity','influence','yellow_cards','goals_conceded',
       'expected_goals','expected_assists','played','long_play']
warnings.filterwarnings('ignore',category=FutureWarning)

def load_data():
    blocks=[]; fixtures=[]; audit=[]
    for s in SEASONS:
        d=pd.read_csv(ROOT/f'data/{s}_gw.csv')
        p=pd.read_csv(ROOT/f'data/{s}_players.csv').set_index('id')
        f=pd.read_csv(ROOT/f'data/{s}_fixtures.csv').set_index('id')
        t=pd.read_csv(ROOT/f'data/{s}_teams.csv').set_index('id')
        before=len(d)
        # Prefer canonical final event assignment, essential for 2019 COVID restart.
        d['event']=d.fixture.map(f.event)
        d['canonical']=(d.GW==d.event)
        d=d.sort_values('canonical').drop_duplicates(['element','fixture'],keep='last')
        d['pos']=d.element.map(p.element_type)
        d=d[d.pos.isin([1,2,3,4])].copy()
        d['pid']=d.element.map(p.code)
        assert d.pid.notna().all()
        d['season']=s
        d['kickoff']=pd.to_datetime(d.kickoff_time,utc=True)
        d['available']=d.kickoff+pd.Timedelta(hours=3)
        # Only metadata from players_raw: invariant player code and in-season position.
        d['team_id']=np.where(d.was_home,d.fixture.map(f.team_h),d.fixture.map(f.team_a))
        d['club']=d.team_id.map(t.code)
        d['opponent']=d.opponent_team.map(t.code)
        d['historic']=d.total_points
        d['core']=portable_core(d)
        d['played']=(d.minutes>0).astype(float)
        d['long_play']=(d.minutes>=60).astype(float)
        d['price']=pd.to_numeric(d.value,errors='coerce')/10
        # Freeze every fixture in same event at same conservative pre-GW cutoff.
        cuts=pd.to_datetime(f.kickoff_time,utc=True).groupby(f.event).min()-pd.Timedelta(hours=36)
        d['cutoff']=d.event.map(cuts)
        for c in STATS:
            if c not in d: d[c]=np.nan
            d[c]=pd.to_numeric(d[c],errors='coerce')
        d=d[d.kickoff.notna() & d.cutoff.notna()].copy()
        audit.append({'season':s,'raw_rows':before,'usable_rows':len(d),'duplicates':before-len(pd.read_csv(ROOT/f'data/{s}_gw.csv').drop_duplicates(['element','fixture'])),
                      'fixtures':d.fixture.nunique(),'events':d.event.nunique(),'xg_available':bool(d.expected_goals.notna().any()),
                      'dc_available':'defensive_contribution' in d,
                      'core_mean':d.core.mean(),'historic_mean':d.historic.mean()})
        if s=='2025-26':
            dc=defensive_points(d)
            diff=d.historic-(d.core+3*d.assists+d.bonus+dc)
            pd.DataFrame({'difference':diff}).value_counts().to_csv(OUT/'scoring_reconciliation_2025.csv')
        blocks.append(d)
        ff=f.reset_index();ff['season']=s
        ff['home']=ff.team_h.map(t.code);ff['away']=ff.team_a.map(t.code)
        ff['available']=pd.to_datetime(ff.kickoff_time,utc=True)+pd.Timedelta(hours=3)
        fixtures.append(ff)
    pd.DataFrame(audit).to_csv(OUT/'data_audit.csv',index=False)
    return pd.concat(blocks,ignore_index=True),pd.concat(fixtures,ignore_index=True)

def features(d,fixtures):
    # Histories contain every appearance/non-appearance row, never the target GW.
    parts=[]
    for pid,g in d.sort_values('available').groupby('pid',sort=False):
        q=g[STATS+['price']].copy(); z=pd.DataFrame(index=g.index)
        for w in [3,6,12,38]:
            r=q.rolling(w,min_periods=1).mean();r.columns=[f'{c}_m{w}' for c in r]
            z=pd.concat([z,r],axis=1)
        for span in [5,15]:
            r=q[['historic','core','minutes']].ewm(span=span,adjust=False).mean();r.columns=[f'{c}_e{span}' for c in r]
            z=pd.concat([z,r],axis=1)
        for c in ['historic','core','minutes']:
            z[f'{c}_sum']=q[c].cumsum()
        z['n_history']=np.arange(1,len(g)+1)
        z['pid']=pid;z['history_time']=g.available
        z['last_price']=g.price
        parts.append(z)
    hist=pd.concat(parts).sort_values('history_time')
    left=d.sort_values('cutoff').copy()
    merged=pd.merge_asof(left,hist,left_on='cutoff',right_on='history_time',by='pid',allow_exact_matches=False)
    assert (merged.history_time.dropna()<merged.loc[merged.history_time.notna(),'cutoff']).all()
    # Dynamic team ratings; no final-table or final team-strength fields are read.
    teams={}; history=[]
    for r in fixtures.sort_values('available').itertuples():
        if pd.isna(r.team_h_score) or pd.isna(r.team_a_score):continue
        for k in [r.home,r.away]:
            if k not in teams: teams[k]={'elo':1500.,'gf':1.35,'ga':1.35}
        h,a=teams[r.home],teams[r.away]
        prob=1/(1+10**((a['elo']-h['elo']-60)/400))
        actual=float(r.team_h_score>r.team_a_score)+.5*float(r.team_h_score==r.team_a_score)
        delta=20*(actual-prob)
        h['elo']+=delta;a['elo']-=delta
        for k,gf,ga in [(r.home,r.team_h_score,r.team_a_score),(r.away,r.team_a_score,r.team_h_score)]:
            z=teams[k];z['gf']=.85*z['gf']+.15*gf;z['ga']=.85*z['ga']+.15*ga
            history.append({'club_key':k,'team_history_time':r.available,**z})
    th=pd.DataFrame(history).sort_values('team_history_time')
    for side,key in [('team','club'),('opp','opponent')]:
        tmp=th.rename(columns={'club_key':key,'team_history_time':f'{side}_time',**{x:f'{side}_{x}' for x in ['elo','gf','ga']}})
        merged=pd.merge_asof(merged.sort_values('cutoff'),tmp,left_on='cutoff',right_on=f'{side}_time',by=key,allow_exact_matches=False)
        assert (merged[f'{side}_time'].dropna()<merged.loc[merged[f'{side}_time'].notna(),'cutoff']).all()
    merged['elo_diff']=merged.team_elo.fillna(1500)-merged.opp_elo.fillna(1500)
    merged['elo_win']=1/(1+10**(-(merged.elo_diff+np.where(merged.was_home,60,-60))/400))
    merged['rest_days']=(merged.cutoff-merged.history_time).dt.total_seconds()/86400
    merged['home']=merged.was_home.astype(int)
    for pos in [1,2,3,4]:merged[f'pos_{pos}']=(merged.pos==pos).astype(int)
    merged['xg_missing']=merged.expected_goals_m6.isna().astype(int)
    merged['trend']=merged.historic_m3-merged.historic_m12
    merged=merged.sort_values(['cutoff','pid','fixture']).reset_index(drop=True)
    base=['home','pos_1','pos_2','pos_3','pos_4','n_history','rest_days','last_price']
    simple=base+[f'{c}_m{w}' for c in ['historic','minutes','played','long_play'] for w in [3,6,12,38]]
    full=base+[c for c in hist if c not in ['pid','history_time','n_history','last_price']]+['trend','xg_missing','team_elo','opp_elo','elo_diff','elo_win','team_gf','team_ga','opp_gf','opp_ga']
    full=list(dict.fromkeys(full))
    sets={'simple':simple,'full':full,'noelo':[c for c in full if 'elo' not in c],
          'noxg':[c for c in full if 'expected_' not in c and c!='xg_missing'],
          'noict':[c for c in full if not any(x in c for x in ['threat','creativity','influence'])],
          'noprice':[c for c in full if 'price' not in c]}
    (OUT/'features.json').write_text(json.dumps(sets,indent=2))
    merged.to_pickle(OUT/'features.pkl')
    return merged,sets

def linear(model):return make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler(),model)

def registry():
    return [
        ('mean3','baseline','full',3),('mean6','baseline','full',6),('mean12','baseline','full',12),('ewm15','baseline','full',15),
        ('eb5','eb','full',5),('eb20','eb','full',20),
        ('ridge_simple','ridge','simple',100),('ridge1','ridge','full',1),('ridge100','ridge','full',100),
        ('elastic','elastic','full',None),('bayesian_ridge','bayes','full',None),
        ('hgb15','hgb','full',(15,20)),('hgb31','hgb','full',(31,20)),('hgb_l2','hgb','full',(15,100)),
        ('hgb_noelo','hgb','noelo',(15,20)),('hgb_noxg','hgb','noxg',(15,20)),
        ('hgb_noict','hgb','noict',(15,20)),('hgb_noprice','hgb','noprice',(15,20)),
        ('extra_trees','extra','full',None),('random_forest','rf','full',None),
        ('neural_mlp','mlp','simple',None),('hurdle','hurdle','full',None),
        ('poisson_components','components','simple',None)]

def predict(cfg,tr,te,sets,target,return_model=False):
    name,kind,fs,param=cfg; y=tr[target].to_numpy();cols=sets[fs]
    X=tr[cols].to_numpy(dtype=float);T=te[cols].to_numpy(dtype=float)
    if kind in ['baseline','eb']:
        prior=te.pos.map(tr.groupby('pos')[target].mean()).fillna(y.mean())
        if kind=='eb':return ((te[f'{target}_sum'].fillna(0)+param*prior)/(te.n_history.fillna(0)+param)).to_numpy()
        col=f'{target}_e15' if name=='ewm15' else f'{target}_m{param}'
        return te[col].fillna(prior).to_numpy()
    if kind=='ridge':model=linear(Ridge(alpha=param))
    elif kind=='elastic':model=linear(ElasticNet(alpha=.02,l1_ratio=.1,max_iter=1500))
    elif kind=='bayes':model=linear(BayesianRidge(max_iter=300))
    elif kind=='hgb':model=HistGradientBoostingRegressor(max_iter=140,learning_rate=.06,max_leaf_nodes=param[0],l2_regularization=param[1],min_samples_leaf=60,early_stopping=False,random_state=17)
    elif kind=='extra':model=make_pipeline(SimpleImputer(),ExtraTreesRegressor(n_estimators=64,max_depth=14,min_samples_leaf=30,max_features=.7,n_jobs=2,random_state=17))
    elif kind=='rf':model=make_pipeline(SimpleImputer(),RandomForestRegressor(n_estimators=48,max_depth=12,min_samples_leaf=40,max_features=.7,n_jobs=2,random_state=17,max_samples=.65))
    elif kind=='mlp':model=linear(MLPRegressor(hidden_layer_sizes=(32,16),alpha=10,max_iter=65,batch_size=1024,early_stopping=False,random_state=17))
    elif kind=='hurdle':
        clf=HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,l2_regularization=20,early_stopping=False,random_state=17)
        clf.fit(X,tr.played)
        reg=HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=15,l2_regularization=20,early_stopping=False,random_state=17)
        mask=tr.played.to_numpy()>0;reg.fit(X[mask],y[mask]);return clf.predict_proba(T)[:,1]*reg.predict(T)
    elif kind=='components':
        # Poisson mean models for event counts; no claim of full joint distribution.
        result=np.zeros(len(te))
        components={'played':1,'long_play':1,'goals_scored':te.pos.map({1:10,2:6,3:5,4:4}).to_numpy(),
                    'clean_sheets':te.pos.map({1:4,2:4,3:1,4:0}).to_numpy(),
                    'save_points':1,'conceded_points':-1,'penalties_saved':5,'penalties_missed':-2,
                    'yellow_cards':-1,'red_cards':-3,'own_goals':-2}
        if target=='historic':components.update({'assists':3,'bonus':1,'dc_points':1})
        for c,weight in components.items():
            yy=tr[c].to_numpy()
            if yy.sum()==0:continue
            m=linear(PoissonRegressor(alpha=1,max_iter=120));m.fit(X,yy);v=m.predict(T)
            if c in ['played','long_play','clean_sheets']:v=np.minimum(v,1)
            result+=v*weight
        return result
    else:raise ValueError(kind)
    model.fit(X,y)
    if return_model:return model
    return model.predict(T)

def metrics(te,pred,target):
    y=te[target].to_numpy();e=(pred-y)**2
    active=te.minutes_m6.fillna(0).to_numpy()>=45
    w=te[['season','event','pid',target]].copy();w['pred']=pred
    w=w.groupby(['season','event','pid'],as_index=False)[[target,'pred']].sum()
    top=w.sort_values('pred',ascending=False).groupby(['season','event']).head(20)
    cap=w.sort_values('pred',ascending=False).groupby(['season','event']).head(1)
    return dict(rmse=float(np.sqrt(e.mean())),mae=float(np.abs(pred-y).mean()),
        active_rmse=float(np.sqrt(e[active].mean())) if active.any() else np.nan,
        top20_mean=float(top[target].mean()),captain_mean=float(cap[target].mean()),n=len(y))

def run():
    self_test();t0=time.time();d,f=load_data();d,sets=features(d,f)
    d['save_points']=np.floor(d.saves/3)*(d.pos==1)
    d['conceded_points']=np.floor(d.goals_conceded/2)*d.pos.isin([1,2])
    d['dc_points']=0.
    mask=d.season=='2025-26';d.loc[mask,'dc_points']=defensive_points(d.loc[mask])
    allrows=[];predrows=[];configs=registry();frozen={}
    # 2019/20 GW1-10 warmup; subsequent seasons use only earlier seasons for fitting.
    # 2025/26 is assessed after selection using <=2024/25 only.
    for target in ['historic','core']:
        use=configs if target=='historic' else [c for c in configs if c[0] in ['mean6','ridge100','bayesian_ridge','hgb15','hgb_noelo','hgb_noxg','poisson_components']]
        for s in SEASONS:
            if s==SEASONS[0]:
                tr=d[(d.season==s)&(d.event<=10)].copy();te=d[(d.season==s)&(d.event>10)].copy()
            else:tr=d[d.season<s].copy();te=d[d.season==s].copy()
            # Purge any training observation not settled before first test decision.
            tr=tr[tr.available<te.cutoff.min()]
            assert tr.available.max()<te.cutoff.min()
            if s=='2025-26':
                dev=pd.DataFrame([x for x in allrows if x['target']==target])
                b=dev[dev.model=='mean6'].set_index('season').rmse
                dev['ratio']=dev.apply(lambda r:r.rmse/b[r.season],axis=1)
                a=dev.groupby('model').ratio.agg(['mean','max'])
                a['criterion']=.5*a['mean']+.5*a['max']; frozen[target]=a.criterion.idxmin()
                (OUT/'frozen_selection.json').write_text(json.dumps(frozen,indent=2))
                print('FROZEN before 2025/26:',target,frozen[target],flush=True)
            pp={}
            for cfg in use:
                name=cfg[0];start=time.time()
                p=predict(cfg,tr,te,sets,target);assert np.isfinite(p).all();pp[name]=p
                row={'target':target,'season':s,'model':name,'n_train':len(tr),**metrics(te,p,target),'seconds':time.time()-start}
                allrows.append(row);print(target,s,name,round(row['rmse'],4),round(row['seconds'],1),flush=True)
            # Fixed, predeclared blend; no fitting weights against evaluation data.
            pp['blend']=.5*pp['hgb15']+.25*pp['ridge100']+.25*pp['mean6']
            allrows.append({'target':target,'season':s,'model':'blend','n_train':len(tr),**metrics(te,pp['blend'],target),'seconds':0})
            pv=te[['season','event','fixture','pid','pos',target,'minutes_m6']].copy().rename(columns={target:'actual'})
            for name,p in pp.items():pv[name]=p
            raw=pv.to_csv(index=False).encode()
            path=OUT/f'predictions_{target}_{s}.csv.gz'
            path.write_bytes(gzip.compress(raw,mtime=0))
            assert gzip.decompress(path.read_bytes())==raw
            pd.DataFrame(allrows).to_csv(OUT/'metrics.csv',index=False)
    (OUT/'run_summary.json').write_text(json.dumps({'elapsed_seconds':time.time()-t0,'n_rows':len(d),'n_features':len(sets['full']),
        'historic_variants':len(configs)+1,'core_variants':8,'frozen':frozen,'seed':17},indent=2))
    print('DONE',time.time()-t0,flush=True)

if __name__=='__main__':run()
