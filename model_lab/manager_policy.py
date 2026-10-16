"""Bounded full-decision policy: legal proposals and episodic return learning.

No outcomes, player identities, or future-origin data enter proposal ranking.
The unchanged planner supplies candidates; the learned model selects a complete
action, including transfers, lineup, captain, bench, and every available chip.
"""
import copy
from itertools import combinations
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from .common import digest

CHIPS = ('wildcard', 'free_hit', 'bench_boost', 'triple_captain')
HISTORY = ('f_last5_minutes_mean', 'f_last5_played_round_share', 'f_history_missing')
FEATURES = [
    'remaining_season', 'remaining_half', 'second_half', 'bank_after', 'free_after',
    'transfers', 'paid', 'initial_squad', 'squad_sale_value',
    'current_net_xp', 'captain_xp', 'vice_xp', 'bench_xp', 'starter_xp_std',
    'retained_next_xp', 'retained_second_xp', 'retained_future_bench',
    'squad_future_peak', 'captain_minutes', 'vice_minutes', 'starter_minutes',
    'bench_minutes', 'captain_play_share', 'vice_play_share', 'bench_play_share',
    'history_missing_share', 'bank_remaining', 'free_remaining',
] + ['used_' + c for c in CHIPS] + ['available_after_' + c for c in CHIPS] + ['option_horizon_' + c for c in CHIPS]


def lineup(squad, pool, values, second=False):
    """Best or second-best expected-point legal XI for one fixed squad."""
    pos = dict(zip(pool.pid, pool.pos)); ids = sorted(map(int, squad))
    groups = {k: sorted([i for i in ids if pos[i] == k], key=lambda i: (-values[i], i)) for k in range(1, 5)}
    choices = []
    for d in range(3, 6):
        for m in range(2, 6):
            f = 10 - d - m
            if not 1 <= f <= 3: continue
            counts = {1: 1, 2: d, 3: m, 4: f}
            selected = [i for k in range(1, 5) for i in groups[k][:counts[k]]]
            if len(selected) != 11: continue
            choices.append(selected)
            # Single same-position substitutions let bench/keeper choices vary,
            # even when the top two formations happen to select the same XI.
            for k in range(1, 5):
                if len(groups[k]) > counts[k]:
                    alt = [i for i in selected if i != groups[k][counts[k]-1]] + [groups[k][counts[k]]]
                    choices.append(alt)
    unique = {tuple(sorted(x)): x for x in choices}
    ranked = sorted(unique.values(), key=lambda x: (-sum(values[i] for i in x), tuple(sorted(x))))
    starters = ranked[min(int(second), len(ranked)-1)]
    ordered = sorted(starters, key=lambda i: (-values[i], i))
    bench = sorted(set(ids) - set(starters), key=lambda i: (pos[i] != 1, -values[i], i))
    return {'squad': ids, 'starters': sorted(starters), 'bench': bench, 'captain': ordered[0], 'vice': ordered[1]}


def current_xp(choice, values):
    counted = choice['squad'] if choice['chip'] == 'bench_boost' else choice['starters']
    extra = 2 if choice['chip'] == 'triple_captain' else 1
    return sum(values[i] for i in counted) + extra * values[choice['captain']] - 4 * choice['paid']


def encode(pool, xp, history, before, after, choice, rules, gw):
    """Action/current-origin features. FH continuation uses the restored squad."""
    xp = np.asarray(xp, float)
    if xp.shape[0] != len(pool) or not np.isfinite(xp).all(): raise ValueError('Invalid forecasts')
    values = dict(zip(pool.pid, xp[:, 0])); index = {int(i): j for j, i in enumerate(pool.pid)}
    squad = choice['squad']; starters = choice['starters']; bench = choice['bench']
    cap, vice = choice['captain'], choice['vice']; retained = list(after['owned'])
    if not retained: raise ValueError('No retained squad')
    forward = []; bench_future = 0.
    for j in (1, 2):
        if gw + j <= 38 and j < xp.shape[1]:
            forecast = dict(zip(pool.pid, xp[:, j])); row = lineup(retained, pool, forecast)
            forward.append(sum(forecast[i] for i in row['starters']) + forecast[row['captain']])
            if j == 1: bench_future = sum(forecast[i] for i in row['bench'])
        else: forward.append(0.)
    end = 19 if gw <= 19 else 38
    # At the end of a half, unused current-half chips expire, rather than being
    # incorrectly valued as next-half inventory. The second set is separate.
    available = [] if gw == end else [c for c in CHIPS if c not in after['used_chips']['1' if gw <= 19 else '2']]
    def mean(ids, column):
        return float(np.mean([history[int(i)][column] for i in ids]))
    prices = dict(zip(pool.pid, pool.market))
    sale = after['bank'] + sum(rules.selling_price(after['owned'][i], int(prices[i])) for i in retained)
    remaining = (38-gw)/37.; half = (end-gw)/18.
    result = [remaining, half, float(gw > 19), after['bank']/1000., after['ft']/5.,
        choice['transfers']/15., float(choice['paid']), float(not before['owned']), sale/1000.,
        current_xp(choice, values)/100., values[cap]/20., values[vice]/20., sum(values[i] for i in bench)/30.,
        float(np.std([values[i] for i in starters]))/10., forward[0]/100., forward[1]/100., bench_future/30.,
        float(max(xp[index[i], :min(xp.shape[1], 39-gw)].max() for i in retained))/20.,
        mean([cap], HISTORY[0])/90., mean([vice], HISTORY[0])/90., mean(starters, HISTORY[0])/90.,
        mean(bench, HISTORY[0])/90., mean([cap], HISTORY[1]), mean([vice], HISTORY[1]), mean(bench, HISTORY[1]),
        mean(squad, HISTORY[2]), after['bank']/1000.*remaining, after['ft']/5.*remaining,
    ] + [float(choice['chip'] == c) for c in CHIPS] + [float(c in available) for c in CHIPS] + [half*float(c in available) for c in CHIPS]
    if len(result) != len(FEATURES) or not np.isfinite(result).all(): raise ValueError('Invalid manager features')
    return list(map(float, result))


def identity(choice):
    return digest({k: choice[k] for k in ['squad', 'starters', 'bench', 'captain', 'vice', 'chip']})


def proposals(adapter, pool, xp, history, state, gw, official_blank=False):
    """At most seven native planner calls normally; shared hard cap stays 40.

    Three free variants per base expose captain, legal XI, and bench ordering.
    No solver failure is swallowed and no result-based proposal search is used.
    """
    xp = np.asarray(xp, float); before_hash = digest(xp.tolist())
    rules = adapter.engine; values = dict(zip(pool.pid, xp[:, 0]))
    if official_blank:
        if not state['owned']: raise ValueError('Blank requires retained squad')
        pos = dict(zip(pool.pid, pool.pos)); ids = sorted(state['owned'])
        first = next(list(c) for c in combinations(ids, 11) if rules.legal_positions(c, pos))
        choice = {'squad': ids, 'starters': first, 'bench': sorted(set(ids)-set(first), key=lambda i: (pos[i] != 1, i)),
                  'captain': first[0], 'vice': first[1]}
        after, choice = rules.apply_decision(state, choice, pool.to_dict('records'), gw)
        return [{'id': identity(choice), 'family': 'official_blank_wait', 'choice': choice, 'after': after,
                 'features': encode(pool, xp, history, state, after, choice, rules, gw), 'base_score': 0.}]
    base = []
    available = [None] + list(rules.available_chips(state, gw))
    for chip in available:
        planned = adapter.plan(pool, xp, state, gw, chip)
        base.append((f'h3_{chip or "ordinary"}', planned['choice']['squad'], chip))
    if state['owned']:
        planned = adapter.plan(pool, xp[:, :1], state, gw)
        base.append(('h1_ordinary', planned['choice']['squad'], None))
        for chip in [None] + [c for c in ('bench_boost', 'triple_captain') if c in available]:
            base.append((f'keep_{chip or "ordinary"}', sorted(state['owned']), chip))
    result = {}; records = pool.to_dict('records')
    for family, squad, chip in base:
        best = lineup(squad, pool, values)
        alternate = lineup(squad, pool, values, second=True)
        other_cap = copy.deepcopy(best); other_cap['captain'], other_cap['vice'] = best['vice'], best['captain']
        other_bench = copy.deepcopy(best); other_bench['bench'] = best['bench'][:1] + list(reversed(best['bench'][1:]))
        for variant, choice in [('best', best), ('captain', other_cap), ('lineup', alternate), ('bench', other_bench)]:
            after, choice = rules.apply_decision(state, dict(choice, chip=chip), records, gw, chip)
            key = identity(choice)
            if key in result: continue
            x = encode(pool, xp, history, state, after, choice, rules, gw)
            # Fixed short-horizon prior, also used by the no-learning ablation.
            reserve = 0. if chip is None else float(adapter.policy.reserve_value(chip, gw))
            base_score = 100*x[9] + .9*100*x[14] + .81*100*x[15] - reserve
            result[key] = {'id': key, 'family': family + '_' + variant, 'choice': choice,
                          'after': after, 'features': x, 'base_score': float(base_score)}
    if digest(xp.tolist()) != before_hash: raise ValueError('Forecast mutation')
    return sorted(result.values(), key=lambda r: r['id'])


def predict(model, x):
    if model is None: return 0.
    if model['features'] != FEATURES: raise ValueError('Manager feature schema changed')
    value = (np.asarray(x)-model['mean'])/model['scale'] @ np.asarray(model['coef']) + model['intercept']
    if not np.isfinite(value): raise ValueError('Invalid policy prediction')
    return float(value)


def select(options, model, rng=None, epsilon=0.):
    scores = [r['base_score'] + predict(model, r['features']) for r in options]
    if not scores: raise ValueError('No legal proposals')
    exploratory = rng is not None and epsilon > 0 and rng.random() < epsilon
    # Sample base families first, so duplicate lineup/captain variants do not
    # accidentally give one chip or squad family a larger exploration weight.
    if exploratory:
        groups = sorted({r['family'].rsplit('_', 1)[0] for r in options})
        group = groups[int(rng.integers(len(groups)))]
        subset = [j for j, r in enumerate(options) if r['family'].rsplit('_', 1)[0] == group]
        index = subset[int(rng.integers(len(subset)))]
    else: index = max(range(len(options)), key=lambda j: (scores[j], options[j]['id']))
    return index, list(map(float, scores)), bool(exploratory)


def episode_samples(logs, season, label_available_at):
    """Undiscounted realised return through GW38; historical training only."""
    if len(logs) != 38 or [r['gw'] for r in logs] != list(range(1, 39)):
        raise ValueError('Learning requires a complete contiguous season')
    total = 0.; result = []
    for row in reversed(logs):
        total += row['net_points']
        action = row['selected']
        result.append({'season': season, 'round': row['gw'], 'forecast_at': row['forecast_at'],
            'label_available_at': label_available_at, 'features': action['features'],
            'base_score': action['base_score'], 'return_to_go': total,
            'residual_return': total-action['base_score'], 'episode': row['episode'],
            'action_id': action['id']})
    return list(reversed(result))


def fit(samples, cutoff, alpha=50.):
    import pandas as pd
    cutoff = pd.Timestamp(cutoff)
    if not samples: raise ValueError('No full-season training samples')
    for r in samples:
        if pd.Timestamp(r['label_available_at']) >= cutoff or pd.Timestamp(r['forecast_at']) >= cutoff:
            raise ValueError('Training label/origin crosses evaluation cutoff')
        if int(r['season'][:4]) >= cutoff.year: raise ValueError('Current/future training season')
    x = np.asarray([r['features'] for r in samples], float)
    y = np.asarray([r['residual_return'] for r in samples], float)
    if not np.isfinite(x).all() or not np.isfinite(y).all() or x.shape[1] != len(FEATURES): raise ValueError('Invalid learning sample')
    scaler = StandardScaler().fit(x); model = Ridge(alpha=alpha).fit(scaler.transform(x), y)
    return {'features': FEATURES, 'alpha': alpha, 'rows': len(samples), 'episodes': len({r['episode'] for r in samples}),
        'training_seasons': sorted({r['season'] for r in samples}), 'cutoff': str(cutoff),
        'latest_label_available_at': max(r['label_available_at'] for r in samples),
        'mean': scaler.mean_.tolist(), 'scale': scaler.scale_.tolist(),
        'coef': model.coef_.tolist(), 'intercept': float(model.intercept_)}
