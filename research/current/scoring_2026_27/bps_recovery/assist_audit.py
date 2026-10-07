"""Evaluate assist candidates; do not turn an aggregate proxy into FPL labels."""
from pathlib import Path
import json,sys
import pandas as pd
from audit import ASSIST_FIELDS
P=Path(__file__).resolve().parent;S=P.parent
CANDIDATE_FIELDS=['goalAssist','assistAttemptSaved','assistPost','assistBlockedShot','assistOwnGoal','assistPenaltyWon','assistFreeKickWon','assistHandballWon','assistPassLost']


def main():
    frame=pd.concat(pd.read_csv(f) for f in sorted((P/'inputs').glob('counts-*.csv.gz')))
    frame=frame[frame.mapping_status.eq('matched')].copy()
    # Hypothesis fixed before evaluating the controls. These categories can
    # overlap and don't encode all modern rule conditions. This is a probe.
    frame['assist_category_sum_diagnostic']=frame[CANDIDATE_FIELDS].fillna(0).sum(axis=1)
    frame['ordinary_assists_diagnostic']=frame.goalAssist.fillna(0)
    summaries=[]
    for season,g in frame.groupby('season'):
        for label,col in [('ordinary_opta','ordinary_assists_diagnostic'),('all_candidate_categories','assist_category_sum_diagnostic')]:
            truth=g.fpl_assists;v=g[col];positive=truth.gt(0)|v.gt(0)
            summaries.append(dict(season=season,hypothesis=label,rows=len(g),fpl_assists=int(truth.sum()),candidate_assists=int(v.sum()),exact_rows=int(v.eq(truth).sum()),positive_union_rows=int(positive.sum()),exact_positive_union_rows=int((v.eq(truth)&positive).sum()),overcount_rows=int(v.gt(truth).sum()),undercount_rows=int(v.lt(truth).sum())))
    pd.DataFrame(summaries).to_csv(P/'assist_hypothesis_comparison.csv',index=False)
    controls=pd.read_csv(S/'acquisition_followup/assist_decisions.csv')
    check=controls.merge(frame,on=['season','fixture','code'],suffixes=('_decision',''),validate='one_to_one')
    check['expected_for_official_example']=check.historical_assists+check.assist_delta
    check['category_sum_matches_example']=check.assist_category_sum_diagnostic.eq(check.expected_for_official_example)
    check[['season','fixture','code','name_decision','awarded_for_this_goal','expected_for_official_example','assist_category_sum_diagnostic','category_sum_matches_example',*CANDIDATE_FIELDS]].to_csv(P/'assist_official_examples.csv',index=False)
    queue=frame[(frame.assist_category_sum_diagnostic.ne(frame.fpl_assists))|frame[CANDIDATE_FIELDS[1:]].notna().any(axis=1)].copy()
    queue['status']='candidate_only_requires_goal_event_adjudication'
    queue[['season','fixture','fixture_code','date','home','away','code','name','match_id','player_id','fpl_assists','assist_category_sum_diagnostic','status',*CANDIDATE_FIELDS]].to_csv(P/'assist_review_candidates.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    findings=dict(candidate_categories=CANDIDATE_FIELDS,all_six_official_examples_matched=bool(check.category_sum_matches_example.all()),official_positive_examples=len(check[check.awarded_for_this_goal.eq(True)]),positive_examples_detected=int(check[check.awarded_for_this_goal.eq(True)].category_sum_matches_example.sum()),candidate_queue_rows=len(queue),queue_is_exhaustive=False,reason='Known modern additions can be absent from every archived assist category; counts cannot encode receiving location, defensive touch sequence or intended receiver.',new_verified_assist_labels=0,existing_official_additions_preserved=4)
    (P/'assist_findings.json').write_text(json.dumps(findings,indent=2)+'\n')
    print(findings)

if __name__=='__main__':main()
