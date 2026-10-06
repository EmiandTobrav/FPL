"""Counterfactual FPL season replay, 2026/27 squad/transfer/chip rules.
Historical player points; not a complete 2026/27 point rescore or rank proof.
Decisions receive only frozen pre-GW forecasts, metadata and price proxies.
Never feed future rows of the prediction files into an earlier decision.
"""
from pathlib import Path
from itertools import combinations
import json,time,gzip,argparse,pickle
import numpy as np
import pandas as pd
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix
from concurrent.futures import ProcessPoolExecutor,as_completed

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'simulation';OUT.mkdir(exist_ok=True)
SEASONS=[f'{y}-{str(y+1)[-2:]}' for y in range(2019,2026)]
MAIN=['mean3','mean6','mean12','ewm15','eb5','eb20','ridge_simple','ridge1','ridge100','elastic',
      'bayesian_ridge','hgb15','hgb31','hgb_l2','hgb_noelo','hgb_noxg','hgb_noict','hgb_noprice',
      'extra_trees','random_forest','neural_mlp','hurdle','poisson_components','blend']
MODELS=MAIN+['bayes_events3','bayes_events10','bayes_events30','bayes_events10_elo']
SENSITIVITY=['mean6','ewm15','ridge100','bayesian_ridge','extra_trees','random_forest','hgb15','hurdle']
FORMATIONS=[(1,d,m,11-1-d-m) for d in range(3,6) for m in range(2,6) if 1<=11-1-d-m<=3]

def selling_price(purchase,market):
    return market if market<=purchase else purchase+(market-purchase)//2

def next_free(ft,transfers,chip,initial=False):
    if initial:return 1
    if chip in ['wildcard','free_hit']:return ft
    return min(5,max(0,ft-transfers)+1)

def legal_positions(ids,pos):
    counts=tuple(sum(pos[i]==p for i in ids) for p in range(1,5))
    return counts in FORMATIONS

def settle(starters,bench,captain,vice,pos,points,active,chip=None):
    """Subs are determined by availability/formation, NEVER by realised points.
    Bench contains reserve keeper and three outfield players in priority order.
    Missing starters remain placeholders until legally replaced.
    """
    final=list(starters);subs=[]
    if chip=='bench_boost':final=list(starters)+list(bench)
    else:
        gk=next(i for i in starters if pos[i]==1)
        bgk=next(i for i in bench if pos[i]==1)
        if not active.get(gk,False) and active.get(bgk,False):
            final[final.index(gk)]=bgk;subs.append((gk,bgk))
        missing=[i for i in starters if pos[i]!=1 and not active.get(i,False)]
        available=[i for i in bench if pos[i]!=1 and active.get(i,False)]
        best=None
        for k in range(min(len(missing),len(available))+1):
            for incoming in combinations(available,k):
                for outgoing in combinations(missing,k):
                    candidate=[i for i in final if i not in outgoing]+list(incoming)
                    if not legal_positions(candidate,pos):continue
                    # Max substitutions, then the highest priority bench subset.
                    key=(k,tuple(i in incoming for i in available))
                    if best is None or key>best[0]:best=(key,candidate,list(zip(outgoing,incoming)))
        if best is not None:final=best[1];subs+=best[2]
    effective=captain if active.get(captain,False) else vice if active.get(vice,False) else None
    multiplier=2 if chip=='triple_captain' else 1
    base=sum(points.get(i,0) for i in final)
    bonus=multiplier*points.get(effective,0) if effective is not None else 0
    direct_chip=(sum(points.get(i,0) for i in bench) if chip=='bench_boost' else points.get(effective,0) if chip=='triple_captain' and effective is not None else 0)
    return dict(gross=base+bonus,base=base,captain_bonus=bonus,effective_captain=effective,
                counted=final,subs=subs,autosub_gain=sum(points.get(b,0)-points.get(a,0) for a,b in subs),direct_chip_points=direct_chip)

def choose(pool,owned,bank,ft,chip=None,bench_weight=.10,transfer_friction=.5,full_pool=False):
    """Same one-week policy for every forecast model. No future forecast rows.
    0.5 expected-point friction per ordinary transfer values continuity/free slots.
    Up to 20 transfers each ordinary GW; WC/FH unrestricted. Candidate shortlist
    uses projections and prices only. Optimality refers to that shortlist.
    """
    p=pool.copy();p['owned']=p.pid.isin(owned)
    if not full_pool:
        ids=set(owned)
        for pos in [1,2,3,4]:
            g=p[(p.pos==pos)&p.can_buy]
            ids.update(g.nlargest(22 if pos!=1 else 12,'xp').pid)
            ids.update(g.sort_values(['market','xp','pid'],ascending=[True,False,True]).head(8).pid)
            ids.update(g.assign(value=g.xp/g.market).nlargest(8,'value').pid)
        p=p[p.pid.isin(ids)].copy()
    p=p.sort_values('pid').reset_index(drop=True)
    n=len(p);size=3*n+1;xp=np.maximum(p.xp.to_numpy(),0)
    own=p.owned.to_numpy();market=p.market.to_numpy(dtype=int)
    price=np.array([selling_price(owned[int(pid)],int(v)) if int(pid) in owned else int(v) for pid,v in zip(p.pid,market)])
    total_funds=bank+price[own].sum()
    obj=np.zeros(size)
    if chip=='bench_boost':obj[:n]=-xp;obj[n:2*n]=-1e-6*xp
    else:obj[:n]=-bench_weight*xp;obj[n:2*n]=-(1-bench_weight)*xp
    obj[2*n:3*n]=-(2 if chip=='triple_captain' else 1)*xp
    ordinary=bool(owned) and chip not in ['wildcard','free_hit']
    if ordinary:obj[:n]+=transfer_friction*(~own)
    # Stable tie breaking favouring fewer transfers, cheaper squad then lower ID.
    obj[:n]+=1e-7*market+np.arange(n)*1e-10
    obj[-1]=4
    rr=[];cc=[];vv=[];lo=[];hi=[]
    def add(idx,val,l=-np.inf,u=np.inf):
        row=len(lo);idx=np.asarray(list(idx),dtype=int);val=np.broadcast_to(val,idx.shape)
        rr.extend([row]*len(idx));cc.extend(idx.tolist());vv.extend(val.tolist());lo.append(l);hi.append(u)
    add(range(n),1,15,15);add(range(n,2*n),1,11,11);add(range(2*n,3*n),1,1,1)
    add(range(n),price,u=total_funds)
    for pos,count,l,u in [(1,2,1,1),(2,5,3,5),(3,5,2,5),(4,3,1,3)]:
        idx=np.flatnonzero(p.pos.to_numpy()==pos);add(idx,1,count,count);add(idx+n,1,l,u)
    for club in p.club.unique():add(np.flatnonzero(p.club.to_numpy()==club),1,u=3)
    for i in range(n):add([n+i,i],[1,-1],u=0);add([2*n+i,n+i],[1,-1],u=0)
    if ordinary:
        idx=np.flatnonzero(~own)
        add(list(idx)+[size-1],list(np.ones(len(idx)))+[-1],u=ft)
        add(idx,1,u=20)
    upper=np.ones(size);upper[-1]=15
    upper[:n]=np.where(p.can_buy.to_numpy()|own,1,0)
    matrix=coo_matrix((vv,(rr,cc)),shape=(len(lo),size)).tocsc()
    r=milp(obj,integrality=np.ones(size),bounds=Bounds(np.zeros(size),upper),
           constraints=LinearConstraint(matrix,lo,hi),options={'time_limit':5,'mip_rel_gap':1e-7})
    if r.x is None:
        if not full_pool:return choose(pool,owned,bank,ft,chip,bench_weight,transfer_friction,True)
        raise RuntimeError(f'No feasible team: {r.message}')
    chosen=p[r.x[:n]>.5].copy();starters=p.loc[r.x[n:2*n]>.5,'pid'].astype(int).tolist()
    # Captain selection from chosen XI is explicit and deterministic.
    order=p[p.pid.isin(starters)].sort_values(['xp','pid'],ascending=[False,True]).pid.astype(int).tolist()
    cap,vice=order[:2]
    bench=p[~p.pid.isin(starters)&p.pid.isin(chosen.pid)].sort_values(['pos','xp','pid'],ascending=[True,False,True])
    bgk=bench[bench.pos==1].pid.astype(int).tolist()
    bout=bench[bench.pos!=1].sort_values(['xp','pid'],ascending=[False,True]).pid.astype(int).tolist()
    ids=set(chosen.pid.astype(int));incoming=ids-set(owned);outgoing=set(owned)-ids
    transfers=len(incoming) if owned else 0;paid=max(0,transfers-ft) if ordinary else 0
    prices=dict(zip(p.pid.astype(int),market.astype(int)))
    after=bank+sum(selling_price(owned[i],prices[i]) for i in outgoing)-sum(prices[i] for i in incoming)
    if not owned:after=bank-sum(prices[i] for i in incoming)
    assert after>=0
    assert len(ids)==15 and len(starters)==11 and len(bgk+bout)==4
    assert chosen.groupby('pos').size().to_dict()=={1:2,2:5,3:5,4:3}
    assert chosen.groupby('club').size().max()<=3
    assert legal_positions(starters,dict(zip(p.pid,p.pos)))
    return dict(squad=ids,starters=starters,bench=bgk+bout,captain=cap,vice=vice,
                incoming=incoming,outgoing=outgoing,transfers=transfers,paid=paid,bank_after=int(after),
                prices=prices,solver_gap=float(getattr(r,'mip_gap',0)),solver_status=int(r.status),pool_size=len(p))

def chip_calendar(start=1,variant='A'):
    if variant=='A':return {max(start+1,6):'wildcard',15:'triple_captain',18:'free_hit',19:'bench_boost',
                           24:'wildcard',33:'free_hit',36:'bench_boost',37:'triple_captain'}
    return {max(start+1,8):'wildcard',14:'triple_captain',17:'free_hit',19:'bench_boost',
            25:'wildcard',34:'free_hit',36:'triple_captain',37:'bench_boost'}

def prepare():
    d=pd.read_pickle(ROOT/'results/features.pkl');audit=[]
    for s in SEASONS:
        z=d[d.season==s].copy();z['pid']=z.pid.astype(int)
        f=pd.read_csv(ROOT/f'data/{s}_fixtures.csv');teams=pd.read_csv(ROOT/f'data/{s}_teams.csv').set_index('id')
        rawp=pd.read_csv(ROOT/f'data/{s}_players.csv');rawp=rawp[rawp.element_type.isin([1,2,3,4])].set_index('code')
        existing=sorted(z.event.unique().astype(int))
        events=existing if s=='2019-20' else list(range(1,39))
        event_index={event:k+1 for k,event in enumerate(events)}
        z['gw']=z.event.map(event_index)
        first=z.sort_values('kickoff').drop_duplicates('pid').set_index('pid')
        meta=first[['pos','club','gw']].rename(columns={'gw':'registered_gw'}).copy()
        meta['name']=rawp.web_name.reindex(meta.index)
        meta['initial_price']=(rawp.now_cost-rawp.cost_change_start).reindex(meta.index).astype(int)
        clubs=pd.concat([f[['event','team_h']].rename(columns={'team_h':'tid'}),f[['event','team_a']].rename(columns={'team_a':'tid'})])
        clubs['club']=clubs.tid.map(teams.code);clubs['gw']=clubs.event.map(event_index)
        firstclub=clubs.groupby('club').gw.min()
        # Clubs blanking GW1 have a roster even though match histories start later.
        meta.loc[meta.registered_gw==meta.club.map(firstclub),'registered_gw']=1
        a=pd.read_csv(ROOT/f'results/predictions_historic_{s}.csv.gz')
        b=pd.read_csv(ROOT/f'results/bayes_predictions_historic_{s}.csv.gz')
        pred=a.merge(b[['event','fixture','pid']+MODELS[24:]],on=['event','fixture','pid'],validate='one_to_one')
        pred['gw']=pred.event.map(event_index)
        grouped=pred.groupby(['gw','pid'])[MODELS].sum()
        games={};lastcut=None
        for gw,event in enumerate(events,1):
            g=z[z.event==event]
            if len(g):cut=g.cutoff.min();lastcut=cut
            else:cut=lastcut+pd.Timedelta(days=7)
            prior=z[z.available<cut].sort_values('available').drop_duplicates('pid',keep='last').set_index('pid')
            current=g.sort_values('kickoff').drop_duplicates('pid').set_index('pid')
            frame=meta[meta.registered_gw<=gw].copy()
            frame['club']=prior.club.reindex(frame.index).fillna(frame.club)
            frame['club']=current.club.reindex(frame.index).fillna(frame.club)
            frame['market_lag']=np.rint(prior.price.reindex(frame.index)*10).fillna(frame.initial_price).astype(int)
            frame['market_recorded']=np.rint(current.price.reindex(frame.index)*10).fillna(frame.market_lag).astype(int)
            activeclubs=set(clubs.loc[clubs.gw==gw,'club'])
            frame['can_buy']=frame.index.isin(current.index)|~frame.club.isin(activeclubs)
            try:pg=grouped.loc[gw]
            except KeyError:pg=pd.DataFrame(columns=MODELS)
            for model in MODELS:frame[model]=pg[model].reindex(frame.index).fillna(0).clip(lower=0)
            actual=g.groupby('pid').historic.sum().to_dict()
            played=g.assign(active=(g.minutes>0)|(g.yellow_cards>0)|(g.red_cards>0)).groupby('pid').active.max().to_dict()
            frame=frame.reset_index().rename(columns={'index':'pid'})
            games[gw]={'frame':frame,'actual':actual,'active':played,'event':int(event),'cutoff':str(cut)}
        mismatch=(z[z.gw==1].drop_duplicates('pid').set_index('pid').price*10-meta.initial_price).dropna()
        audit.append({'season':s,'rounds':len(games),'start_gw':11 if s=='2019-20' else 1,'initial_price_mismatches':int((mismatch.abs()>.01).sum()),'players':len(meta)})
        with open(OUT/f'cache_{s}.pkl','wb') as file:pickle.dump(games,file)
    pd.DataFrame(audit).to_csv(OUT/'data_audit.csv',index=False)

def run_one(task):
    s,model,mode,price_mode,start_strategy=task;start=11 if s=='2019-20' else 1
    with open(OUT/f'cache_{s}.pkl','rb') as file:games=pickle.load(file)
    calendar={} if mode=='no_chips' else chip_calendar(start,mode[-1])
    owned={};bank=1000;ft=1;history=[];rosters=[];last_chip=None
    t0=time.time()
    for gw in range(start,39):
        game=games[gw];p=game['frame'];pool=p[['pid','pos','club','can_buy']].copy()
        pool['xp']=p[model];pool['market']=p['market_'+price_mode]
        # Registrations persist, including removed players already owned.
        assert set(owned).issubset(set(pool.pid))
        chip=calendar.get(gw);initial=not owned
        if initial and start_strategy=='shared_preseason':
            if s=='2019-20':
                reference=pool.copy();reference['xp']=p.extra_trees
                initial_ids=choose(reference,{},1000,1)['squad']
            else:
                initial_table=pd.read_csv(OUT/'preseason_squads.csv')
                opening_method=json.loads((OUT/'preseason_selection.json').read_text())[s]
                initial_ids=set(initial_table[(initial_table.season==s)&(initial_table.method==opening_method)].pid.astype(int))
            assert len(initial_ids)==15
            pool=pool[pool.pid.isin(initial_ids)].copy()
        if initial and chip in ['free_hit','wildcard']:raise AssertionError('Chip at initial selection')
        if chip=='free_hit':assert last_chip!='free_hit'
        choice=choose(pool,owned,bank,ft,chip)
        pos=dict(zip(pool.pid,pool.pos));names=dict(zip(p.pid,p.name))
        result=settle(choice['starters'],choice['bench'],choice['captain'],choice['vice'],pos,game['actual'],game['active'],chip)
        cost=4*choice['paid'];net=result['gross']-cost
        before_bank=bank;before_ft=ft;before_owned=dict(owned)
        if chip!='free_hit':
            owned={i:owned[i] if i in owned else choice['prices'][i] for i in choice['squad']}
            bank=choice['bank_after']
        ft=next_free(ft,choice['transfers'],chip,initial)
        if chip=='free_hit':assert bank==before_bank and owned==before_owned
        assert 1<=ft<=5
        info={'season':s,'model':model,'mode':mode,'price_mode':price_mode,'start_strategy':start_strategy,'gw':gw,'event':game['event'],
              'chip':chip or '', 'net_points':net,'gross_points':result['gross'],'hit_cost':cost,
              'transfers':choice['transfers'],'paid_transfers':choice['paid'],'bank_before':before_bank/10,'bank_after':bank/10,
              'free_before':before_ft,'free_after':ft,'captain':names[choice['captain']],'vice':names[choice['vice']],
              'effective_captain':names.get(result['effective_captain'],''),'captain_bonus':result['captain_bonus'],
              'autosub_gain':result['autosub_gain'],'direct_chip_points':result['direct_chip_points'],
              'in':'; '.join(names[i] for i in sorted(choice['incoming'])),'out':'; '.join(names[i] for i in sorted(choice['outgoing'])),
              'solver_gap':choice['solver_gap'],'solver_status':choice['solver_status'],'candidate_count':choice['pool_size'],
              'decision_cutoff_proxy':game['cutoff']}
        history.append(info)
        for i in sorted(choice['squad']):
            actual=game['actual'].get(i,0);counted=i in result['counted']
            mult=(1 if counted else 0)+((2 if chip=='triple_captain' else 1) if result['effective_captain']==i else 0)
            rosters.append({'season':s,'model':model,'mode':mode,'price_mode':price_mode,'start_strategy':start_strategy,'gw':gw,'pid':i,'name':names[i],'pos':pos[i],
                            'starter':i in choice['starters'],'bench_priority':choice['bench'].index(i) if i in choice['bench'] else -1,
                            'captain':i==choice['captain'],'vice':i==choice['vice'],'forecast':float(pool.loc[pool.pid==i,'xp'].iloc[0]),
                            'actual_points':actual,'active':game['active'].get(i,False),'counted':counted,'multiplier':mult,
                            'contribution':actual*mult,'market_price':choice['prices'][i]/10,'chip':chip or ''})
        assert sum(r['contribution'] for r in rosters[-15:])==result['gross']
        last_chip=chip
    hist=pd.DataFrame(history);roster=pd.DataFrame(rosters)
    key=f'{s}_{model}_{mode}_{price_mode}_{start_strategy}'
    for kind,df in [('weeks',hist),('teams',roster)]:
        raw=df.to_csv(index=False).encode();path=OUT/f'{kind}_{key}.csv.gz';path.write_bytes(gzip.compress(raw,mtime=0))
    summary={'season':s,'model':model,'mode':mode,'price_mode':price_mode,'start_strategy':start_strategy,'rounds':len(hist),
             'total_points':int(hist.net_points.sum()),'gross_points':int(hist.gross_points.sum()),'hit_cost':int(hist.hit_cost.sum()),
             'transfers':int(hist.transfers.sum()),'captain_bonus':int(hist.captain_bonus.sum()),'autosub_gain':int(hist.autosub_gain.sum()),
             'direct_chip_points':int(hist.direct_chip_points.sum()),'chips_used':int((hist.chip!='').sum()),
             'end_bank':bank/10,'nonoptimal_solves':int((hist.solver_status!=0).sum()),'max_mip_gap':float(hist.solver_gap.max()),
             'points_gw1_6':int(hist.loc[hist.gw<=6,'net_points'].sum()) if start==1 else np.nan,
             'points_gw7_19':int(hist.loc[hist.gw.between(7,19),'net_points'].sum()) if start==1 else np.nan,
             'points_gw20_38':int(hist.loc[hist.gw>=20,'net_points'].sum()),
             'seconds':time.time()-t0}
    return summary

def run_suite(workers=4,sensitivity=False,quick=False):
    if quick:tasks=[('2025-26','extra_trees',mode,'lag',strategy) for mode in ['no_chips','chips_A'] for strategy in ['self','shared_preseason']]
    elif sensitivity:
        tasks=[(s,m,'chips_B','lag','shared_preseason') for s in SEASONS for m in SENSITIVITY]
        tasks += [(s,m,c,'recorded','shared_preseason') for s in SEASONS for m in SENSITIVITY for c in ['no_chips','chips_A']]
    else:tasks=[(s,m,c,'lag',strategy) for s in SEASONS for m in MODELS for c in ['no_chips','chips_A'] for strategy in ['self','shared_preseason']]
    label='quick' if quick else 'sensitivity' if sensitivity else 'primary'
    results=[];t=time.time()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(run_one,task):task for task in tasks}
        for fut in as_completed(futures):
            row=fut.result();results.append(row)
            pd.DataFrame(results).sort_values(['season','model','mode','price_mode','start_strategy']).to_csv(OUT/f'{label}_summary.csv',index=False)
            print(len(results),'/',len(tasks),row['season'],row['model'],row['mode'],row['price_mode'],row['start_strategy'],row['total_points'],round(row['seconds'],1),'elapsed',round(time.time()-t),flush=True)
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--quick',action='store_true')
    parser.add_argument('--sensitivity',action='store_true');parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    if args.prepare:prepare()
    else:run_suite(args.workers,args.sensitivity,args.quick)
