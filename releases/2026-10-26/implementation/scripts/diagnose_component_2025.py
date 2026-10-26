"""Frozen-result diagnosis, not tuning or a new deployable hindsight strategy."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import sys,json,collections,itertools
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json,verify_files
P=R/'reports/component_2025_diagnosis_2026_10_26'
F=R/'reports/matched_season_retest_2026_10_26_v8'
S=['2023-24','2024-25','2025-26'];ARMS=['component','operational_matched'];KEY=['season','round','code']
def read(p):return json.loads(Path(p).read_text())
def cache(s,g):return R/('reports/fpl_simulator_2026_10_13/cache_manager' if s=='2025-26' else 'reports/fpl_improvement_2026_10_14/cache')/s/f'gw{g:02d}'
def oracle(pool,points,budget=1000):
    """Constant-budget weekly difficulty index with perfect future outcomes.

    Free rebuild each week, no chips or hits. It is NOT an attainable season
    strategy, a production forecast or an explanation of causal score losses.
    """
    p=pool[pool.can_buy].sort_values('pid').reset_index(drop=True);n=len(p);size=3*n;y=np.array([points.get(int(i),0.) for i in p.pid]);cost=p.market.to_numpy();pos=p.pos.to_numpy();club=p.club.to_numpy()
    obj=np.r_[np.zeros(n),-y,-y];rr=[];cc=[];vv=[];lo=[];hi=[]
    def add(idx,values,lower=-np.inf,upper=np.inf):
        idx=np.asarray(list(idx),int);values=np.broadcast_to(values,idx.shape);r=len(lo);rr.extend([r]*len(idx));cc.extend(idx);vv.extend(values);lo.append(lower);hi.append(upper)
    add(range(n),1,15,15);add(range(n,2*n),1,11,11);add(range(2*n,3*n),1,1,1);add(range(n),cost,upper=budget)
    for v,count,l,u in [(1,2,1,1),(2,5,3,5),(3,5,2,5),(4,3,1,3)]:
        ix=np.flatnonzero(pos==v);add(ix,1,count,count);add(ix+n,1,l,u)
    for v in set(club):add(np.flatnonzero(club==v),1,upper=3)
    for i in range(n):add([n+i,i],[1,-1],upper=0);add([2*n+i,n+i],[1,-1],upper=0)
    A=coo_matrix((vv,(rr,cc)),shape=(len(lo),size)).tocsc()
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        result=milp(obj,integrality=np.ones(size),bounds=Bounds(np.zeros(size),np.ones(size)),constraints=LinearConstraint(A,lo,hi),options={'time_limit':10.,'mip_rel_gap':0.,'threads':1,'parallel':'off'})
    if result.x is None:raise ValueError('No diagnostic oracle solution')
    x=np.rint(result.x);assert np.max(abs(x-result.x))<1e-5;assert (A@x>=np.array(lo)-1e-5).all() and (A@x<=np.array(hi)+1e-5).all()
    score=float(-obj@x);upper=float(-result.mip_dual_bound);assert abs(score-round(score))<1e-5 and score<=upper+1e-5
    return dict(points=score,upper_bound=upper,gap=float(result.mip_gap),certified_optimal=bool(upper-score<1e-5),squad_price=float(cost@x[:n]),players=len(p))

def run():
    spec=read(P/'proposal.json');verify_files(R,spec['input_hashes']);d=pd.read_pickle(F/'head_data.pkl');av=pd.read_csv(F/'availability.csv.gz');av=av.set_index(KEY);pred={a:pd.read_csv(F/f'{a}.csv.gz').set_index(KEY) for a in ARMS}
    raw=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',low_memory=False);raw=raw[raw.season.isin(S)];truth=raw.groupby(KEY).agg(points=('target_total_points','sum'),minutes=('native_minutes','sum')).reset_index();names=raw.groupby('code').name.last().to_dict();yearpoints=raw.groupby(['season','code']).target_total_points.sum()
    metrics=[];weekly=[];contributions=[];selected=[];markets=[];oracles=[];league=[];calibration=[]
    md=pd.read_pickle(F/'metadata.pkl');schema=read(R/'datasets/fpl_common_training_v3/schema.json');coverage=pd.read_csv(F/'feature_coverage.csv');rawtruth=truth.set_index(KEY)
    for s in S:
        q=d[d.season.eq(s)].copy();index=pd.MultiIndex.from_frame(q[KEY]);mask=av.reindex(index).model_can_buy.to_numpy(bool);q=q[mask].copy();index=pd.MultiIndex.from_frame(q[KEY]);q['actual_minutes']=rawtruth.reindex(index).minutes.to_numpy();q['common_rank']=pred['operational_matched'].reindex(index).xp_0.to_numpy();q['in_common_top']=False
        for (g,pos),v in q.groupby(['round','position']):q.loc[v.nlargest(dict(GK=5,DEF=20,MID=20,FWD=10)[pos],'common_rank').index,'in_common_top']=True
        for arm in ARMS:
            p=pred[arm].reindex(pd.MultiIndex.from_frame(q[KEY]));q['p']=p.xp_0.to_numpy();q['p3']=p[['xp_0','xp_1','xp_2']].sum(axis=1).to_numpy()
            for scope,z in [('all_buyable',q),('common_top_candidates',q[q.in_common_top]),('premium_9m_plus',q[q.price_tenths.ge(90)])]:
                for block,start,end in [('full',1,38),('GW1_4',1,4),('GW5_12',5,12),('GW13_24',13,24),('GW25_38',25,38)]:
                    v=z[z['round'].between(start,end)&z.y_0.notna()];y=v.y_0.to_numpy(float);p=v.p.to_numpy(float);baseline=v.h_fixed_points.to_numpy(float)*v.u_count_0.to_numpy(float);known=np.isfinite(baseline)
                    if not len(y):continue
                    ranks=[v1.p.corr(v1.y_0,method='spearman') for _,v1 in v.groupby('round') if v1.p.nunique()>1 and v1.y_0.nunique()>1]
                    metrics.append(dict(season=s,arm=arm,scope=scope,block=block,n=len(v),actual_mean=y.mean(),actual_variance=y.var(),zero_share=float(np.mean(y==0)),mse=float(np.mean((p-y)**2)),bias=float(np.mean(p-y)),relative_mse_to_variance=float(np.mean((p-y)**2)/y.var()),mean_round_spearman=float(np.mean(ranks)),baseline_n=int(known.sum()),baseline_mse=float(np.mean((baseline[known]-y[known])**2)),base_points_mse=float(np.mean((v.component_p1-y)**2)),minutes_mse=float(np.mean((v.component_m1-v.actual_minutes)**2))))
            ctr=collections.Counter();capt=collections.Counter();terms=[]
            for g in range(1,39):
                folder=F/'manager'/f'{s}_{arm}';dec=read(folder/f'gw{g:02d}.decision.json');sett=read(folder/f'gw{g:02d}.settlement.json');c=dec['choice'];z=sett['settlement'];assert z['gross']-sett['hits']==sett['net'];terms.append(sett['net'])
                y={int(v['code']):float(v['points']) for v in sett['outcomes']};v=pred[arm].xs((s,g),level=['season','round']);expected=float(v.reindex(c['starters']).xp_0.sum()+(2 if c['chip']=='triple_captain' else 1)*v.loc[c['captain'],'xp_0'])
                if c['chip']=='bench_boost':expected+=float(v.reindex(c['bench']).xp_0.sum())
                capbonus=float(z['captain_bonus']);max_in_xi=max(y.get(int(i),0) for i in c['starters']);actual_cap=y.get(int(z['effective_captain']),0) if z['effective_captain'] is not None else 0
                pool=pd.read_csv(cache(s,g)/'pool.csv.gz');row=av.xs((s,g),level=['season','round']).reindex(pool.code);pool['can_buy']=row.model_can_buy.to_numpy(bool)
                pv=pool.set_index('code');code_to_pos=pv.pos.to_dict();clubtot=pool.set_index('code').club.to_dict();block='GW1_4' if g<=4 else 'GW5_12' if g<=12 else 'GW13_24' if g<=24 else 'GW25_38'
                weekly.append(dict(season=s,arm=arm,round=g,block=block,net=sett['net'],gross=z['gross'],base=z['base'],captain_bonus=capbonus,hits=sett['hits'],expected_start_and_cap=expected,gross_minus_expected=z['gross']-expected,transfers=c['transfers'],chip=c['chip'],direct_chip_points=z['direct_chip_points'],autosub_gain=z['autosub_gain'],captain=int(c['captain']),captain_name=names.get(int(c['captain'])),effective_captain_points=actual_cap,highest_actual_in_selected_XI=max_in_xi,captain_hindsight_gap_in_XI=(max_in_xi-actual_cap)*(2 if c['chip']=='triple_captain' else 1),starting_zero_minutes=sum(not next(v1['appeared'] for v1 in sett['outcomes'] if v1['code']==i) for i in c['starters'])))
                for code,value in z['contributions'].items():ctr[int(code)]+=value
                if z['effective_captain'] is not None:capt[int(z['effective_captain'])]+=capbonus
                for i in c['squad']:
                    selected.append(dict(season=s,arm=arm,round=g,code=i,name=names.get(i),position=code_to_pos[i],price_tenths=int(pv.at[i,'market']),starter=i in c['starters'],counted=i in z['counted'],captain=i==c['captain'],actual=y.get(i,0),forecast=float(v.at[i,'xp_0']),contribution=z['contributions'].get(str(i),0)))
                if arm==ARMS[0]:
                    official=md[(s,g)].set_index('code');both=pool[pool.code.isin(official.index)].copy();new=official.reindex(both.code);actual_clubs=both.club.map(lambda name: name)
                    teammap=pd.read_csv(R/f'FPL_training_dataset/research/current/project/data/{s}_teams.csv.gz');nm=dict(zip(teammap.name,teammap.code));nm['Ipswich Town']=nm.get('Ipswich');price_delta=both.market.to_numpy()-new.last_price.to_numpy()*10;club_delta=both.club.map(nm).to_numpy()!=new.club.to_numpy();pos_delta=both.pos.to_numpy()!=new.pos.to_numpy()
                    markets.append(dict(season=s,round=g,overlap=len(both),pool_size=len(pool),official_size=len(official),price_mismatch=int((abs(price_delta)>1e-4).sum()),maximum_price_error_tenths=float(np.max(abs(price_delta))),club_mismatch=int(club_delta.sum()),position_mismatch=int(pos_delta.sum()),official_players_missing_pool=len(set(official.index)-set(pool.code)),pool_players_missing_official=len(set(pool.code)-set(official.index))))
                    yy=rawtruth.xs((s,g),level=['season','round']).points.to_dict()
                    playing=set(raw.loc[raw.season.eq(s)&raw['round'].eq(g),'club_code'].astype(int))
                    for r in pool.itertuples():
                        club=nm.get(r.club)
                        if r.code not in yy and r.code in official.index and club==int(official.at[r.code,'club']) and club not in playing:yy[r.code]=0.
                    verified_pool=pool[pool.code.isin(yy)].copy();o=oracle(verified_pool,yy);oracles.append(dict(season=s,round=g,unknown_actual_players_excluded=int((pool.can_buy&~pool.code.isin(yy)).sum()),**o));pd.DataFrame(oracles).to_csv(P/'oracle_rounds.csv',index=False)
                if g%10==0:print('DIAGNOSIS',s,arm,g,flush=True)
            score=pd.read_csv(F/'scores.csv');expectednet=float(score.loc[score.season.eq(s)&score.arm.eq(arm),'net'].iloc[0]);assert sum(terms)==expectednet
            contributions.extend(dict(season=s,arm=arm,code=code,name=names.get(code),contribution=value,captain_bonus=capt[code]) for code,value in ctr.items())
        totals=yearpoints.loc[s].sort_values(ascending=False);league.append(dict(season=s,total_points=float(totals.sum()),top10=float(totals.head(10).sum()),top20=float(totals.head(20).sum()),top50=float(totals.head(50).sum()),points_top10_share=float(totals.head(10).sum()/totals.sum()),goals=float(raw.loc[raw.season.eq(s),'native_goals_scored'].sum())))
    for name,rows in [('metrics',metrics),('rounds',weekly),('contributions',contributions),('selected',selected),('market_comparison',markets),('league',league)]:pd.DataFrame(rows).to_csv(P/f'{name}.csv',index=False)
    w=pd.DataFrame(weekly);summary=w.groupby(['season','arm'])[['net','base','captain_bonus','hits','expected_start_and_cap','gross_minus_expected','transfers','direct_chip_points','autosub_gain','captain_hindsight_gap_in_XI','starting_zero_minutes']].sum();summary.to_csv(P/'decomposition.csv')
    w.groupby(['season','arm','block'])[['net','base','captain_bonus','hits','expected_start_and_cap','transfers']].sum().to_csv(P/'periods.csv')
    atomic_json(P/'audit.json',dict(passed=True,all_228_scores_exact=True,new_model_fits=0,new_policy_decisions=0,diagnostic_oracles=len(oracles),all_oracle_bounds_certified=all(r['certified_optimal'] for r in oracles),active_model_unchanged=True,warning='Hindsight difficulty indices are not deployable strategies, FPL ranks or causal attribution; predictive errors and actual team results remain separate.',files={str(p.relative_to(R)):sha(p) for p in P.glob('*.csv')}))
    print(summary.to_string(),flush=True)
if __name__=='__main__':run()
