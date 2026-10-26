"""Post-run checks use saved choices; do not call the H3/H8 chooser."""
import copy
import math
from .common import read,sha,digest,atomic_json
from .horizon_execution import HERE,DESIGN,SEASONS,normalized,bound,stamp
from .horizon_preflight import A
from .simulation import backend
from .manager_learning import Environment,settle
from . import manager_policy as base

def audit():
    bound();assert read(HERE/'execution_complete.json')['decisions']==152
    env=Environment();mod,ad=backend(16,200);results=[];verified=0;calls=0;nodes=0;options_checked=0
    def check(o,p,x,h,before,g):
        nonlocal options_checked
        after,c=ad.engine.apply_decision(before,copy.deepcopy(o['choice']),p.to_dict('records'),g)
        assert after==o['after'] and base.identity(c)==o['id']
        features=base.encode(p,x,h,before,after,c,ad.engine,g)
        assert all(math.isclose(a,b,abs_tol=1e-9) for a,b in zip(features,o['features']))
        reserve=0 if c['chip'] is None else ad.policy.reserve_value(c['chip'],g)
        expected=100*features[9]+.9*100*features[14]+.81*100*features[15]-reserve
        assert math.isclose(expected,o['base_score'],abs_tol=1e-8)
        options_checked+=1
    for season in SEASONS:
        arms={}
        for horizon in (3,8):
            folder=HERE/'runs'/f'{season}_h{horizon}';state=ad.engine.initial_state();total=0.;hits=0;chips={c:[] for c in base.CHIPS};armcalls=0;armnodes=0;seconds=0.;max_seconds=0.
            for gw in range(1,39):
                path=folder/f'gw{gw:02d}.decision.json';raw=read(path);d=normalized(raw);row=read(folder/f'gw{gw:02d}.settled.json');w=read(folder/f'gw{gw:02d}.watchdog.json')
                p,x,m,h=env.inputs(season,gw);assert x.shape[1]>=min(8,39-gw)
                assert d['state_before']==state and d['forecast_at']==m['forecast_at']
                assert d['forecast_array_sha256']==digest(x.tolist()) and not d['outcomes_read']
                assert d['execution_lock_sha256']==sha(HERE/'execution_lock.json')
                assert row['decision_sha256']==w['decision_sha256']==sha(path) and not w['timeout'] and w['seconds']<=120
                assert row['outcomes_read'] and d['requested_horizon']==horizon and d['horizon']==min(horizon,39-gw)
                if horizon==3:
                    old=read(A/'runs'/season/f'gw{gw:02d}.decision.json')
                    for key in ('options','branches','selected_index','shortlist','control_index','state_before','horizon'):
                        assert raw[key]==old[key],('H3 parity',season,gw,key)
                for o in d['options']:check(o,p,x,h,state,gw)
                ci=max(range(len(d['options'])),key=lambda i:(d['options'][i]['base_score'],d['options'][i]['id']))
                assert ci==d['control_index']
                ranked=sorted(range(len(d['options'])),key=lambda i:(d['options'][i]['base_score'],d['options'][i]['id']),reverse=True)
                shortlist=[];seen=set()
                for i in ranked:
                    key=digest(d['options'][i]['after'])
                    if key not in seen:shortlist.append(i);seen.add(key)
                    if len(shortlist)==2:break
                assert shortlist==d['shortlist'] and ci in shortlist
                assert [b['root_index'] for b in d['branches']]==shortlist
                for b in d['branches']:
                    current=copy.deepcopy(state);score=0.;blank=bool(m.get('official_all_blank_forced_wait'))
                    assert len(b['steps'])==(1 if blank else d['horizon'])
                    for offset,step in enumerate(b['steps']):
                        g=gw+offset;assert step['gw']==g and step['state_before']==current
                        if offset==0:assert step['selected']==d['options'][b['root_index']]
                        else:
                            for o in step['options']:check(o,p,x[:,offset:d['horizon']],h,current,g)
                            best=max(range(len(step['options'])),key=lambda i:(step['options'][i]['base_score'],step['options'][i]['id']))
                            assert step['selected_index']==best and step['selected']==step['options'][best]
                        c=step['selected']['choice'];values=dict(zip(p.pid,x[:,offset]))
                        ids=c['squad'] if c['chip']=='bench_boost' else c['starters']
                        multiplier=2 if c['chip']=='triple_captain' else 1
                        reserve=0 if c['chip'] is None else ad.policy.reserve_value(c['chip'],g)
                        reward=0. if blank else sum(values[i] for i in ids)+multiplier*values[c['captain']]-4*c['paid']-reserve
                        assert math.isclose(reward,step['reward'],abs_tol=1e-8)
                        score+=.9**offset*reward;current=step['selected']['after']
                    assert math.isclose(score,b['score'],abs_tol=1e-8)
                chosen=max(d['branches'],key=lambda b:(b['score'],b['root_index']==ci,d['options'][b['root_index']]['id']))['root_index']
                assert d['selected_index']==chosen and d['selected']==d['options'][chosen]
                assert len(d['solver_calls'])<=200 and max(d['proposal_call_counts'])<=40 and sum(d['proposal_call_counts'])==len(d['solver_calls'])
                for call in d['solver_calls']:
                    assert call['options']==ad.options and call['nodes']<=16 and call['full_mip_feasible']
                    assert call['termination_class'] in ('optimal_within_gap','node_limit_incumbent')
                outcomes,result,net=settle(ad,env,season,gw,d['selected'],p)
                assert outcomes==row['outcomes'] and mod.clean(result)==row['settlement'] and net==row['net_points']
                c=d['selected']['choice'];total+=net;hits+=4*c['paid']
                if c['chip']:chips[c['chip']].append(gw)
                armcalls+=len(d['solver_calls']);armnodes+=sum(r['nodes'] for r in d['solver_calls']);seconds+=w['seconds'];max_seconds=max(max_seconds,w['seconds']);state=d['selected']['after'];verified+=1
            summary=read(folder/'summary.json');assert total==summary['net_points'] and armcalls==summary['calls']
            arms[str(horizon)]=dict(net_points=total,hits=hits,chips=chips,calls=armcalls,nodes=armnodes,seconds=seconds,max_decision_seconds=max_seconds,
                final_bank=state['bank'],final_ft=state['ft'],unused_chips={half:[c for c in base.CHIPS if c not in state['used_chips'][half]] for half in ('1','2')})
            calls+=armcalls;nodes+=armnodes
        results.append(dict(season=season,H3=arms['3']['net_points'],H8=arms['8']['net_points'],difference=arms['8']['net_points']-arms['3']['net_points'],details=arms))
    assert verified==152 and calls<=30400 and nodes<=486400
    bound();atomic_json(HERE/'audit.json',dict(status='pass',at_utc=stamp(),rounds_verified=verified,options_checked=options_checked,
        h3_archive_parities=76,calls=calls,nodes=nodes,results=results,passed=all(r['difference']>0 for r in results),
        prospective_rows_used=0,model_fits=0,forecast_package_unchanged=True))
    print('All four episodes independently audited',flush=True)

if __name__=='__main__':audit()
