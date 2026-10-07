"""Check reconstruction against explicit 2026/27 Opta keeper counts.

These share Opta provenance with shot events: a consistency check, not a claim
of provider independence. Null explicit counts are not counted as true zeros.
"""
import json
import pandas as pd
from recover import ROOT,recover_team


def main():
    s=pd.read_csv(ROOT/'inputs/current_validation_targets.csv.gz')
    h=pd.read_csv(ROOT/'inputs/shots-2026-2027.csv.gz',dtype={k:'boolean' for k in ['big_chance','is_own_goal','is_blocked']})
    e=pd.read_csv(ROOT/'inputs/events-2026-2027.csv.gz');e['q']=e.qualifier_json.map(json.loads)
    agg=pd.read_csv(ROOT/'inputs/player_stats.csv.gz')
    rows=[]
    for (mid,tid),g in s.groupby(['match_id','team_id']):
        keepers=[dict(player_id=x.player_id,team_id=tid,
                      fpl_saves=x.saves if pd.notna(x.saves) else 0,
                      explicit_big_chance_saves=x.bigChanceSaves) for x in g.itertuples()]
        # The save upper bound here is the Opta box score, not an FPL value.
        counts,problems,_=recover_team(keepers,agg[agg.match_id.eq(mid)&agg.team_id.ne(tid)],
            h[h.match_id.eq(mid)&h.team_id.ne(tid)],e[e.match_id.eq(mid)])
        for x in g.itertuples():
            rows.append(dict(match_id=mid,player_id=x.player_id,name=x.player_name,
                explicit=x.bigChanceSaves,derived=counts.get(x.player_id),problems=';'.join(problems)))
    out=pd.DataFrame(rows);out.to_csv(ROOT/'current_season_validation.csv',index=False)
    known=out[out.explicit.notna()]
    result={'keeper_observations':len(out),'matches':out.match_id.nunique(),
            'explicit_comparisons':len(known),'explicit_exact':int(known.explicit.eq(known.derived).sum()),
            'unresolved':int(out.problems.ne('').sum()),'independent_provider':False}
    (ROOT/'current_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
