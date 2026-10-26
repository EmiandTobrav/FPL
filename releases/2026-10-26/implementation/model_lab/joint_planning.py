"""Compare explicit chip schedules by predicted net points, with no reserves."""
import copy
from itertools import product, combinations
import numpy as np
from .common import digest
from . import point_planner


def schedules(rules, state, gw, horizon):
    """Inventory-only enumeration; every realised transition is validated too."""
    if not 1 <= horizon <= 2 or gw+horizon-1 > 38: raise ValueError('Invalid planning horizon')
    result = []
    for sequence in product((None, *rules.CHIPS), repeat=horizon):
        used = copy.deepcopy(state['used_chips']); last = state['last_chip']; legal = True
        for offset, chip in enumerate(sequence):
            at = gw+offset; half = '1' if at <= 19 else '2'
            if chip is not None:
                if chip in used[half] or ((at == 1 or (offset == 0 and not state['owned'])) and chip in ('wildcard', 'free_hit')) or (chip == 'free_hit' and last == 'free_hit'):
                    legal = False; break
                used[half].append(chip)
            last = chip
        if legal: result.append(list(sequence))
    return result


def expected_points(choice, pool, values):
    values = dict(zip(pool.pid, values))
    counted = choice['squad'] if choice['chip'] == 'bench_boost' else choice['starters']
    multiplier = 2 if choice['chip'] == 'triple_captain' else 1
    return float(sum(values[i] for i in counted) + multiplier*values[choice['captain']] - 4*choice['paid'])


def evaluate(adapter, pool, xp, state, gw, sequence):
    """Joint transfer/FT plan; FH segments restore original ownership and cash."""
    current = copy.deepcopy(state); steps = []; offset = 0; native_objective = 0.
    while offset < len(sequence):
        end = offset+1
        if sequence[offset] != 'free_hit':
            while end < len(sequence) and sequence[end] != 'free_hit': end += 1
        chips = sequence[offset:end]
        choice = point_planner.choose(adapter, pool, xp[:, offset:end], current['owned'], current['bank'], current['ft'], chips)
        native_objective += choice['objective']
        decoded = [choice] + choice['plan']
        if len(decoded) != len(chips): raise ValueError('Incomplete native plan')
        for j, raw in enumerate(decoded):
            at = offset+j; clean = {k: v for k, v in raw.items() if k not in ('plan', 'objective')}
            after, legal = adapter.engine.apply_decision(current, clean, pool.to_dict('records'), gw+at, sequence[at])
            value = expected_points(legal, pool, xp[:, at])
            steps.append({'gw': gw+at, 'choice': legal, 'state_before': current, 'state_after': after, 'expected_net_points': value})
            current = after
        offset = end
    total = float(sum(r['expected_net_points'] for r in steps))
    if abs(total-native_objective) > 1e-5: raise ValueError('Native objective contains non-point terms or decoding mismatch')
    return {'id': digest(sequence), 'schedule': sequence, 'steps': steps, 'expected_net_points': total}


def plans(adapter, pool, xp, state, gw, official_blank=False):
    xp = np.asarray(xp, float); before = digest(xp.tolist())
    horizon = min(2, xp.shape[1], 39-gw)
    if official_blank:
        # Same official retained-squad wait used by all prior experiments.
        ids = sorted(state['owned']); pos = dict(zip(pool.pid, pool.pos))
        first = next(list(c) for c in combinations(ids, 11) if adapter.engine.legal_positions(c, pos))
        raw = {'squad': ids, 'starters': first, 'bench': sorted(set(ids)-set(first), key=lambda i: (pos[i] != 1, i)), 'captain': first[0], 'vice': first[1]}
        after, choice = adapter.engine.apply_decision(state, raw, pool.to_dict('records'), gw)
        return [{'id': digest([None]), 'schedule': [None], 'expected_net_points': 0.,
                 'steps': [{'gw': gw, 'choice': choice, 'state_before': state, 'state_after': after, 'expected_net_points': 0.}]}]
    result = [evaluate(adapter, pool, xp, state, gw, seq) for seq in schedules(adapter.engine, state, gw, horizon)]
    # A node-limited solve can miss a plainly beneficial feasible incumbent.
    # Replay the same troops/lineups with a point-multiplying chip substituted
    # for an ordinary round. This changes only legal state and actual expected
    # points; it adds no bonus, reserve, penalty or extra solver work.
    by_sequence = {tuple(r['schedule']): r for r in result}
    accounting = {'incoming', 'outgoing', 'transfers', 'paid', 'bank_after', 'free_before', 'prices', 'gw'}
    for base in list(result):
        for at, old_chip in enumerate(base['schedule']):
            if old_chip is not None: continue
            for chip in ('bench_boost', 'triple_captain'):
                seq = list(base['schedule']); seq[at] = chip; key = tuple(seq)
                if key not in by_sequence: continue
                current = copy.deepcopy(state); steps = []
                for j, old_step in enumerate(base['steps']):
                    raw = {k: v for k, v in old_step['choice'].items() if k not in accounting}
                    raw['chip'] = seq[j]
                    after, choice = adapter.engine.apply_decision(current, raw, pool.to_dict('records'), gw+j, seq[j])
                    steps.append({'gw': gw+j, 'choice': choice, 'state_before': current, 'state_after': after,
                                  'expected_net_points': expected_points(choice, pool, xp[:, j])})
                    current = after
                total = float(sum(s['expected_net_points'] for s in steps))
                if total > by_sequence[key]['expected_net_points'] + 1e-8:
                    by_sequence[key] = {'id': digest(seq), 'schedule': seq, 'steps': steps,
                                        'expected_net_points': total, 'source': 'feasible_same_team_chip_variant'}
    result = [by_sequence[tuple(r['schedule'])] for r in result]
    if digest(xp.tolist()) != before: raise ValueError('Forecast mutation')
    return result


def select(options, reserve_function=None):
    """Pure mode never calls reserve code; optional legacy cost is an ablation."""
    if not options: raise ValueError('No legal plans')
    scores = []
    for option in options:
        cost = 0. if reserve_function is None else sum(reserve_function(step['choice']['chip'], step['gw']) for step in option['steps'] if step['choice']['chip'])
        scores.append(float(option['expected_net_points']-cost))
    # Equal predicted returns: prefer fewer hits/transfers, then no current chip.
    # These rules break equal scores; they never subtract from a point score.
    def key(j):
        c = options[j]['steps'][0]['choice']
        return (scores[j], -c['paid'], -c['transfers'], c['chip'] is None, options[j]['id'])
    return max(range(len(options)), key=key), scores
