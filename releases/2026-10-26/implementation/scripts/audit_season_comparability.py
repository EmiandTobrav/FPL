"""Independent read-only audit of season coverage, labels, pools and saved play.
No model fitting, final-calendar substitution or parameter selection here.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import sys,json,collections,hashlib,difflib
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json,verify_files
from model_lab.simulation import backend
from scripts.common_season_comparison import qualify
P=R/'reports/season_comparability_audit_2026_10_25';OLD=R/'reports/common_season_comparison_2026_10_25';NEW=R/'reports/component_confirmation_2026_10_25_v2'
SEASONS=['2023-24','2024-25','2025-26'];ARMS=['component','operational_fixed'];KEY=['season','round','code'];B='fixture_full_h3_adaptive_tc_harmonized_causal_v1'
def read(p):return json.loads(p.read_text())
def cache(s):return R/('reports/fpl_simulator_2026_10_13/cache_manager' if s=='2025-26' else 'reports/fpl_improvement_2026_10_14/cache')/s
def folder(s,a):return NEW/'manager'/f'{a}_adaptive_chips' if s=='2025-26' else OLD/'manager'/f'{s}_{a}'
def frame(s):
    d=pd.read_pickle((NEW if s=='2025-26' else OLD)/'pool_features.pkl');return d[d.season.eq(s)].copy()
def collect():
    P.mkdir(exist_ok=True);assert not (P/'audit.json').exists();deps={};paths=[Path(__file__),R/'model_lab/vendor/fpl_rules_v1/engine.py',R/'model_lab/vendor/fpl_rules_v1/controlled_policy_v1.py',R/'scripts/common_season_inputs.py',R/'scripts/component_confirmation_inputs.py',R/'scripts/common_season_comparison.py',R/'scripts/component_confirmation_v2.py',R/'overview/ACTIVE_TEAM_BENCHMARK.json',OLD/'result.json',NEW/'result.json']
    source=R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz';master=pd.read_csv(source,low_memory=False);m=master[master.season.isin(SEASONS)].copy();assert not m.duplicated(['season','fixture','code']).any();paths +=[source,R/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz',R/'datasets/fpl_master_enriched_v5/player_matches.csv.xz',R/'datasets/fpl_common_training_v1/schema.json',R/'datasets/fpl_common_training_v1/manifest.json']
    # Recompute published target arithmetic, retaining explicit event revisions.
    year=m.season.str[:4].astype(int);expected=m.native_total_points-m.original_bonus+m.target_bonus+3*(m.target_assists-m.native_assists)+m.target_defcon_points.where(year<2025,0)+4*m.native_goals_scored.where(m.position.eq('GK')&(year<2024),0)
    revisions=R/'reports/full_rescoring_2026_10_12/results/event_revision_review.csv';paths.append(revisions);events=pd.read_csv(revisions);revision_rows=[]
    for e in events[events.season.isin(SEASONS)].itertuples():
        scorer=m.season.eq(e.season)&m.fixture.eq(e.fixture)&m.code.eq(e.scorer_code);former=m.season.eq(e.season)&m.fixture.eq(e.fixture)&m.code.eq(e.former_own_goal_code);assert scorer.sum()==former.sum()==1;expected.loc[scorer]+=m.loc[scorer,'position'].map(dict(GK=10,DEF=6,MID=5,FWD=4));expected.loc[former]+=2;revision_rows.append(dict(season=e.season,fixture=e.fixture,scorer=e.scorer_code,former_own_goal=e.former_own_goal_code,provenance='previously recorded event revision; not newly adjudicated'))
    np.testing.assert_allclose(expected,m.target_total_points,atol=0,rtol=0);rank=m.groupby(['season','fixture']).target_bps.rank(method='min',ascending=False);bonus=(4-rank).clip(0,3);np.testing.assert_allclose(bonus,m.target_bonus,atol=0,rtol=0)
    aggregates=m.groupby(KEY).agg(points=('target_total_points',lambda v:v.sum(min_count=len(v))),native=('native_total_points',lambda v:v.sum(min_count=len(v))),minutes=('native_minutes','sum'),yellow=('native_yellow_cards','sum'),red=('native_red_cards','sum'));rounds=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz');comparison=rounds[rounds.season.isin(SEASONS)].merge(aggregates.reset_index(),on=KEY,validate='one_to_one');np.testing.assert_allclose(comparison.target_total_points,comparison.points,rtol=0,atol=0)
    pd.DataFrame(revision_rows).to_csv(P/'recorded_event_revisions.csv',index=False);league=[];calendars=[];markets=[];terms=[];players=[];weekly=[];chips=[];calibration=[];quality=[];paths+=[OLD/'pool_features.pkl',NEW/'pool_features.pkl'];schema=read(R/'datasets/fpl_common_training_v1/schema.json');all_views={s:frame(s) for s in SEASONS}
    for directory,flag in [('fpl_availability_all_seasons_v1','av_source_known'),('fpl_set_piece_roles_v1','sp_source_known')]:
        path=R/'datasets'/directory/'player_round_context.csv.xz';paths.append(path);q=pd.read_csv(path,usecols=['season',flag]);quality.extend(dict(season=s,group=flag,known_share=float(q.loc[q.season.eq(s),flag].mean())) for s in SEASONS)
    for s in SEASONS:
        q=m[m.season.eq(s)];v=all_views[s];assert all(c in v for c in schema['features']);actual=q[['fixture','round','historical_team']].drop_duplicates();actual.historical_team=actual.historical_team.replace({'Ipswich Town':'Ipswich'});counts=actual.groupby(['round','historical_team']).fixture.nunique();names=q.groupby('code').name.last();g=q.groupby('code').target_total_points.sum().sort_values(ascending=False)
        fixture_path=R/'FPL_training_dataset/research/current/project/data'/f'{s}_fixtures.csv.gz';team_path=fixture_path.with_name(s+'_teams.csv.gz');paths += [fixture_path,team_path];fixtures=pd.read_csv(fixture_path);teams=pd.read_csv(team_path);assert len(fixtures)==fixtures.id.nunique()==380 and fixtures.finished.eq(True).all() and set(fixtures.id)==set(q.fixture);assert q['round'].eq(q.fixture.map(fixtures.set_index('id').event)).all();assert pd.to_datetime(q.fixture_kickoff_time,utc=True).eq(pd.to_datetime(q.fixture.map(fixtures.set_index('id').kickoff_time),utc=True)).all();assert pd.concat([fixtures.team_h,fixtures.team_a]).value_counts().eq(38).all();assert q.native_goals_scored.sum()+q.native_own_goals.sum()==fixtures[['team_h_score','team_a_score']].sum().sum()
        league.append(dict(season=s,matches=380,rounds=q['round'].nunique(),players=q.code.nunique(),native_minutes=q.native_minutes.sum(),goals=q.native_goals_scored.sum(),native_points=q.native_total_points.sum(),target_points=q.target_total_points.sum(),defcon_points=q.target_defcon_points.sum(),top10_points=g.head(10).sum(),top20_points=g.head(20).sum(),top50_points=g.head(50).sum(),top100_points=g.head(100).sum(),pool_rows=len(v),calendar_known_share=float(v.u_count_0.notna().mean()),calendar_origins_with_coverage=int(v[v.u_count_0.notna()]['round'].nunique()),quality_flagged_share=float(q.quality_flagged_for_sensitivity.mean())))
        for group,cols in schema['feature_groups'].items():quality.append(dict(season=s,group=group,known_share=float(v[cols].notna().mean().mean())))
        for gw in range(1,39):
            c=cache(s)/f'gw{gw:02d}';pool=pd.read_csv(c/'pool.csv.gz');snap=read(c/'snapshot_audit.json');man=read(c/'manifest.json');view=v[v['round'].eq(gw)];at=pd.Timestamp(view.forecast_at.iloc[0]);meta_ages=[]
            for field in ['price','position','club']:
                dates=pd.to_datetime(pool[field+'_available_at'],utc=True);assert dates.lt(at).all();meta_ages.append((at-dates).dt.total_seconds()/86400)
            assert len(pool)==len(view);assert (pool.price_tenths==pool.market).all() and np.isclose(pool.price*10,pool.price_tenths).all();a=read(c/(B+'.json'));paths += [c/'pool.csv.gz',c/'manifest.json',c/'snapshot_audit.json',c/(B+'.json')]
            pool_club_count=pool.club.map(lambda club:counts.get((gw,club),0));known=view.u_count_0.notna();actual_for_view=view.code.map(pool.set_index('code').club).map(lambda club:counts.get((gw,club),0));mismatch=known&view.u_count_0.ne(actual_for_view)
            calendars.append(dict(season=s,round=gw,players=len(view),known=int(known.sum()),known_share=float(known.mean()),false_blank_after_the_fact=int((known&view.u_count_0.eq(0)&actual_for_view.gt(0)).sum()),known_vs_actual_mismatch=int(mismatch.sum()),reference_calendar_status=a.get('calendar_status'),reference_calendar_age_days=a.get('calendar_age_days')))
            markets.append(dict(season=s,round=gw,players=len(pool),buyable=int(pool.can_buy.sum()),median_price=float(pool.price_tenths.median()),median_price_age_days=float(meta_ages[0].median()),maximum_price_age_days=float(meta_ages[0].max()),preseason_source_age_days=snap.get('preseason_evidence',{}).get('age_days_at_gw1'),salah_price=int(pool.set_index('code').loc[118748,'price_tenths']) if 118748 in set(pool.code) else None))
        for arm in ARMS:
            f=folder(s,arm);state=None;contribution=collections.Counter();captains=collections.Counter();total=dict(base=0.,captain_bonus=0.,hits=0.,net=0.,native_net=0.,direct_chip_points=0.);n_blanks=0;mod,adapter=backend(16,40);state=adapter.engine.initial_state()
            for gw in range(1,39):
                dp=f/f'gw{gw:02d}.decision.json';sp=f/f'gw{gw:02d}.settlement.json';paths +=[dp,sp];decision=read(dp);saved=read(sp);at=pd.Timestamp(decision['forecast_at']);pool=qualify(pd.read_csv(cache(s)/f'gw{gw:02d}/pool.csv.gz'),s,at);assert mod.clean(state)==decision['state_before'];choice=decision['choice'];choice['prices']={int(k):v for k,v in choice['prices'].items()};state,legal=adapter.engine.apply_decision(state,choice,pool.to_dict('records'),gw);assert mod.clean(state)==decision['state_after'];pts={};native={};active={}
                for row in saved['outcomes']:
                    code=int(row['code']);key=(s,gw,code)
                    if key in aggregates.index:
                        z=aggregates.loc[key];pts[code]=float(z.points);native[code]=float(z.native);active[code]=bool(z.minutes>0 or z.yellow>0 or z.red>0)
                    else:
                        assert row['blank_derived'] and row['settlement_source']=='complete_fixture_inventory_blank';assert counts.get((gw,row['blank_club']),0)==0;pts[code]=native[code]=0.;active[code]=False;n_blanks+=1
                    assert pts[code]==row['points'] and active[code]==row['appeared']
                r=adapter.engine.settle(legal['starters'],legal['bench'],legal['captain'],legal['vice'],dict(zip(pool.pid,pool.pos)),pts,active,legal['chip']);assert mod.clean(r)==saved['settlement'];net=r['gross']-4*legal['paid'];assert net==saved['net'];nr=adapter.engine.settle(legal['starters'],legal['bench'],legal['captain'],legal['vice'],dict(zip(pool.pid,pool.pos)),native,active,legal['chip']);native_net=nr['gross']-4*legal['paid'];total['native_net']+=native_net;total['net']+=net;total['hits']+=4*legal['paid']
                for k in ['base','captain_bonus','direct_chip_points']:total[k]+=r[k]
                contribution.update({int(k):val for k,val in r['contributions'].items()});captains[r['effective_captain']]+=1;weekly.append(dict(season=s,arm=arm,round=gw,net=net,base=r['base'],captain_bonus=r['captain_bonus'],hits=4*legal['paid'],native_net=native_net,chip=legal['chip'],direct_chip_points=r['direct_chip_points'],counted_nonparticipants=sum(not active[i] for i in r['counted'])))
                if legal['chip']:chips.append(dict(season=s,arm=arm,round=gw,chip=legal['chip'],net=net,direct_chip_points=r['direct_chip_points']))
            assert collections.Counter(x['chip'] for x in chips if x['season']==s and x['arm']==arm)=={k:2 for k in adapter.engine.CHIPS};summary=read(f/'summary.json');assert total['net']==summary['net'];terms.append(dict(season=s,arm=arm,blank_outcomes_verified=n_blanks,**total));players.extend(dict(season=s,arm=arm,code=code,name=names.get(code,str(code)),contribution=val,captain_rounds=captains[code]) for code,val in contribution.items())
            print('INDEPENDENTLY REPLAYED',s,arm,total['net'],flush=True)
        if s=='2025-26':
            files=sorted((NEW/'reference_models').glob('gw*.json'))
            for f in files:
                a=read(f);payload=hashlib.sha256(json.dumps(a['models'],sort_keys=True).encode()).hexdigest();calibration.append(dict(season=s,refit_round=a['refit_round'],total_head_training_rows=sum(v['rows'] for v in a['audits']),unique_coefficient_payload=payload,current_season_training_rows=0));paths.append(f)
        else:
            data=pd.read_pickle(R/'reports/season_role_gate_2026_10_24/data.pkl');paths.append(R/'reports/season_role_gate_2026_10_24/data.pkl')
            for gw in range(1,39,4):
                at=all_views[s].loc[all_views[s]['round'].eq(gw),'forecast_at'].iloc[0];tr=data[data.can_buy&data.forecast_at.lt(at)&data.label_at_0.lt(at)&data.y_0.notna()];files=sorted((R/'reports/season_role_gate_2026_10_24/models').glob(f'{s}_gw{gw:02d}_*_fixed.json'));payload=hashlib.sha256(''.join(sha(f) for f in files).encode()).hexdigest();calibration.append(dict(season=s,refit_round=gw,total_head_training_rows=None,unique_coefficient_payload=payload,current_season_training_rows=int(tr.season.eq(s).sum())));paths+=files
    for name,rows in [('league',league),('calendar',calendars),('markets',markets),('score_decomposition',terms),('player_contributions',players),('rounds',weekly),('chips',chips),('calibration_updates',calibration),('feature_coverage',quality)]:pd.DataFrame(rows).to_csv(P/(name+'.csv'),index=False)
    a=(R/'scripts/common_season_inputs.py').read_text().splitlines();b=(R/'scripts/component_confirmation_inputs.py').read_text().splitlines();diff=list(difflib.unified_diff(a,b));assert sum(x.startswith('+') and not x.startswith('+++') for x in diff)==3;(P/'builder_difference.txt').write_text('\n'.join(diff)+'\n')
    for path in set(paths):deps[str(path.relative_to(R))]=sha(path)
    atomic_json(P/'input_manifest.json',dict(files=deps));atomic_json(P/'audit.json',dict(passed=True,scope='arithmetic,inventory,source and recipe audit; does not establish causal calendar effect',season_matches_checked=1140,player_match_point_and_bonus_rows_recalculated=len(m),player_round_sums_checked=len(comparison),manager_decisions_independently_replayed=228,common_engine_and_scoring_standard=True,all_selected_outcomes_known_or_verified_blank=True,feature_builder_diff_only_paths_and_seasons=True,reference_current_season_update_policy_differs=True,production_changed=False));print('AUDIT COMPLETE',flush=True)
if __name__=='__main__':collect()
