"""Materialize one enriched master for all seasons; no new PL observations."""
import bisect,collections,csv,json,lzma
from common import *
from workload_store import Store,WINDOWS
from build_calendar import calculate as calendar
OUT=R/'datasets/fpl_master_enriched_v2'
def national(code,at,base,events):
 prior=[r for r in events.get(code,[]) if r['available']<at];good=[r for r in prior if r['minutes'] is not None];last=max((r for r in good if r['minutes']>0),key=lambda r:r['kickoff'],default=None)
 out=dict(wl_internationals_covered=True,wl_international_coverage_complete=False,wl_international_missing_means_zero=False,wl_international_youth_included=True,wl_club_friendlies_covered=False,wl_international_latest_input_available_at=max((r['available'] for r in prior),default=None),wl_last_international_country=last['team'] if last else '',wl_last_international_level=last['age_level'] if last else '',wl_hours_since_last_international_appearance_end_proxy=round((at-last['end']).total_seconds()/3600,4) if last else None,wl_all_competitions_coverage_complete=False)
 rests=[t for t in [base['wl_hours_since_last_observed_scoped_appearance_end_proxy'],out['wl_hours_since_last_international_appearance_end_proxy']] if t is not None];out['wl_hours_since_last_observed_any_appearance_end_proxy']=min(rests) if rests else None
 for days in WINDOWS:
  window=[r for r in prior if at-timedelta(days=days)<=r['kickoff']<at];known=[r for r in window if r['minutes'] is not None]
  out[f'wl_international_unknown_minute_rows_{days}d']=sum(r['minutes'] is None for r in window);out[f'wl_international_observed_squad_rows_{days}d']=len(window)
  for field,value in [('minutes',sum(r['minutes'] for r in known)),('appearances',sum(r['minutes']>0 for r in known)),('starts',sum(r['starts'] for r in known))]:
   out[f'wl_international_{field}_lower_bound_{days}d']=value;out[f'wl_all_observed_{field}_lower_bound_{days}d']=base[f'wl_scoped_{field}_lower_bound_{days}d']+value
  for level in ['senior','U21','U20','U17','U19','U23_Olympic']:out[f'wl_international_{level}_minutes_lower_bound_{days}d']=sum(r['minutes'] for r in known if r['age_level']==level)
 return out
def inputs():
 seasons,rounds,members=config();pl=[];fixtures={};targets=collections.defaultdict(list)
 for row in read(MASTER/'player_matches.csv.xz'):
  season=row['season'];code=num(row['code']);key=season+':'+num(row['fixture']);t=dt(row['fixture_kickoff_time']);f=fixtures.setdefault(key,dict(key=key,kickoff=t,available=t+timedelta(hours=24),teams=set(),season=season));f['teams'].add(row['historical_team'])
  targets[season].append(dict(season=season,fixture=num(row['fixture']),code=code,round=int(float(row['round']))))
  if truth(row['history_eligible']):
   minute=float(row['native_minutes']);starts=float(row['native_starts']) if row['native_starts'] else (0 if minute==0 else None)
   pl.append(dict(code=code,key=key,kickoff=t,available=t+timedelta(hours=24),end=t+timedelta(minutes=120),team=row['historical_team'],minutes=minute,starts=starts,competition='Premier League',extra_time=False))
 fs={};cupfs=[];cuprows=[];nationals=collections.defaultdict(list);rosters={};qualified={(r['season'],r['external_match_key'],r['team']) for r in read(P/'team_timeline_audit.csv.gz') if truth(r['qualified'])}
 for row in read(P/'matches.csv.gz'):
  if row['competition_type']!='club_cup':continue
  t=dt(row['kickoff_utc']);f=dict(key=row['external_match_key'],kickoff=t,available=t+timedelta(hours=24),end=t+timedelta(minutes=int(row['match_length_excluding_added_time'])+30),teams={row['home_team'],row['away_team']},competition=row['competition'],extra_time=truth(row['extra_time']),season=row['season']);fs[(row['season'],f['key'])]=f
  cupfs.append(f);path=R/row['raw_file']
  if path.exists():
   for side in json.loads(path.read_text()).get('rosters',[]):
    team=cup.club(side['team']['displayName'])
    if (row['season'],f['key'],team) in qualified:rosters[(f['key'],team)]={r['athlete']['id'] for r in side.get('roster',[])}
 for row in read(P/'player_minutes.csv.gz'):
  minute=int(row['minutes_played']) if row['minutes_played']!='' else None;t=dt(row['kickoff_utc'])
  if row['competition_type']=='club_cup':
   if minute is not None:cuprows.append(dict(fs[(row['season'],row['external_match_key'])],code=row['code'],team=row['team'],espn_player_id=row['espn_player_id'],minutes=minute,starts=int(truth(row['starter']))))
  else:nationals[row['season']].append(dict(row,kickoff=t,available=t+timedelta(hours=24),end=t+timedelta(minutes=150 if truth(row['extra_time_included']) else 120),minutes=minute,starts=int(truth(row['starter']))))
 return seasons,rounds,targets,pl,list(fixtures.values()),cuprows,cupfs,rosters,nationals
def main():
 OUT.mkdir(exist_ok=True);seasons,rounds,targets,pl,plfs,cups,cupfs,rosters,nationals=inputs();snaps=collections.defaultdict(list)
 for r in read(P/'fixture_snapshots.csv.gz'):snaps[(r['season'],int(r['round']))].append(r)
 announcements=list(read(P/'historical_announced_club_fixtures.csv'));coverage=[];fieldnames=None;round_writer=None;match_writer=None;master_writer=None
 with lzma.open(P/'player_round_context.csv.xz','wt',newline='',preset=3) as rf,lzma.open(P/'player_match_context.csv.xz','wt',newline='',preset=3) as mf,lzma.open(OUT/'player_matches.csv.xz','wt',newline='',preset=3) as of:
  for season,z in seasons.items():
   p=[e for e in pl if z['history_start']<=e['kickoff']<z['end']];cf=[e for e in cupfs if z['history_start']<=e['kickoff']<z['end']];cs=[e for e in cups if z['history_start']<=e['kickoff']<z['end']];pf=[f for f in plfs if z['history_start']<=f['kickoff']<z['end']]
   store=Store(p,cs,pf,cf,rosters,{});store.season_start=z['start'];intl=collections.defaultdict(list)
   for row in nationals[season]:intl[row['code']].append(row)
   cache={};match_context={};calcache={};changedrest=0
   for target in targets[season]:
    gw=target['round'];code=target['code'];at=rounds[(season,gw)]-timedelta(minutes=90)
    if (gw,code) not in cache:
     base=store.calculate(code,at);context=dict(base,**national(code,at,base,intl));team=base['wl_last_observed_club'];ck=(gw,team)
     if ck not in calcache:calcache[ck]=calendar(team,season,gw,at,snaps[(season,gw)],announcements)
     context.update(calcache[ck]);context.update(wl_club_assignment_verified=False,wl_club_assignment_basis='last_available_observed_club_not_future_target_club',wl_external_scope='FA_EFL_UEFA_with_qualifying',wl_source_scope_complete=False)
     for k,v in list(context.items()):
      if hasattr(v,'isoformat'):context[k]=v.isoformat()
     cache[(gw,code)]=context
     rr=dict(season=season,round=gw,code=code,**context)
     if round_writer is None:round_writer=csv.DictWriter(rf,fieldnames=list(rr));round_writer.writeheader()
     round_writer.writerow(rr)
    context=cache[(gw,code)];mr=dict(target,**context)
    if match_writer is None:match_writer=csv.DictWriter(mf,fieldnames=list(mr));match_writer.writeheader()
    match_writer.writerow(mr);match_context[(target['fixture'],code)]=context
   for row in read(MASTER/'player_matches.csv.xz'):
    if row['season']!=season:continue
    merged=dict(row,**match_context[(num(row['fixture']),num(row['code']))])
    if master_writer is None:master_writer=csv.DictWriter(of,fieldnames=list(merged));master_writer.writeheader();fieldnames=list(merged)
    master_writer.writerow(merged)
   coverage.append(dict(season=season,master_rows=len(targets[season]),player_round_rows=len(cache),forecast_origins=sum(s==season for s,g in rounds),player_round_rows_with_national_minutes_7d=sum(c['wl_international_minutes_lower_bound_7d']>0 for c in cache.values()),PL_calendar_fresh_origins=len({gw for (gw,code),c in cache.items() if c['cal_pl_calendar_fresh']}),all_competitions_complete=False))
   print('Enriched',season,len(targets[season]),'PL rows',len(cache),'player-round contexts',flush=True)
 write('context_coverage.csv',coverage);(P/'context_summary.json').write_text(json.dumps(dict(seasons=coverage,master_rows=sum(r['master_rows'] for r in coverage),context_columns=[k for k in fieldnames if k.startswith(('wl_','cal_'))],model_changed=False),indent=2))
if __name__=='__main__':main()
