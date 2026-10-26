"""Read-only verification and scoring for the locked takeover campaign."""
import sys
import numpy as np
import pandas as pd
from model_lab.takeover_campaign import R,P,C,S,ARMS,MANAGERS,REFITS,EXTRA
from model_lab.common import read,sha,atomic_json,verify_files,digest
from model_lab.simulation import backend,BENCHMARK
from model_lab.takeover_inputs import copy_takeover_state
from model_lab.manager_learning import Environment

def forecast_scores():
    lock=read(P/'forecast_lock.json');data=pd.read_pickle(P/'training.pkl')
    metrics=[];coverage=[];aggregate=[];allrows=[]
    for s in S:
        for gw in range(7,39):
            p=P/f'{s}_gw{gw:02d}.csv.gz';assert sha(p)==lock['outputs'][p.name]
            pred=pd.read_csv(p);pool=pd.read_csv(C/s/f'gw{gw:02d}'/'pool.csv.gz')
            baseline=pd.read_csv(C/s/f'gw{gw:02d}'/(BENCHMARK+'.csv.gz'))
            b=baseline.melt(id_vars=['code'],value_vars=[f'xp_{h}' for h in range(min(8,39-gw))],var_name='h',value_name='benchmark')
            b['offset']=b.h.str[3:].astype(int)
            z=pred.merge(b[['code','offset','benchmark']],on=['code','offset'],validate='one_to_one')
            lab=data[data.season.eq(s)&data.origin_round.eq(gw)][['code','offset','target_total_points']]
            z=z.merge(lab,on=['code','offset'],validate='one_to_one').merge(pool[['code','can_buy']],on='code',validate='many_to_one')
            z=z[z.can_buy].copy();z['repeat_H1']=z.code.map(z[z.offset.eq(0)].set_index('code').trajectory_full)
            allrows.append(z)
    z=pd.concat(allrows,ignore_index=True)
    for (s,h),g in z.groupby(['season','offset']):
        known=g.target_total_points.notna();coverage.append(dict(season=s,offset=int(h),eligible=len(g),known=int(known.sum()),missing=int((~known).sum())))
        for arm in ARMS+['repeat_H1']:
            e=g.loc[known,arm]-g.loc[known,'target_total_points']
            metrics.append(dict(season=s,offset=int(h),arm=arm,n=len(e),mse=float((e**2).mean()),mae=float(e.abs().mean()),bias=float(e.mean())))
    for h in [3,8]:
        for (s,gw,code),g in z[z.offset.lt(h)].groupby(['season','origin_round','code']):
            if len(g)!=h or g.target_total_points.isna().any():continue
            record=dict(season=s,origin_round=int(gw),code=int(code),horizon=h,actual=float(g.target_total_points.sum()))
            record.update({a:float(g[a].sum()) for a in ARMS+['repeat_H1']});aggregate.append(record)
    a=pd.DataFrame(aggregate);am=[]
    for (s,h),g in a.groupby(['season','horizon']):
        for arm in ARMS+['repeat_H1']:
            e=g[arm]-g.actual;am.append(dict(season=s,horizon=int(h),arm=arm,n=len(g),mse=float((e**2).mean()),mae=float(e.abs().mean())))
    pd.DataFrame(metrics).to_csv(P/'forecast_metrics.csv',index=False)
    pd.DataFrame(coverage).to_csv(P/'forecast_coverage.csv',index=False)
    pd.DataFrame(am).to_csv(P/'forecast_sum_metrics.csv',index=False)
    print(pd.DataFrame(am).to_string(index=False))

def audit():
    verify_files(R,read(P/'proposal.json')['input_hashes'])
    clock_audit=read(P/'target_clock_audit.json')
    assert clock_audit['known_target_at_or_before_origin']==0
    assert sha(P/'training.pkl')==clock_audit['training_table_sha256']
    fl=read(P/'forecast_lock.json');assert fl['fits']==16 and len(fl['outputs'])==64
    for n,h in fl['outputs'].items():assert sha(P/n)==h
    for n,h in read(P/'runtime_and_models.json')['models'].items():assert sha(P/n)==h
    for s in S:
        for gw in REFITS:
            for arm in ARMS[1:]:
                f=read(P/f'{s}_{gw:02d}_{arm}.fit.json');cutoff=pd.Timestamp(f['cutoff'])
                assert pd.Timestamp(f['latest_origin'])<cutoff and pd.Timestamp(f['latest_label'])<cutoff
                assert not any(n.startswith('target') or n in ['code','season','forecast_at'] for n in f['features'])
    for a in read(P/'data_lock.json')['audits']:
        if a['strength_max']!='NaT':assert pd.Timestamp(a['strength_max'])<pd.Timestamp(a['forecast_at'])
    states=read(R/'reports/takeover_workpackage_2026_10_17/takeover_states.json')
    mod,adapter=backend();env=Environment();count=0;inputs={};pairs=[];parity=[]
    for state in states:
        for arm in ARMS:
            for manager in MANAGERS:
                folder=P/'episodes'/(state['id']+'__'+arm+'__'+manager)
                current=copy_takeover_state(state['state'],state['round']);total=0.;hits=0
                for gw in range(state['round'],39):
                    d=read(folder/f'gw{gw:02d}.decision.json');o=read(folder/f'gw{gw:02d}.settlement.json')
                    assert d['outcomes_read'] is False
                    assert len(d['solver_calls'])<=40
                    assert all(r.get('nodes') is None or r['nodes']<=16 for r in d['solver_calls'])
                    assert digest(mod.clean(current))==digest(d['state_before'])
                    key=(state['season'],gw)
                    if key not in inputs:
                        p=pd.read_csv(C/key[0]/f'gw{gw:02d}'/'pool.csv.gz')
                        if 'metadata_complete' in p:p=p[p.metadata_complete].copy()
                        for c in ['pid','pos','market']:p[c]=p[c].astype(int)
                        inputs[key]=p
                    pool=inputs[key];choice=d['choice']
                    if 'prices' in choice:choice['prices']={int(k):v for k,v in choice['prices'].items()}
                    current,legal=adapter.engine.apply_decision(current,choice,pool.to_dict('records'),gw)
                    assert digest(mod.clean(current))==digest(d['state_after'])
                    outcomes={int(x['code']):x for x in o['outcomes']}
                    fresh={int(x['code']):x for x in env.outcomes(state['season'],gw,legal,pool)}
                    assert set(fresh)==set(outcomes)
                    for i in legal['squad']:
                        assert all(fresh[i][k]==outcomes[i][k] for k in ['points','appeared','known'])
                    assert all(outcomes[i]['known'] for i in legal['squad'])
                    result=adapter.engine.settle(legal['starters'],legal['bench'],legal['captain'],legal['vice'],dict(zip(pool.pid,pool.pos)),{i:outcomes[i]['points'] for i in legal['squad']},{i:outcomes[i]['appeared'] for i in legal['squad']},legal['chip'])
                    assert result['gross']-4*legal['paid']==o['net']
                    total+=o['net'];hits+=4*legal['paid'];count+=1
                summary=read(folder/'summary.json');assert summary['net_points']==total and summary['hits']==hits
                if state['source_policy']=='same_proposals_unlearned_v1' and arm=='benchmark' and manager=='proposal_ranker':
                    original=R/'reports/season_manager_2026_10_15/episodes'/('eval__'+state['season']+'__same_proposals_unlearned_v1')
                    expected=sum(read(original/f'gw{g:02d}.json')['net_points'] for g in range(state['round'],39))
                    assert expected==total,'Archived same-policy continuation mismatch'
                    parity.append(dict(state_id=state['id'],expected=expected,actual=total))
                pairs.append(summary)
    assert len(pairs)==96 and count==2136
    atomic_json(P/'verification.json',dict(status='passed',episodes=96,decisions=count,identical_initial_states=True,
        legal_choices_replayed=True,settlements_recomputed=True,outcomes_reloaded_from_source=True,causal_fit_clocks=True,forecast_hashes=True,
        preserved_source_hashes=True,archived_same_policy_parity=parity,independent_test_seasons=False,rank_claim=False))
    print('VERIFIED',len(pairs),count)

if __name__=='__main__':globals()[sys.argv[1]]()
