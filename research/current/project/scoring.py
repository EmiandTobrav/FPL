"""2026/27 scoring components. Never silently invent missing event data."""
import numpy as np
import pandas as pd

GOALS = {1: 10, 2: 6, 3: 5, 4: 4}
CS = {1: 4, 2: 4, 3: 1, 4: 0}

def portable_core(d):
    """Exact computable subset; EXCLUDES assists, bonus and defensive contributions.
    Historical season positions retained. Not a complete current-rule FPL score.
    clean_sheets/goals_conceded must be player-level official FPL stats.
    """
    p = d.pos
    return ((d.minutes > 0).astype(int) + (d.minutes >= 60).astype(int)
            + d.goals_scored * p.map(GOALS) + d.clean_sheets * p.map(CS)
            - np.floor(d.goals_conceded / 2) * p.isin([1, 2])
            + np.floor(d.saves / 3) * (p == 1) + 5 * d.penalties_saved
            - 2*d.penalties_missed - d.yellow_cards - 3*d.red_cards - 2*d.own_goals)

def defensive_points(d):
    # DEF: CBI + tackles; MID/FWD additionally recoveries. Counts, not averages.
    c = d.clearances_blocks_interceptions + d.tackles
    return 2 * (((d.pos == 2) & (c >= 10)) |
                (d.pos.isin([3,4]) & ((c + d.recoveries) >= 12))).astype(int)

def allocate_bonus(bps):
    rank = pd.Series(bps).rank(method='min', ascending=False)
    return (4-rank).clip(lower=0).astype(int).to_numpy()

def exact_current_score(d):
    """Caller must supply externally verified current-rule assists and BPS.
    Input must include ALL players in each match, including opposing team.
    Missing data raises: historical aggregate BPS is deliberately insufficient.
    """
    needed = ['assists_2026_verified', 'bps_2026_verified',
              'clearances_blocks_interceptions', 'tackles', 'recoveries']
    if any(c not in d or d[c].isna().any() for c in needed):
        raise ValueError('Exact rescoring blocked: missing verified 2026/27 event inputs')
    rank = d.groupby(['season','fixture']).bps_2026_verified.rank(method='min',ascending=False)
    return portable_core(d) + 3*d.assists_2026_verified + (4-rank).clip(lower=0) + defensive_points(d)

def self_test():
    assert allocate_bonus([40,40,30,20]).tolist() == [3,3,1,0]
    assert allocate_bonus([40,30,30,20]).tolist() == [3,2,2,0]
    assert allocate_bonus([40,30,20,20]).tolist() == [3,2,1,1]
    x=pd.DataFrame({'pos':[2,2,3,4,1], 'clearances_blocks_interceptions':[7,7,7,7,20],
                    'tackles':[3,2,3,3,0], 'recoveries':[0,10,2,1,0]})
    assert defensive_points(x).tolist()==[2,0,2,0,0]

if __name__=='__main__':
    self_test()
    print('Scoring boundary and bonus tie checks passed')
