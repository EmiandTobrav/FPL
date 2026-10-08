"""All-season canonical tables and nullable next-round targets; no legacy fallback."""
from pathlib import Path
import hashlib,json,lzma
import pandas as pd

P=Path(__file__).resolve().parent
T=P.parent
R=T.parent
K=['season','fixture','code']
RK=['season','round','code']
VERSION='fpl_2026_27_canonical_v1_partial'
TARGETS=['total_points_2026_27','bps_2026_27','bonus_2026_27','assists_2026_27','defcon_points_2026_27']
STATS=['minutes','goals_scored','assists','clean_sheets','goals_conceded','own_goals',
       'penalties_saved','penalties_missed','yellow_cards','red_cards','saves','bonus','bps',
       'total_points','clearances_blocks_interceptions','recoveries','tackles','defensive_contribution',
       'starts','expected_goals','expected_assists','expected_goal_involvements','expected_goals_conceded']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(df,path):
    raw=df.to_csv(index=False,lineterminator='\n').encode()
    path.write_bytes(lzma.compress(raw) if path.suffix=='.xz' else raw)

def strict_sum(grouped,field,size):
    value=grouped[field].sum(min_count=1)
    return value.where(grouped[field].count().eq(size))

def horizon_targets(rounds,horizons=(1,3,6)):
    """Labels for rounds after the anchor; missing rounds never become blank zeros."""
    if rounds.duplicated(RK).any():raise ValueError('Duplicate round key')
    result=rounds[RK].copy()
    indexed=rounds.set_index(RK)
    for horizon in horizons:
        values=[]
        for offset in range(1,horizon+1):
            keys=pd.MultiIndex.from_arrays([result.season,result['round']+offset,result.code],names=RK)
            candidate=indexed.reindex(keys)
            values.append(pd.Series(candidate.total_points_2026_27.where(candidate.scoring_qualified.eq(True)).to_numpy(),index=result.index))
        slots=pd.concat(values,axis=1)
        result[f'target_points_next_{horizon}_rounds']=slots.sum(axis=1,min_count=horizon)
        result[f'target_next_{horizon}_qualified']=slots.notna().all(axis=1)
    result['anchor_is_completed_round']=True
    result['deadline_eligible_universe_qualified']=False
    result['training_ready']=False
    return result

def main():
    out=P/'results';out.mkdir(parents=True,exist_ok=True)
    hashes={}
    def csv(path):
        hashes[str(path.relative_to(R))]=sha(path)
        return pd.read_csv(path,low_memory=False)
    def js(path):
        hashes[str(path.relative_to(R))]=sha(path)
        return json.loads(path.read_text())
    hpath=T/'scoring/results/historical_inventory.csv.xz'
    hmanifest=js(T/'scoring/results/manifest.json')
    if sha(hpath)!=hmanifest['output_sha256'][hpath.name]:raise ValueError('Historical inventory changed')
    hist=csv(hpath).copy()
    source=csv(T/'scoring/season_2025/results/player_matches.csv.xz')
    sm=js(T/'scoring/season_2025/results/manifest.json')
    if sha(T/'scoring/season_2025/results/player_matches.csv.xz')!=sm['output_sha256']['player_matches.csv.xz']:
        raise ValueError('Qualified scoring view changed')
    hist['scoring_qualified']=False
    hist['label_status']='historical_scoring_unqualified'
    hist['points_version']='unqualified_original_fpl_only'
    for field in TARGETS:hist[field]=float('nan')
    hist['original_starts']=hist.starts
    for field in ['times_tackled','saves_inside_box','saves_outside_box','big_chance_saves']:
        hist[field]=float('nan');hist[field+'_source']=None
    hi=hist.set_index(K)
    si=source.set_index(K)
    for field in TARGETS+['scoring_qualified','label_status','points_version','times_tackled',
        'saves_inside_box','saves_outside_box','big_chance_saves','times_tackled_source',
        'saves_inside_box_source','saves_outside_box_source','big_chance_saves_source']:
        hi.loc[si.index,field]=si[field]
    hist=hi.reset_index()
    starts=csv(T/'lineups/conservation/starts_qualified.csv.xz')
    starts_index=starts.set_index(K)
    if starts_index.index.duplicated().any() or not starts.starts_value_qualified.all():
        raise ValueError('Historical start qualification incomplete')
    keys=pd.MultiIndex.from_frame(hist[K])
    hist['starts']=starts_index.starts_qualified.reindex(keys).to_numpy()
    hist['starts_quality']=starts_index.starts_quality.reindex(keys).to_numpy()
    if hist.starts.isna().any():raise ValueError('Canonical start merge dropped history')
    xg=csv(T/'fpl_history_2022/reconciliation/expected_statistics_qualified.csv.xz').set_index(K)
    for field in [x for x in STATS if x.startswith('expected_')]:
        hist[field+'_original']=hist[field]
        hist[field+'_quality']='native_fpl_definition_not_qualified'
        index=hist.set_index(K)
        index.loc[xg.index,field]=xg[field+'_qualified']
        index.loc[xg.index,field+'_quality']=xg[field+'_quality']
        hist=index.reset_index()
    hist['round']=hist.fixture_event.astype(int)
    hist['source_history_file']=hist.source_file
    hist['source_observed_at']=None
    hist['defcon_count']=hist.defensive_contribution
    hist['performance_feature_availability_qualified']=False
    for season in sorted(hist.season.unique()):
        teams=csv(R/'project/data'/f'{season}_teams.csv.gz').set_index('id')
        mask=hist.season.eq(season)
        hist.loc[mask,'club_code']=hist.loc[mask,'historical_team_id'].map(teams.code)
        hist.loc[mask,'opponent_club_code']=hist.loc[mask,'opponent_team'].map(teams.code)
    for field in ['total_points','bps','bonus','assists']:
        hist['original_'+field]=hist[field]
    snapshot=T/'snapshots/2026_10_08'
    native=csv(snapshot/'derived/player_matches.csv.gz')
    nm=js(snapshot/'derived/manifest.json')
    bootstrap=js(snapshot/'raw/bootstrap-static.json')
    expected_raw=next(x['sha256'] for x in nm['raw_sources'] if x['file']=='raw/bootstrap-static.json')
    if sha(snapshot/'raw/bootstrap-static.json')!=expected_raw:raise ValueError('Native register changed')
    clubs=pd.DataFrame(bootstrap['teams']).set_index('id')
    native['historical_team_id']=native.team
    native['historical_team']=native.team.map(clubs.name)
    native['club_code']=native.team.map(clubs.code)
    native['opponent_club_code']=native.opponent_team.map(clubs.code)
    native['fixture_event']=native['round']
    native['fixture_kickoff_time']=native.kickoff_time
    native['kickoff_sources_agree']=True
    native['scoring_qualified']=True
    native['label_status']='official_target_season_scoring'
    native['points_version']=nm['version']
    native['defcon_points_2026_27']=native.defcon_points
    native['original_assists']=native.assists
    native['original_starts']=native.starts
    native['starts_quality']='native_fpl'
    native['source_observed_at']=native.observed_at
    native['performance_feature_availability_qualified']=False
    native['scoring_relevant_inventory']=True
    native['source_history_file']='snapshots/2026_10_08/'+native.source_history_file
    native['source_live_file']='snapshots/2026_10_08/'+native.source_live_file
    native['source_fixture_file']='snapshots/2026_10_08/'+native.source_fixture_file
    for field in [x for x in STATS if x.startswith('expected_')]:
        native[field+'_original']=native[field]
        native[field+'_quality']='official_target_season_statistic'
    pm=pd.concat([hist,native],ignore_index=True).sort_values(K).reset_index(drop=True)
    pm['dataset_version']=VERSION
    pm['points_standard']='2026-27'
    pm['training_ready']=False
    if pm.duplicated(K).any() or pm[['club_code','opponent_club_code']].isna().any().any():
        raise ValueError('Canonical identity/club mapping incomplete')
    if pm.loc[~pm.scoring_qualified,TARGETS].notna().any().any():
        raise ValueError('Unqualified historical points leaked into harmonized targets')
    ledger=js(P/'inputs/ledger_CURRENT.json')
    req_path=R/'scoring_2026_27/bulk_reconciliation'/ledger['requirements']
    if sha(req_path)!=ledger['requirements_sha256']:raise ValueError('Canonical counter ledger changed')
    req=csv(req_path)
    counters=req[K+['field','value','status','provenance','is_open','needs_external_quality_review']].copy()
    counters.loc[counters.is_open,'value']=float('nan')
    qualified_keys=pd.MultiIndex.from_frame(pm.loc[pm.scoring_qualified,K])
    counters['value_qualified_for_scoring']=pd.MultiIndex.from_frame(counters[K]).isin(qualified_keys)
    counters['before_deadline_feature_qualified']=False
    grouped=hist.groupby(RK,sort=True)
    size=grouped.size()
    rounds=size.rename('fixture_count').to_frame()
    rounds['element']=grouped.element.first()
    rounds['position']=grouped.position.first()
    if grouped.position.nunique().gt(1).any():raise ValueError('Conflicting historical position within round')
    rounds['club_codes']=grouped.club_code.agg(lambda x:'|'.join(str(int(c)) for c in sorted(set(x))))
    rounds['club_changes_within_round']=grouped.club_code.nunique().gt(1)
    for field in STATS+TARGETS+['original_total_points','original_bps','original_bonus','original_assists','defcon_points']:
        rounds[field]=strict_sum(grouped,field,size)
    rounds['scoring_qualified']=grouped.scoring_qualified.all()
    rounds['label_status']='blocked_missing_or_unqualified_fixture'
    rounds.loc[rounds.scoring_qualified,'label_status']='qualified_complete_observed_round'
    rounds['round_population_basis']='observed_official_history_rows_only_no_fabricated_blanks'
    rounds=rounds.reset_index()
    nr=csv(snapshot/'derived/player_rounds.csv.gz')
    nr['scoring_qualified']=True
    nr['label_status']='official_target_season_round_including_explicit_nonparticipation'
    nr['round_population_basis']='official_event_live_universe_at_collection_time'
    for field in ['total_points','bps','bonus','assists']:nr['original_'+field]=nr[field]
    nr['bps_2026_27']=nr.bps
    nr['bonus_2026_27']=nr.bonus
    nr['assists_2026_27']=nr.assists
    defcon=native.groupby(RK).defcon_points.sum()
    nr['defcon_points_2026_27']=defcon.reindex(pd.MultiIndex.from_frame(nr[RK])).to_numpy()
    # An explicit native round with no fixture observation cannot receive a defensive award.
    ineligible=nr.fixture_count.eq(0)&nr.minutes.eq(0)&nr.defensive_contribution.eq(0)
    nr.loc[ineligible,'defcon_points_2026_27']=0
    pr=pd.concat([rounds,nr],ignore_index=True).sort_values(RK).reset_index(drop=True)
    pr['deadline_eligible_universe_qualified']=False
    pr['training_ready']=False
    pr['dataset_version']=VERSION
    pr['points_standard']='2026-27'
    if pr.duplicated(RK).any():raise ValueError('Duplicate canonical round identity')
    # Ensure aggregation never changes the qualified native current outcomes.
    observed=native.groupby(RK).total_points_2026_27.sum()
    native_check=nr.set_index(RK).total_points_2026_27.reindex(observed.index)
    if not observed.eq(native_check).all():raise ValueError('Native fixture-to-round point residual')
    future=horizon_targets(pr)
    coverage=[]
    for season,g in pm.groupby('season',sort=True):
        for field in STATS+TARGETS+['times_tackled','big_chance_saves','saves_inside_box','saves_outside_box']:
            coverage.append(dict(season=season,field=field,canonical_rows=len(g),
                populated_rows=int(g[field].notna().sum()),
                populated_scoring_qualified_rows=int((g[field].notna()&g.scoring_qualified).sum()),
                before_deadline_feature_qualified_rows=0))
    summary=dict(version=VERSION,status='canonical_scoring_and_horizon_tables_features_unqualified',
        seasons=sorted(pm.season.unique()),player_matches=len(pm),player_rounds=len(pr),
        qualified_player_match_labels=int(pm.scoring_qualified.sum()),
        qualified_player_round_labels=int(pr.scoring_qualified.sum()),
        qualified_whole_historical_fixtures=sm['counts']['qualified_whole_fixtures'],
        qualified_native_fixtures=nm['fixtures'],
        historical_rounds_with_multiple_observed_fixtures=int(rounds.fixture_count.gt(1).sum()),
        historical_rounds_with_club_change=int(rounds.club_changes_within_round.sum()),
        official_native_nonparticipation_rounds=int(nr.fixture_count.eq(0).sum()),
        historical_blank_rounds_fabricated=0,native_fixture_round_point_residuals=0,
        qualified_next_round_targets=int(future.target_next_1_qualified.sum()),
        qualified_next_three_round_targets=int(future.target_next_3_qualified.sum()),
        qualified_next_six_round_targets=int(future.target_next_6_qualified.sum()),
        training_ready_rows=0,
        remaining_gates=['All historical season scoring gates and unresolved inputs',
            'Historical nonparticipation and blank-round membership/labels',
            'Actual historical deadlines and eligible universes',
            'Verified pre-deadline performance/metadata availability and feature construction'])
    for df,name in [(pm,'player_matches.csv.xz'),(pr,'player_rounds.csv.xz'),
        (future,'next_round_targets.csv.xz'),(counters,'input_counters.csv.xz'),
        (pd.DataFrame(coverage),'statistic_coverage.csv')]:save(df,out/name)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    manifest=dict(version=VERSION,points_standard='2026-27',training_ready=False,path_root='research/current',
        input_sha256=hashes,code_sha256={'training_dataset/canonical/build.py':sha(Path(__file__))},
        output_sha256={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json'},counts=summary)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
