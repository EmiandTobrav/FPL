"""Focused data-repair and source-definition checks; no model tests."""
from pathlib import Path
import json,hashlib
import pandas as pd
from build_labels import point_bounds,COUNTS,MAP
P=Path(__file__).resolve().parent;O=P/'results';ROOT=P.parents[3]
def run():
 for name,sha in json.loads((P/'input_sha256.json').read_text()).items():
  assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
 for source in json.loads((O/'clearance_sources.json').read_text()):assert hashlib.sha256((P/'raw'/source['file']).read_bytes()).hexdigest()==source['sha256']
 gaps=pd.read_csv(O/'gap_fill_audit.csv');assert len(gaps)==133 and gaps.defcon_new.notna().all() and gaps.identity_ok.all()
 assert gaps.defcon_new.isin([0,2]).all()
 pure=point_bounds(gaps.drop(columns=COUNTS).rename(columns=MAP))[0]
 assert pure.equals(gaps.defcon_new)
 z=gaps[['season','element','fixture','name','position','defcon_new']].copy();z['all_fotmob_award']=pure;z['count_disagreements']=0
 for new,old in MAP.items():
  known=gaps[old+'_before'].notna();assert gaps.loc[known,old].equals(gaps.loc[known,old+'_before'])
  z['count_disagreements']+=(known&gaps[new].notna()&(gaps[old+'_before']!=gaps[new])).astype(int)
 z.to_csv(O/'target_source_sensitivity.csv',index=False)
 c=pd.read_csv(O/'clearance_audit.csv');assert len(c)==50 and c.minute_ok.all() and c.goals_ok.all()
 assert (c.fbref_clearances==c.pl_total_clearance+c.pl_blocked_cross).all()
 h=c[c.season=='2021-22'];assert (h.fotmob_clearances==h.pl_total_clearance).all()
 n=c[c.season=='2025-26'];bad=n[n.official_award!=n.pl_award];assert len(bad)==3
 bad.to_csv(O/'remaining_official_disagreements.csv',index=False)
 assert (n[n.purpose=='2025_official_award_disagreement'].official_award==n[n.purpose=='2025_official_award_disagreement'].clearance_only_award).sum()==7
 hist=h.copy();hist['corrected_clearing_count']=hist.pl_total_clearance
 hist[['season','fixture','element','code','name','fbref_clearances','corrected_clearing_count','pl_blocked_cross']].to_csv(O/'verified_clearance_observations.csv',index=False)
 summary=pd.read_csv(O/'summary.csv');assert summary.missing_after.sum()==0 and summary.filled.sum()==133
 tests=pd.DataFrame({'position':['MID','MID','DEF','GK'],'minutes':[90]*4,'Tkl_Tackles':[3,3,3,None],'Sh_Blocks':[1,1,1,None],'Int':[3,2,3,None],'Clr':[5,5,3,None],'Recov':[None]*4})
 tests[COUNTS]=tests[COUNTS].astype(float)
 ex,lo,hi,inf=point_bounds(tests);assert ex.iloc[[0,2,3]].tolist()==[2,2,0] and pd.isna(ex.iloc[1]) and hi.iloc[1]==2
 print('PASS: input hashes, 133 identity-gated fills, known counts preserved, all-source point sensitivity, 50 clearance identities, three explicitly retained official disagreements, missing-not-zero bounds.')
if __name__=='__main__':run()
