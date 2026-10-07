"""Project pinned archive and freeze a stratified control sample before collection."""
from pathlib import Path
import hashlib,json,argparse
import pandas as pd
import pyarrow.parquet as pq
P=Path(__file__).resolve().parent;S=P.parent;KEY=['season','fixture','code']
FIELDS={'timesTackled':'times_tackled','savedObox':'saved_obox','savedIbox':'saved_ibox',
 'totalTackle':'total_tackle','wonTackle':'won_tackle','challengeLost':'challenge_lost',
 'clearanceOffLine':'clearance_off_line','totalClearance':'total_clearance','outfielderBlock':'outfielder_block',
 'interception':'interception','ballRecovery':'ball_recovery','wasFouled':'was_fouled',
 'ontargetScoringAtt':'ontarget_scoring_att','attPenGoal':'att_pen_goal','saves':'saves'}
EXPECTED='2765b1771493c917ce7c544b01cf3a151e159a818abb889c7fcbd746353eaead'

def save(df,name):df.to_csv(P/name,index=False,compression={'method':'gzip','mtime':0} if name.endswith('.gz') else None)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,default=S/'keeper_recovery/raw/opta_player_stats.parquet');args=parser.parse_args()
 raw=args.archive;digest=hashlib.sha256(raw.read_bytes()).hexdigest()
 if digest!=EXPECTED:raise ValueError('Archive differs from frozen source')
 schema=pq.read_schema(raw)
 (P/'inputs/archive_schema.json').write_text(json.dumps(dict(sha256=digest,columns=schema.names),indent=2)+'\n')
 mapped=pd.concat([pd.read_csv(f,low_memory=False) for f in sorted((S/'bps_recovery/inputs').glob('counts-*.csv.gz'))],ignore_index=True)
 meta=['match_id','player_id','match_date','team_id','team_name','player_name','season','minsPlayed']
 stats=pq.read_table(raw,columns=meta+list(FIELDS),filters=[('competition','=','EPL'),('season','in',[f'{y}-{y+1}' for y in range(2019,2027)]),('minsPlayed','>',0)]).to_pandas()
 if stats.duplicated(['match_id','player_id']).any():raise ValueError('Duplicate archive identity')
 out=mapped[KEY+['name','position','date','home','away','match_id','player_id','team_id','mapping_status']].merge(stats,on=['match_id','player_id'],how='left',suffixes=('','_raw'),validate='many_to_one')
 linked=out.mapping_status.eq('matched')
 if not out.loc[linked,'team_id'].eq(out.loc[linked,'team_id_raw']).all():raise ValueError('Team identity drift')
 if not out.loc[linked,'date'].eq(out.loc[linked,'match_date'].str[:10]).all():raise ValueError('Date drift')
 expected_season=out.season.str[:4]+'-'+(out.season.str[:4].astype(int)+1).astype(str)
 if not out.loc[linked,'season_raw'].eq(expected_season[linked]).all():raise ValueError('Season drift')
 for field in set(FIELDS)&set(mapped):
  old=mapped.set_index(KEY)[field];new=out.set_index(KEY)[field]
  if not (old.eq(new)|(old.isna()&new.isna())).all():raise ValueError('Existing projection changed: '+field)
 save(out,'inputs/archive_projection.csv.gz')
 # Additional corroboration, not a fitted rule: official Kante net-tackle example.
 example=pq.read_table(raw,columns=meta+list(FIELDS),filters=[('competition','=','EPL'),('season','=','2017-2018')]).to_pandas()
 example=example[example.player_name.eq('N. Kanté')&example.match_date.str.startswith('2018-04-08')]
 if len(example)!=1:raise ValueError('Ambiguous narrative example')
 save(example,'inputs/kante_net_example.csv')
 controls=pd.read_csv(S/'bps_recovery/inputs/primary_controls.csv.gz',low_memory=False)
 follow=pd.read_csv(S/'keeper_recovery/followup/primary_verified/observations.csv')
 used=pd.MultiIndex.from_frame(pd.concat([controls[KEY],follow[KEY]]).drop_duplicates())
 hist=out[out.season.ne('2026-27')&linked].copy()
 hist=hist[~pd.MultiIndex.from_frame(hist[KEY]).isin(used)]
 selected=[]
 for season,g in hist.groupby('season',sort=True):
  candidates=[('explicit_line_clearance',g.clearanceOffLine.gt(0)),('explicit_tackled_zero',g.timesTackled.eq(0)),('explicit_tackled_positive',g.timesTackled.gt(0)),('explicit_keeper_outside_save',g.position.eq('GK')&g.savedObox.gt(0))]
  for stratum,mask in candidates:
   h=g[mask].sort_values(KEY)
   chosen={(r['fixture'],r['code']) for r in selected if r['season']==season}
   h=h[[ (int(r.fixture),int(r.code)) not in chosen for r in h.itertuples() ]]
   if h.empty:raise ValueError('Empty sample stratum '+season+' '+stratum)
   row=h.iloc[0];selected.append(dict(**{k:row[k] for k in KEY+['name','date','home','away']},stratum=stratum))
 sample=pd.DataFrame(selected)
 if sample.duplicated(KEY).any():raise ValueError('Sample overlap')
 save(sample,'control_plan.csv')
 (P/'control_protocol.json').write_text(json.dumps(dict(selection='First season/fixture/code in each explicit source stratum; exclude all prior controls. Frozen before collecting official responses.',strata=[x[0] for x in candidates],rows=len(sample),primary_comparison='Compare both-explicit values, omission differences and invalid values separately. No missing-to-zero coercion.',acceptance='No disagreement may be hidden by aggregate agreement. Conflicting cells stay open; field agreement is not blanket row approval.',limitations='Purposeful coverage sample, not random population estimate; same Opta ancestry, not independent provider validation; no scoring holdout claimed.'),indent=2)+'\n')
 print(dict(projected=len(out),matched=int(linked.sum()),fresh_sample=len(sample)))
if __name__=='__main__':main()
