"""Pure deadline-to-deadline FPL 2026/27 rules; no forecasts or outcome lookup.

Money is integer £0.1m. Inputs use integer player ids. No inputs are mutated.
A decision is one final transfer batch, not an intra-week trading history.
Pool metadata MUST already be frozen at the decision deadline by the caller.
Outcomes MUST be supplied explicitly for all 15 players, including known blanks.
"""
from collections import Counter
from copy import deepcopy
from itertools import combinations
from math import isfinite
from numbers import Integral, Real

CHIPS = ('wildcard', 'free_hit', 'bench_boost', 'triple_captain')
SQUAD_COUNTS = {1: 2, 2: 5, 3: 5, 4: 3}
FORMATIONS = tuple((1,d,m,10-d-m) for d in range(3,6) for m in range(2,6)
                   if 1 <= 10-d-m <= 3)

class RuleError(ValueError):
    """A state, decision or outcome violates the rules contract."""

class MissingOutcomeError(RuleError):
    """A selected player's result or participation is not known."""

def _int(value, name, minimum=0, maximum=None):
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise RuleError(f'{name} must be an integer: {value!r}')
    value = int(value)
    if value < minimum or (maximum is not None and value > maximum):
        raise RuleError(f'{name} outside valid bounds: {value}')
    return value

def _ids(values, name):
    values = [_int(v, name, 1) for v in values]
    if len(values) != len(set(values)):
        raise RuleError(f'duplicate player in {name}')
    return values

def selling_price(purchase, market):
    purchase = _int(purchase, 'purchase', 1)
    market = _int(market, 'market', 1)
    return market if market <= purchase else purchase + (market-purchase)//2

def next_free(ft, transfers, chip=None, initial=False):
    ft = _int(ft, 'free transfers', 0, 5)
    transfers = _int(transfers, 'transfers')
    if chip not in (None, *CHIPS):
        raise RuleError('unknown chip')
    if initial:
        return 1
    if chip in ('wildcard', 'free_hit'):
        return ft
    return min(5, max(0, ft-transfers)+1)

def initial_state(start_gw=1, bank=1000, ft=1):
    return {'owned': {}, 'bank': _int(bank, 'bank'), 'ft': _int(ft, 'ft', 0, 5),
            'next_gw': _int(start_gw, 'start_gw', 1, 38),
            'used_chips': {'1': [], '2': []}, 'last_chip': None,
            'ownership_clubs': {}}

def normalize_pool(pool):
    if isinstance(pool, dict):
        rows = [(pid, row) for pid, row in pool.items()]
    else:
        rows = [(row['pid'], row) for row in pool]
    result = {}
    for pid, row in rows:
        pid = _int(pid, 'pid', 1)
        if pid in result:
            raise RuleError(f'duplicate pool player {pid}')
        if row.get('club') is None:
            raise RuleError(f'missing club for {pid}')
        result[pid] = dict(row, pos=_int(row['pos'], 'position', 1, 4),
                           market=_int(row['market'], 'market', 1))
        if not isinstance(row.get('can_buy', True), bool):
            raise RuleError(f'can_buy for {pid} must be boolean')
    return result

def legal_positions(ids, pos):
    ids = list(ids)
    return len(ids) == 11 and len(set(ids)) == 11 and tuple(
        sum(pos[i] == p for i in ids) for p in range(1,5)) in FORMATIONS

def _validate_lineup(squad, starters, bench, captain, vice, pos):
    squad = _ids(squad, 'squad')
    starters = _ids(starters, 'starters')
    bench = _ids(bench, 'bench')
    if len(squad) != 15 or len(starters) != 11 or len(bench) != 4:
        raise RuleError('need 15 squad players, 11 starters and 4 bench players')
    if set(starters) & set(bench) or set(starters+bench) != set(squad):
        raise RuleError('starters and bench must partition squad')
    if any(i not in pos for i in squad):
        raise RuleError('missing position metadata')
    if Counter(pos[i] for i in squad) != SQUAD_COUNTS:
        raise RuleError('squad must have 2 GK, 5 DEF, 5 MID, 3 FWD')
    if not legal_positions(starters, pos):
        raise RuleError('illegal starting formation')
    captain = _int(captain, 'captain', 1)
    vice = _int(vice, 'vice', 1)
    if captain not in starters or vice not in starters or captain == vice:
        raise RuleError('captain and vice must be distinct starters')
    return squad, starters, bench

def available_chips(state, gw=None):
    gw = state['next_gw'] if gw is None else gw
    gw = _int(gw, 'gameweek', 1, 38)
    half = '1' if gw <= 19 else '2'
    used = state.get('used_chips', {}).get(half, [])
    result = [c for c in CHIPS if c not in used]
    if not state['owned'] or gw == 1:
        result = [c for c in result if c not in ('wildcard', 'free_hit')]
    if state.get('last_chip') == 'free_hit':
        result = [c for c in result if c != 'free_hit']
    return result

def validate_decision(state, choice, pool, gw=None, chip=None):
    """Validate and normalize final batch; supplied accounting must agree exactly."""
    pool = normalize_pool(pool)
    gw = state['next_gw'] if gw is None else gw
    gw = _int(gw, 'gameweek', 1, 38)
    if gw != state['next_gw']:
        raise RuleError('gameweek must equal state next_gw; skipping rounds forbidden')
    if chip is None:
        chip = choice.get('chip') or None
    elif choice.get('chip') not in (None, '', chip):
        raise RuleError('contradictory chip arguments')
    if chip is not None and chip not in available_chips(state, gw):
        raise RuleError(f'chip unavailable in GW{gw}: {chip}')
    owned = state['owned']
    for pid, purchase in owned.items():
        _int(pid, 'owned pid', 1)
        _int(purchase, 'purchase price', 1)
    bank = _int(state['bank'], 'bank')
    ft = _int(state['ft'], 'ft', 0, 5)
    if owned and len(owned) != 15:
        raise RuleError('existing ownership must contain 15 players')
    squad = _ids(choice['squad'], 'squad')
    if not (set(squad) | set(owned)).issubset(pool):
        raise RuleError('pool must contain all selected and owned players')
    pos = {i: row['pos'] for i, row in pool.items()}
    squad, starters, bench = _validate_lineup(squad, choice['starters'], choice['bench'],
                                             choice['captain'], choice['vice'], pos)
    incoming = set(squad) - set(owned)
    outgoing = set(owned) - set(squad)
    if any(not pool[i].get('can_buy', True) for i in incoming):
        raise RuleError('attempted purchase of unavailable player')
    clubs = Counter(pool[i]['club'] for i in squad)
    if max(clubs.values()) > 3:
        # A club change can temporarily create a fourth player. A subsequent
        # manager transfer must restore the cap. The original legal snapshot is
        # kept while no manager transfers occur, so this may persist several GWs.
        previous = state.get('ownership_clubs', {})
        exception = (bool(owned) and not incoming and not outgoing
                     and set(previous) == set(owned)
                     and max(Counter(previous.values()).values()) <= 3
                     and any(previous[i] != pool[i]['club'] for i in owned))
        if not exception:
            raise RuleError('maximum three players per club')
    initial = not owned
    if initial and bank > 1000:
        raise RuleError('initial budget exceeds £100m')
    transfers = 0 if initial else len(incoming)
    paid = max(0, transfers-ft) if chip not in ('wildcard','free_hit') else 0
    prices = {i: row['market'] for i, row in pool.items()}
    bank_after = bank + sum(selling_price(owned[i], prices[i]) for i in outgoing)
    bank_after -= sum(prices[i] for i in incoming)
    if bank_after < 0:
        raise RuleError('insufficient funds')
    expected = {'incoming': incoming, 'outgoing': outgoing, 'transfers': transfers,
                'paid': paid, 'bank_after': bank_after}
    for key, expected_value in expected.items():
        if key in choice:
            supplied = set(choice[key]) if key in ('incoming','outgoing') else choice[key]
            if supplied != expected_value:
                raise RuleError(f'incorrect {key}: {supplied!r} != {expected_value!r}')
    if 'prices' in choice:
        for i in set(owned) | set(squad):
            if i not in choice['prices'] or choice['prices'][i] != prices[i]:
                raise RuleError(f'choice price disagrees with frozen market for {i}')
    result = deepcopy(choice)
    result.update(squad=sorted(squad), starters=starters, bench=bench,
                  incoming=sorted(incoming), outgoing=sorted(outgoing),
                  transfers=transfers, paid=paid, bank_after=bank_after,
                  prices=prices, chip=chip, gw=gw)
    return result

def apply_decision(state, choice, pool, gw=None, chip=None):
    """Return state entering next GW and audited decision; FH restoration included."""
    pool = normalize_pool(pool)
    choice = validate_decision(state, choice, pool, gw, chip)
    chip, gw = choice['chip'], choice['gw']
    result = deepcopy(state)
    if chip != 'free_hit':
        result['owned'] = {i: state['owned'][i] if i in state['owned'] else pool[i]['market']
                           for i in choice['squad']}
        result['bank'] = choice['bank_after']
        if not state['owned'] or choice['transfers']:
            result['ownership_clubs'] = {i: pool[i]['club'] for i in choice['squad']}
    result['ft'] = next_free(state['ft'], choice['transfers'], chip, not state['owned'])
    result['next_gw'] = gw+1
    result['last_chip'] = chip
    result.setdefault('used_chips', {'1': [], '2': []})
    if chip:
        result['used_chips'].setdefault('1' if gw <= 19 else '2', []).append(chip)
    return result, choice

def appearance(minutes, yellow_cards=0, red_cards=0):
    """Official participation includes a card even with zero pitch minutes."""
    for name, value in [('minutes', minutes), ('yellow_cards', yellow_cards), ('red_cards', red_cards)]:
        if not isinstance(value, Real) or not isfinite(value) or value < 0:
            raise MissingOutcomeError(f'unknown/invalid {name}')
    return bool(minutes > 0 or yellow_cards > 0 or red_cards > 0)

def settle(starters, bench, captain, vice, pos, points, active, chip=None):
    """Settle explicit outcomes. Bench priority/formation only, never points."""
    if chip not in (None, *CHIPS):
        raise RuleError('unknown chip')
    squad, starters, bench = _validate_lineup(list(starters)+list(bench), starters, bench,
                                             captain, vice, pos)
    for i in squad:
        if i not in points or i not in active:
            raise MissingOutcomeError(f'missing points/participation for {i}')
        if not isinstance(points[i], Real) or isinstance(points[i], bool) or not isfinite(points[i]):
            raise MissingOutcomeError(f'unknown/nonfinite points for {i}')
        if not isinstance(active[i], bool):
            raise MissingOutcomeError(f'participation must be explicit boolean for {i}')
        if not active[i] and points[i] != 0:
            raise RuleError(f'inactive player {i} has nonzero points; check cards/minutes')
    final, subs = list(starters), []
    if chip == 'bench_boost':
        final += bench
    else:
        gk = next(i for i in starters if pos[i] == 1)
        bgk = next(i for i in bench if pos[i] == 1)
        if not active[gk] and active[bgk]:
            final[final.index(gk)] = bgk
            subs.append((gk,bgk))
        missing = [i for i in starters if pos[i] != 1 and not active[i]]
        available = [i for i in bench if pos[i] != 1 and active[i]]
        best = None
        for k in range(min(len(missing),len(available))+1):
            for incoming in combinations(available,k):
                for outgoing in combinations(missing,k):
                    candidate = [i for i in final if i not in outgoing]+list(incoming)
                    if not legal_positions(candidate, pos):
                        continue
                    # Maximize filled slots, then lexicographic bench priority.
                    # Missing starters remain formation placeholders if unfilled.
                    key = (k, tuple(i in incoming for i in available))
                    if best is None or key > best[0]:
                        best = (key,candidate,list(zip(outgoing,incoming)))
        if best is not None:
            final = best[1]
            subs.extend(best[2])
    effective = captain if active[captain] else vice if active[vice] else None
    extra = 2 if chip == 'triple_captain' else 1
    base = sum(points[i] for i in final)
    bonus = extra*points[effective] if effective is not None else 0
    multipliers = {i: int(i in final)+(extra if i == effective else 0) for i in squad}
    return {'gross': base+bonus, 'base': base, 'captain_bonus': bonus,
            'effective_captain': effective, 'counted': final, 'subs': subs,
            'multipliers': multipliers,
            'contributions': {i: points[i]*multipliers[i] for i in squad},
            'autosub_gain': sum(points[b]-points[a] for a,b in subs),
            'direct_chip_points': sum(points[i] for i in bench) if chip == 'bench_boost'
              else points[effective] if chip == 'triple_captain' and effective is not None else 0}

def play_round(state, choice, pool, outcomes, gw=None, chip=None):
    """Atomic pure decision + settlement; missing outcomes leave caller state intact."""
    pool = normalize_pool(pool)
    next_state, decision = apply_decision(state, choice, pool, gw, chip)
    for i in decision['squad']:
        if i not in outcomes or not isinstance(outcomes[i], dict):
            raise MissingOutcomeError(f'missing outcome for {i}')
        if 'points' not in outcomes[i] or 'active' not in outcomes[i]:
            raise MissingOutcomeError(f'incomplete outcome for {i}')
    result = settle(decision['starters'], decision['bench'], decision['captain'], decision['vice'],
                    {i: row['pos'] for i,row in pool.items()},
                    {i: outcomes[i]['points'] for i in decision['squad']},
                    {i: outcomes[i]['active'] for i in decision['squad']}, decision['chip'])
    log = {'gw': decision['gw'], 'chip': decision['chip'], 'state_before': deepcopy(state),
           'decision': decision, 'state_after': deepcopy(next_state), 'settlement': result,
           'hit_cost': 4*decision['paid'], 'net_points': result['gross']-4*decision['paid']}
    return next_state, log
