"""Audit source availability without promoting omitted counters to observed zeros."""
from pathlib import Path
from functools import lru_cache
import sys,json,hashlib,math,ast,gzip
import pandas as pd
P=Path(__file__).resolve().parent
S=P.parent
sys.path.insert(0,str(S/'keeper_recovery'))
from recover import norm,name_match,team
import recover
recover.norm=lru_cache(None)(norm)

FIELDS={
 'minsPlayed':'mins_played','goals':'goals','attPenGoal':'att_pen_goal',
 'goalAssist':'goal_assist','saves':'saves','savedIbox':'saved_ibox',
 'bigChanceSaves':'big_chance_saves','penaltySave':'penalty_save',
 'totalClearance':'total_clearance','outfielderBlock':'outfielder_block',
 'interception':'interception','ballRecovery':'ball_recovery',
 'accurateCrossNocorner':'accurate_cross_nocorner','accurateFreekickCross':'accurate_freekick_cross',
 'bigChanceCreated':'big_chance_created','totalAttAssist':'total_att_assist',
 'wonTackle':'won_tackle','wonContest':'won_contest','winningGoal':'winning_goal',
 'clearanceOffLine':'clearance_off_line','wasFouled':'was_fouled',
 'ontargetScoringAtt':'ontarget_scoring_att','totalPass':'total_pass',
 'accuratePass':'accurate_pass','penaltyConceded':'penalty_conceded',
 'bigChanceMissed':'big_chance_missed','errorLeadToGoal':'error_lead_to_goal',
 'errorLeadToShot':'error_lead_to_shot','fouls':'fouls',
 'totalOffside':'total_offside','shotOffTarget':'shot_off_target',
 'cleanSheet':'clean_sheet','goalsConceded':'goals_conceded',
 'yellowCard':'yellow_card','redCard':'red_card','ownGoals':'own_goals'}
ASSIST_FIELDS=['goalAssist','goalAssistIntentional','goalAssistOpenplay','goalAssistDeadball',
 'goalAssistSetplay','assistHandballWon','assistOwnGoal','assistPenaltyWon',
 'assistFreeKickWon','assistAttemptSaved','assistPassLost','assistPost','assistBlockedShot','secondGoalAssist']

def controls():
    parts=[]
    for folder in ['primary_player_counts','primary_player_counts_gw2']:
        parts.extend(pd.read_csv(f) for f in sorted((S/'primary_data'/folder).glob('part-*.csv')))
    parts.append(pd.read_csv(S/'acquisition_followup/collection/observations.csv'))
    frame=pd.concat(parts,ignore_index=True)
    assert not frame.duplicated(['season','fixture','code']).any()
    return frame


def map_targets(stats,fixtures,population):
    lookup={}
    for r in fixtures.to_dict('records'):
        key=(r['season'],str(r['match_date'])[:10],team(r['home_team']),team(r['away_team']))
        assert key not in lookup
        lookup[key]=r
    bymatch={m:g.to_dict('records') for m,g in stats.groupby('match_id')}
    rows=[]
    for season,group in population.groupby('season'):
        players=(pd.DataFrame(json.loads(gzip.decompress((P/'inputs/current_bootstrap.json.gz').read_bytes()))['elements']) if season=='2026-27' else pd.read_csv(S.parent/f'project/data/{season}_players.csv.gz')).set_index('code')
        ff=(pd.DataFrame(json.loads(gzip.decompress((P/'inputs/current_fixtures.json.gz').read_bytes()))) if season=='2026-27' else pd.read_csv(S.parent/f'project/data/{season}_fixtures.csv.gz')).set_index('id')
        teams=pd.read_csv(S.parent/f'project/data/{season}_teams.csv.gz').set_index('id').name.to_dict()
        for fixture,g in group.groupby('fixture'):
            f=ff.loc[fixture]
            key=(f'{season[:4]}-{int(season[:4])+1}',str(f.kickoff_time)[:10],team(teams[f.team_h]),team(teams[f.team_a]))
            match=lookup.get(key)
            if match:
                assert int(match['home_score'])==int(f.team_h_score) and int(match['away_score'])==int(f.team_a_score), key
            fs=ast.literal_eval(f['stats']) if isinstance(f['stats'],str) else f['stats']
            fs={x['identifier']:{int(z['element']):z['value'] for side in ('h','a') for z in x[side]} for x in fs}
            for row in g.to_dict('records'):
                pl=players.loc[row['code']]
                if isinstance(pl,pd.DataFrame):raise ValueError('Duplicate FPL code')
                cand=[]
                if match:
                    for pr in bymatch.get(match['match_id'],[]):
                        score=name_match(pl,pr)
                        if norm(row['name'])==norm(pr['player_name']) or norm(str(pl.first_name)+' '+str(pl.second_name))==norm(pr['player_name']):score=3
                        if score:cand.append((score,pr))
                if cand:
                    best=max(x[0] for x in cand);cand=[x[1] for x in cand if x[0]==best]
                pr=cand[0] if len(cand)==1 else None
                out={**row,'element':int(pl.id),'position':{1:'GK',2:'DEF',3:'MID',4:'FWD'}[int(pl.element_type)],
                     'fixture_code':int(f.code),'date':key[1],'home':teams[f.team_h],'away':teams[f.team_a],
                     'match_id':match['match_id'] if match else '',
                     'mapping_status':'matched' if pr else ('missing_match' if not match else f'name_candidates_{len(cand)}')}
                for field in ['assists','bps','bonus','goals_scored']:
                    out['fpl_'+field]=fs[field].get(int(pl.id),0) if field in fs else None
                if pr:
                    out.update({k:v for k,v in pr.items() if k not in ['season','position','match_id']})
                    if pd.notna(row.get('frozen_minutes')):out['minutes_difference']=pr['minsPlayed']-row['frozen_minutes']
                rows.append(out)
        print('mapped',season,len(group),flush=True)
    # Reuse only unanimous identity anchors established in other actual matches.
    anchors={}
    for r in rows:
        if r['mapping_status']=='matched':anchors.setdefault(r['code'],set()).add(r['player_id'])
    for r in rows:
        if r['mapping_status'] in ('matched','missing_match'):continue
        ids=anchors.get(r['code'],set())
        if len(ids)!=1:continue
        candidates=[x for x in bymatch.get(r['match_id'],[]) if x['player_id'] in ids]
        if len(candidates)!=1:continue
        pr=candidates[0]
        r.update({k:v for k,v in pr.items() if k not in ['season','position','match_id']})
        r['mapping_status']='matched';r['mapping_method']='unanimous_cross_match_identity'
        r['minutes_difference']=pr['minsPlayed']-r['frozen_minutes']
    frame=pd.DataFrame(rows)
    assert not frame.duplicated(['season','fixture','code']).any()
    mapped=frame[frame.mapping_status.eq('matched')]
    assert not mapped.duplicated(['match_id','player_id']).any()
    return frame



def apply_aliases(mapped,stats,aliases):
    """A reviewed ID may fill an unmatched row only in its verified fixture."""
    assert not aliases.code.duplicated().any()
    bykey=stats.set_index(['match_id','player_id'])
    assert bykey.index.is_unique
    out=mapped.copy()
    for a in aliases.to_dict('records'):
        for i,r in out[out.code.eq(a['code'])].iterrows():
            if r.mapping_status=='missing_match':continue
            if r.mapping_status=='matched':
                assert r.player_id==a['player_id']
                continue
            key=(r.match_id,a['player_id'])
            if key not in bykey.index:continue
            pr=bykey.loc[key]
            for k,v in pr.items():
                if k not in ['season','position','match_id']:out.loc[i,k]=v
            out.loc[i,'player_id']=a['player_id']
            out.loc[i,'mapping_status']='matched'
            out.loc[i,'mapping_method']='reviewed_name_alias'
            out.loc[i,'minutes_difference']=pr.minsPlayed-r.frozen_minutes
    assert not out[out.mapping_status.eq('matched')].duplicated(['match_id','player_id']).any()
    return out


def main():
    ctrl=pd.read_csv(P/'inputs/primary_controls.csv.gz') if (P/'inputs/primary_controls.csv.gz').exists() and '--prepare' not in sys.argv else controls()
    # Raw source projection is an intermediate. Committed per-season extracts
    # permit all later audits to replay without the 316 MB external asset.
    if not list((P/'inputs').glob('counts-*.csv.gz')) or '--prepare' in sys.argv:
        import pyarrow.parquet as pq
        stats=pd.read_parquet(P/'active_stats.parquet')
        fixtures=pq.read_table(S/'keeper_recovery/raw/opta_fixtures.parquet',filters=[('competition','=','EPL'),('season','in',[f'{y}-{y+1}' for y in range(2019,2027)])]).to_pandas()
        pop=[]
        for f in sorted((S/'data').glob('*/part-*.csv')):
            g=pd.read_csv(f);pop.append(g[['season','fixture','code','name','minutes_played']].rename(columns={'minutes_played':'frozen_minutes'}))
        pop=pd.concat(pop,ignore_index=True)
        cur=ctrl[ctrl.season.eq('2026-27')][['season','fixture','code','name','minutes']].rename(columns={'minutes':'frozen_minutes'})
        pop=pd.concat([pop,cur],ignore_index=True)
        mapped=apply_aliases(map_targets(stats,fixtures,pop),stats,pd.read_csv(P/'identity_aliases.csv'))
        (P/'inputs').mkdir(exist_ok=True)
        for season,g in mapped.groupby('season'):
            g.to_csv(P/f'inputs/counts-{season}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    else:
        mapped=pd.concat(pd.read_csv(f) for f in sorted((P/'inputs').glob('counts-*.csv.gz')))
    audit(mapped,ctrl)


def audit(mapped,ctrl):
    coverage=[]
    for season,g in mapped.groupby('season'):
        for field in list(dict.fromkeys([*FIELDS,*ASSIST_FIELDS])):
            v=g[field]
            coverage.append(dict(season=season,field=field,target_rows=len(g),mapped_rows=int(g.mapping_status.eq('matched').sum()),explicit_values=int(v.notna().sum()),explicit_zeros=int(v.eq(0).sum()),positive_values=int(v.gt(0).sum()),missing_values=int(v.isna().sum())))
    pd.DataFrame(coverage).to_csv(P/'field_coverage.csv',index=False)
    mapped[~mapped.mapping_status.eq('matched')].to_csv(P/'unmapped_observations.csv',index=False)
    mapped[mapped.minutes_difference.fillna(0).ne(0)][['season','fixture','code','name','frozen_minutes','minsPlayed','minutes_difference']].to_csv(P/'minute_disagreements.csv',index=False)
    join=ctrl.merge(mapped,on=['season','fixture','code'],suffixes=('_control',''),validate='one_to_one')
    comparison=[];disagreements=[]
    for scope,g in [('historical',join[join.season.ne('2026-27')]),('current',join[join.season.eq('2026-27')])]:
        for field,alias in FIELDS.items():
            a=g[field];b=g['pl_'+alias] if 'pl_'+alias in g else pd.Series(float('nan'),index=g.index)
            both=a.notna()&b.notna();one=a.notna()^b.notna()
            comparison.append(dict(scope=scope,field=field,rows=len(g),both_explicit=int(both.sum()),both_explicit_equal=int((both&a.eq(b)).sum()),one_omitted=int(one.sum()),both_omitted=int((a.isna()&b.isna()).sum()),sparse_zero_equal=int(a.fillna(0).eq(b.fillna(0)).sum())))
            bad=both&a.ne(b)|one
            for idx in g[bad].index:
                disagreements.append(dict(scope=scope,season=g.loc[idx,'season'],fixture=int(g.loc[idx,'fixture']),code=int(g.loc[idx,'code']),name=g.loc[idx,'name'],field=field,archive=a.loc[idx],primary=b.loc[idx],kind='explicit_conflict' if both.loc[idx] else 'omission_difference'))
    pd.DataFrame(comparison).to_csv(P/'primary_comparison.csv',index=False)
    pd.DataFrame(disagreements).to_csv(P/'primary_disagreements.csv',index=False)
    # Keep controls in a compact frozen file; no online query needed to replay.
    if not (P/'inputs/primary_controls.csv.gz').exists():
        (P/'inputs/primary_controls.csv.gz').write_bytes(gzip.compress(ctrl.to_csv(index=False).encode(),mtime=0))
    diagnostics(join)
    history=mapped[mapped.season.ne('2026-27')]
    result=dict(branch_base='dfa2ff30b36e33c4b16f5402d25af9337266af3f',historical_target_rows=len(history),historical_mapped_rows=int(history.mapping_status.eq('matched').sum()),historical_missing_matches=int(history[history.mapping_status.eq('missing_match')][['season','fixture']].drop_duplicates().shape[0]),historical_other_unmapped=int((~history.mapping_status.isin(['matched','missing_match'])).sum()),primary_controls=len(ctrl),historical_controls=int(ctrl.season.ne('2026-27').sum()),current_controls=int(ctrl.season.eq('2026-27').sum()),missing_policy='Absent counters remain NA. Sparse-zero calculations are diagnostics only.',full_historical_rescoring_ready=False,locked_labels_modified=False,cost_nok=0)
    (P/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


def diagnostics(join):
    sys.path.insert(0,str(S));from validate_bps import calculate,bonus
    current=join[join.season.eq('2026-27')].copy()
    scores=[];primary_scores=[]
    for _,r in current.iterrows():
        x=r.to_dict()
        x['position']=r.get('position_control',r['position'])
        primary_scores.append(calculate(x))
        # Preserve FPL roster/clean-sheet/assist inputs. Only replace mapped
        # provider counters for source-substitution diagnostic.
        for field,alias in FIELDS.items():x['pl_'+alias]=r[field]
        x['position']=r.get('position_control',r['position'])
        scores.append(calculate(x))
    current['primary_bps_diagnostic']=primary_scores
    current['archive_bps_diagnostic']=scores
    current['source_bps_difference']=current.archive_bps_diagnostic-current.primary_bps_diagnostic
    current['archive_bonus_diagnostic']=current.groupby('fixture').archive_bps_diagnostic.transform(bonus)
    current['bps_difference']=current.archive_bps_diagnostic-current.bps
    current[['season','fixture','code','name','bps','bonus','archive_bps_diagnostic','archive_bonus_diagnostic','bps_difference','primary_bps_diagnostic','source_bps_difference']].to_csv(P/'current_bps_diagnostic.csv',index=False)
    results=dict(rows=len(current),exact_bps=int(current.bps_difference.eq(0).sum()),exact_bonus=int(current.archive_bonus_diagnostic.eq(current.bonus).sum()),primary_exact_bps=int(current.primary_bps_diagnostic.eq(current.bps).sum()),archive_primary_bps_equal=int(current.source_bps_difference.eq(0).sum()),scope='Previously used GW1/GW2; not a new holdout. FPL assists retained. Omitted archive counters diagnostically zero, not observed historical zero.')
    (P/'current_bps_diagnostic.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
