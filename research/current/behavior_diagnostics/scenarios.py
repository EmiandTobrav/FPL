from common import *
from upside.features import load_history,prediction_rows
import time

def scenarios(p,gw):
    """All scenario membership uses pre-deadline features, never actual outcomes."""
    groups={'all':np.full(len(p),'all',dtype=object)}
    groups['position']=p.pos.map({1:'GK',2:'DEF',3:'MID',4:'FWD'}).to_numpy()
    cheap=p.pos.map({1:45,2:50,3:60,4:60});premium=p.pos.map({1:55,2:60,3:90,4:90})
    groups['price']=np.select([p.market<=cheap,p.market>=premium],['cheap','premium'],default='standard')
    groups['minutes6']=np.select([p.minutes_m6.isna(),p.minutes_m6<30,p.minutes_m6<70],['missing','low','rotation'],default='regular')
    change=p.minutes_m6-p.minutes_m12
    groups['minutes_change']=np.select([change.isna(),change<=-15,change>=15],['missing','falling','rising'],default='stable')
    groups['history']=np.where(p.n_history<12,'short','established')
    groups['fixtures']=np.where(p['count']>=2,'multiple','single')
    groups['venue']=np.select([p['count']>=2,p.home==1,p.home==0],['multiple','home','away'],default='missing')
    for category,column in [('opponent_defence','opp_ga'),('opponent_attack','opp_gf'),('team_attack','team_gf')]:
        lower,upper=('strong','weak') if category=='opponent_defence' else ('weak','strong')
        groups[category]=np.select([p[column].isna(),p[column]<=1,p[column]>1.6],['missing',lower,upper],default='middle')
    groups['elo']=np.select([p.elo_diff.isna(),p.elo_diff < -100,p.elo_diff>100],['missing','underdog','favourite'],default='balanced')
    groups['season_phase']=np.full(len(p),'early' if gw<=12 else 'middle' if gw<=24 else 'late',dtype=object)
    groups['refresh_age']=np.full(len(p),str((gw-5)%4),dtype=object)
    return groups

def error_sums(y,score,mask):
    e=score[mask]-y[mask]
    return dict(n=len(e),err=float(e.sum()),ae=float(np.abs(e).sum()),se=float((e*e).sum()),pred=float(score[mask].sum()),actual=float(y[mask].sum()))

def main():
    from upside.summarize import ranked_metrics
    t=time.time();d,fixtures,th=load_history();metrics=[];audits=[]
    for s in SEASONS:
        games=games_for(s);inputs=[]
        for gw in range(5,39):
            g=games[gw];batch,p=prediction_rows(d,fixtures,th,g,s,gw)
            assert np.array_equal(p.index,g['frame'].pid)
            for col in ['home','opp_ga','opp_gf','elo_diff']:
                p[col]=batch.groupby('_row')[col].mean().reindex(np.arange(len(p))).to_numpy() if len(batch) else np.nan
            p['count']=g['count'];y=np.array([g['actual'].get(int(i),0) for i in p.index]);ids=p.index.to_numpy();scheduled=p['count'].to_numpy()>0
            scores={m:experiment.xp_for(g,m) for m in PRED_MODELS};ref=scores[REF]
            relevant=np.zeros(len(p),bool);eligible=np.flatnonzero(scheduled);relevant[eligible[np.lexsort((ids[eligible],-ref[eligible]))[:60]]]=True
            inputs.append(p[['pos','market','minutes_m6','minutes_m12','n_history','count','home','opp_ga','opp_gf','team_gf','elo_diff']].assign(season=s,gw=gw,cutoff=g['cutoff'],actual=y,reference_top60=relevant).reset_index())
            groups=scenarios(p,gw)
            for dimension,labels in groups.items():
                for label in np.unique(labels):
                    mask=scheduled&(labels==label);k=20 if dimension=='all' else 10
                    if not mask.any():continue
                    for m,score in scores.items():
                        rank=ranked_metrics(y[mask],score[mask],ids[mask],k) if mask.sum()>=k else dict(precision=np.nan,mean_points=np.nan,ndcg=np.nan)
                        row=dict(season=s,gw=gw,model=m,dimension=dimension,scenario=label,**error_sums(y,score,mask),top_precision=rank['precision'],top_points=rank['mean_points'],ndcg=rank['ndcg'],rank_round=int(mask.sum()>=k))
                        row.update({'relevant_'+key:val for key,val in error_sums(y,score,mask&relevant).items()});metrics.append(row)
            audits.append(dict(season=s,gw=gw,cutoff=g['cutoff'],latest_feature_outcome=str(d.loc[d.available<pd.Timestamp(g['cutoff']),'available'].max()),rows=int(scheduled.sum()),relevant_rows=int(relevant.sum())))
        pd.concat(inputs,ignore_index=True).to_csv(OUT/f'scenario_inputs_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0});print('FEATURES',s,round(time.time()-t),flush=True)
    pd.DataFrame(audits).to_csv(OUT/'feature_audit.csv',index=False)
    w=pd.DataFrame(metrics);w.to_csv(OUT/'scenario_weekly.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    keys=['season','model','dimension','scenario'];sums=['n','err','ae','se','pred','actual','relevant_n','relevant_err','relevant_ae','relevant_se','relevant_pred','relevant_actual','rank_round']
    per=w.groupby(keys)[sums].sum().join(w.groupby(keys)[['top_precision','top_points','ndcg']].mean()).reset_index()
    for prefix in ['','relevant_']:
        n=per[prefix+'n'].replace(0,np.nan)
        for name,col in [('bias','err'),('mae','ae'),('mean_prediction','pred'),('mean_actual','actual')]:per[prefix+name]=per[prefix+col]/n
        per[prefix+'rmse']=np.sqrt(per[prefix+'se']/n)
    per.to_csv(OUT/'scenario_seasons.csv',index=False)
    met=['bias','mae','rmse','mean_prediction','mean_actual','relevant_bias','relevant_mae','relevant_rmse','top_precision','top_points','ndcg']
    summary=per.groupby(['model','dimension','scenario'])[met].mean().join(per.groupby(['model','dimension','scenario']).agg(seasons=('season','nunique'),rows=('n','sum'),rank_rounds=('rank_round','sum'),relevant_rows=('relevant_n','sum'))).reset_index();summary.to_csv(OUT/'scenario_summary.csv',index=False)
    comparisons=list(dict.fromkeys([tuple(x) for x in COMPARISONS]+[(m,REF) for m in PRED_MODELS if m!=REF]+[('hgb_refresh','hgb'),('rich_refresh','rich_frozen')]))
    pairs=[]
    for a,b in comparisons:
        z=per[per.model==a].merge(per[per.model==b],on=['season','dimension','scenario'],suffixes=('_a','_b'),validate='one_to_one')
        for metric in ['rmse','relevant_rmse','mae','bias','top_points','top_precision','ndcg']:
            q=z[['season','dimension','scenario']].copy();q['comparison']=a+' - '+b;q['metric']=metric;q['difference']=z[metric+'_a']-z[metric+'_b'];q['rank_rounds']=z.rank_round_a;q['rows']=z.n_a;q['relevant_rows']=z.relevant_n_a
            # Positive improvement always means better, except bias which is left signed.
            q['improvement']=(-1 if metric in ['rmse','relevant_rmse','mae'] else 1)*q.difference;pairs.append(q)
    pairs=pd.concat(pairs,ignore_index=True);pairs.to_csv(OUT/'scenario_paired_seasons.csv',index=False)
    psummary=pairs.groupby(['comparison','dimension','scenario','metric']).agg(mean_difference=('difference','mean'),mean_improvement=('improvement','mean'),positive_seasons=('improvement',lambda x:int((x>0).sum())),seasons=('difference','count'),min_difference=('difference','min'),max_difference=('difference','max'),min_rank_rounds=('rank_rounds','min'),min_rows=('rows','min'),min_relevant_rows=('relevant_rows','min')).reset_index()
    psummary['recurring_rank_pattern']=(psummary.metric.isin(['top_points','top_precision','ndcg']))&(psummary.seasons>=5)&(psummary.positive_seasons>=5)&(psummary.min_rank_rounds>=12)
    psummary.to_csv(OUT/'scenario_paired_summary.csv',index=False)
    checks=dict(player_rounds=int(pd.DataFrame(audits).rows.sum()),forecast_models=len(PRED_MODELS),scenario_weekly_rows=len(w),pre_deadline_membership=True,common_reference_top60=True,blank_round_players_excluded=True,no_new_fitted_models=True)
    (OUT/'scenario_checks.json').write_text(json.dumps(checks,indent=2));print(checks)
if __name__=='__main__':main()
