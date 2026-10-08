"""Conservative BPS upper bounds; unknown negative events remain unknown."""
import math
from numbers import Real

POSITIVE = {
    'accurateCrossNocorner': 'accurate_cross_nocorner',
    'bigChanceCreated': 'big_chance_created',
    'totalAttAssist': 'total_att_assist',
    'wonContest': 'won_contest',
    'ballRecovery': 'ball_recovery',
    'totalPass': 'total_pass',
    'accuratePass': 'accurate_pass',
}
NEGATIVE = {'penaltyConceded': ('penalty_conceded', 3),
    'bigChanceMissed': ('big_chance_missed', 3),
    'errorLeadToGoal': ('error_lead_to_goal', 3),
    'errorLeadToShot': ('error_lead_to_shot', 1),
    'fouls': ('fouls', 1), 'totalOffside': ('total_offside', 1),
    'shotOffTarget': ('shot_off_target', 1)}


def counter(row, field, signed=False):
    value = row.get(field)
    if (isinstance(value, bool) or not isinstance(value, Real)
            or not math.isfinite(value) or int(value) != value
            or (not signed and value < 0)):
        raise ValueError('Missing or invalid counter: ' + field)
    return int(value)


def known(value):
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)


def upper_bound(row, mode):
    year = int(row['season'].split('-')[0])
    if year not in range(2019, 2025) or row['position'] not in ['DEF','MID','FWD']:
        raise ValueError('Only historical outfield legacy-net observations supported')
    if mode not in ['signed', 'clipped']:
        raise ValueError('Unknown legacy hypothesis')
    minutes, goals = counter(row, 'minutes'), counter(row, 'goals_scored')
    if minutes == 0:
        raise ValueError('An active player is required')
    net = counter(row, 'legacy_net_tackles', signed=True)
    cbi = counter(row, 'clearances_blocks_interceptions')
    total, accurate = counter(row, 'totalPass'), counter(row, 'accuratePass')
    if accurate > total:
        raise ValueError('Accurate passes exceed attempts')
    # Always allow the maximum active minute award, including ambiguous clocks.
    terms = dict(minutes_upper=6,
        goals={'DEF':12,'MID':18,'FWD':24}[row['position']] * goals,
        assists=9 * counter(row, 'assists'),
        clean_sheets=12 * counter(row, 'clean_sheets') if row['position'] == 'DEF' else 0,
        cbi=cbi // 2, recoveries=counter(row, 'ballRecovery') // 3,
        crosses=counter(row, 'accurateCrossNocorner'),
        big_chances_created=3 * counter(row, 'bigChanceCreated'),
        key_passes=counter(row, 'totalAttAssist'), dribbles=counter(row, 'wonContest'),
        winning_goal_upper=3 if goals else 0,
        passes=(6 if accurate / total >= .9 else 4 if accurate / total >= .8
                else 2 if accurate / total >= .7 else 0) if total >= 30 else 0,
        tackles=2 * (max(0, net) if mode == 'clipped' else net),
        penalties_missed=-6 * counter(row, 'penalties_missed'),
        yellow_cards=-3 * counter(row, 'yellow_cards'),
        red_cards=-9 * counter(row, 'red_cards'),
        own_goals=-6 * counter(row, 'own_goals'))
    ignored = []
    for field, (_, weight) in NEGATIVE.items():
        if known(row.get(field)):
            terms[field] = -weight * counter(row, field)
        else:
            ignored.append(field)
    if known(row.get('times_tackled')):
        terms['times_tackled'] = -counter(row, 'times_tackled')
    else:
        ignored.append('times_tackled')
    if year == 2024:
        terms.update(goal_line_clearances=3 * counter(row, 'goal_line_clearances'),
                     fouls_won=counter(row, 'fouls_won'),
                     shots_on_target=2 * counter(row, 'shots_on_target'))
        if row['position'] == 'DEF':
            terms['goals_conceded'] = -4 * counter(row, 'goals_conceded')
    return sum(terms.values()), terms, ignored
