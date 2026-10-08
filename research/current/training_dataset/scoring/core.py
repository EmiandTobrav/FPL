"""Changed-component scorer. Computation alone never qualifies a label.

Only changed BPS terms are replaced. Legacy tackle clipping is an explicit
hypothesis until qualified, never a transformation of the signed raw counter.
Event bundles must be complete and separately approved before use.
"""
from dataclasses import dataclass
import math
from numbers import Real

POSITIONS = ('GK', 'DEF', 'MID', 'FWD')
GOAL_POINTS = {'GK': 10, 'DEF': 6, 'MID': 5, 'FWD': 4}

class MissingInput(ValueError):
    pass

def integer(row, field, signed=False):
    value = row.get(field)
    if value is None or not isinstance(value, Real) or not math.isfinite(value):
        raise MissingInput(field)
    if isinstance(value, bool) or int(value) != value or (not signed and value < 0):
        raise ValueError(f'Invalid counter {field}: {value}')
    return int(value)

def position(row):
    value = row.get('position')
    if value not in POSITIONS:
        raise ValueError(f'Unknown historical position: {value}')
    return value

def season_start(row):
    year = int(str(row['season']).split('-')[0])
    if not 2019 <= year <= 2026:
        raise ValueError('Unsupported season')
    return year

def bps_changes(original, target, legacy_mode):
    """Return an auditable additive breakdown, not a training qualification."""
    year, pos = season_start(original), position(original)
    if year == 2026:
        raise ValueError('Official target-season BPS must be preserved directly')
    cbi = integer(target, 'clearances_blocks_interceptions')
    terms = dict(cbi=cbi // 3 - cbi // 2,
                 remove_times_tackled=integer(target, 'times_tackled'),
                 assists=9 * (integer(target, 'assists_2026_27') - integer(original, 'assists')))
    if year < 2025:
        if legacy_mode not in ('clipped', 'signed'):
            raise ValueError('Legacy clipping hypothesis must be explicit')
        net = integer(target, 'legacy_net_tackles', signed=True)
        old = max(0, net) if legacy_mode == 'clipped' else net
        terms['tackles'] = 2 * (integer(target, 'won_tackles') - old)
        terms['goal_line_clearances'] = (6 if year == 2024 else 9) * integer(target, 'goal_line_clearances')
        if pos in ('MID', 'FWD') and integer(original, 'goals_scored') > 0:
            penalties = integer(target, 'penalty_goals')
            if penalties > integer(original, 'goals_scored'):
                raise ValueError('Penalty goals exceed recorded goals; revision bundle required')
            terms['penalty_goals'] = -(6 if pos == 'MID' else 12) * penalties
    if year < 2024:
        terms['fouls_won'] = integer(target, 'fouls_won')
        terms['shots_on_target'] = 2 * integer(target, 'shots_on_target')
        if pos in ('GK', 'DEF'):
            terms['goals_conceded'] = -4 * integer(original, 'goals_conceded')
    if pos == 'GK':
        saves = integer(original, 'saves')
        inside = integer(target, 'saves_inside_box')
        big = integer(target, 'big_chance_saves')
        penalties = integer(original, 'penalties_saved')
        new = 2 * saves + inside + big + 7 * penalties
        if year == 2025:
            old = 3 * inside + 2 * integer(target, 'saves_outside_box') + 8 * penalties
        else:
            old = 2 * saves + (9 if year == 2024 else 15) * penalties
        terms['keeper_saves'] = new - old
    return terms

@dataclass(frozen=True)
class EventBundle:
    goals_delta: int
    own_goals_delta: int
    bps_delta: int
    proof: str
    qualified: bool

def apply_bundle(original, terms, bundle):
    if not bundle.qualified or not bundle.proof:
        raise ValueError('Unqualified or incomplete event-revision bundle')
    for value in (bundle.goals_delta, bundle.own_goals_delta, bundle.bps_delta):
        if type(value) is not int:
            raise ValueError('Revision deltas must be explicit integers')
    if integer(original, 'goals_scored') + bundle.goals_delta < 0 or integer(original, 'own_goals') + bundle.own_goals_delta < 0:
        raise ValueError('Revision makes an event count negative')
    return {**terms, 'approved_event_bundle': bundle.bps_delta}

def bps_candidate(original, target, legacy_mode, bundle=None):
    terms = bps_changes(original, target, legacy_mode)
    if bundle is not None:
        terms = apply_bundle(original, terms, bundle)
    value = integer(original, 'bps', signed=True) + sum(terms.values())
    return value, terms

def basic_changes(original, target, defcon_points, bundle=None):
    year, pos = season_start(original), position(original)
    if type(defcon_points) is not int or defcon_points not in (0, 2):
        raise ValueError('Need an explicit qualified defensive award, 0 or 2')
    if defcon_points and (pos == 'GK' or integer(original, 'minutes') == 0):
        raise ValueError('Defensive award for an ineligible observation')
    terms = dict(assists=3 * (integer(target, 'assists_2026_27') - integer(original, 'assists')))
    if pos == 'GK' and year < 2024:
        terms['keeper_goal_value'] = 4 * integer(original, 'goals_scored')
    if year < 2025:
        terms['defcon'] = defcon_points
    if bundle is not None:
        apply_bundle(original, {}, bundle)
        terms['approved_goal_revision'] = GOAL_POINTS[pos] * bundle.goals_delta
        terms['approved_own_goal_revision'] = -2 * bundle.own_goals_delta
    return terms

def total_candidate(original, target, new_bonus, defcon_points, bundle=None):
    if type(new_bonus) is not int or new_bonus not in (0, 1, 2, 3):
        raise ValueError('Whole-match bonus must be supplied')
    terms = basic_changes(original, target, defcon_points, bundle)
    total = integer(original, 'total_points', signed=True) - integer(original, 'bonus') + sum(terms.values()) + new_bonus
    return total, terms

def bonus_for_complete_fixture(scores, expected_codes):
    expected_codes = list(expected_codes)
    if len(set(expected_codes)) != len(expected_codes) or set(scores) != set(expected_codes) or len(scores) < 22:
        raise ValueError('Incomplete or duplicate fixture participant inventory')
    for value in scores.values():
        if value is None or isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or int(value) != value:
            raise ValueError('Unresolved fixture BPS')
    return {code: max(0, 3 - sum(other > score for other in scores.values())) for code, score in scores.items()}

def basic_component_account(original, defcon_points):
    """Independent basic-point audit using explicit FPL event totals.

    This audits already published basic points. It never creates missing counts
    or adjudicates source exceptions, on-field clean sheets or red-card exposure.
    """
    year, pos = season_start(original), position(original)
    minutes = integer(original, 'minutes')
    weights = {**GOAL_POINTS, 'GK': 6 if year < 2024 else 10}
    terms = dict(minutes=2 if minutes >= 60 else int(minutes > 0),
                 goals=weights[pos] * integer(original, 'goals_scored'),
                 assists=3 * integer(original, 'assists'),
                 clean_sheets={'GK': 4, 'DEF': 4, 'MID': 1, 'FWD': 0}[pos] * integer(original, 'clean_sheets'),
                 penalties_saved=5 * integer(original, 'penalties_saved'),
                 penalties_missed=-2 * integer(original, 'penalties_missed'),
                 yellow_cards=-integer(original, 'yellow_cards'),
                 red_cards=-3 * integer(original, 'red_cards'),
                 own_goals=-2 * integer(original, 'own_goals'))
    if pos in ('GK', 'DEF'):
        terms['goals_conceded'] = -(integer(original, 'goals_conceded') // 2)
    if pos == 'GK':
        terms['saves'] = integer(original, 'saves') // 3
    if year >= 2025:
        if type(defcon_points) is not int or defcon_points not in (0, 2):
            raise ValueError('Missing authoritative defensive award')
        terms['defcon'] = defcon_points
    return terms
