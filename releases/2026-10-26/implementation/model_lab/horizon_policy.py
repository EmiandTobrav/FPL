"""Stage C: bounded H3/H8 rollout. Accepts current-origin inputs only.

No file I/O, outcomes or future-origin loader is available to this module.
The root action generator is unchanged. Truncation has no improvement guarantee.
"""
import copy
import numpy as np
from .common import digest
from . import manager_policy as base


def shortlist(options, width=2):
    if width < 1 or not options:
        raise ValueError('Positive width and nonempty proposals required')
    ranked = sorted(range(len(options)), key=lambda j: (options[j]['base_score'], options[j]['id']), reverse=True)
    selected, seen = [], set()
    for j in ranked:
        key = digest(options[j]['after'])
        if key not in seen:
            selected.append(j); seen.add(key)
        if len(selected) == width:
            break
    return selected


def reward(option, pool, values, reserve_function, gw):
    choice = option['choice']
    reserve = 0. if choice['chip'] is None else reserve_function(choice['chip'], gw)
    return float(base.current_xp(choice, dict(zip(pool.pid, values))) - reserve)


def choose(adapter, pool, xp, history, state, gw, *, horizon=3, width=2,
           official_blank=False, proposals=base.proposals):
    """Same reward/horizon as root base score; replace hold with base actions.

    Frozen history is passed solely because the original proposal encoder needs
    it; unlearned selection uses only base_score. No metadata is advanced from
    later origins. Each continuation sees only the remaining chosen-horizon forecast suffix; the existing proposal planner
    itself retains its local H3 rule.
    """
    xp = np.asarray(xp, float)
    if horizon not in (3, 8) or width != 2 or xp.ndim != 2 or not np.isfinite(xp).all():
        raise ValueError('Only locked H3/H8 two-branch comparisons are supported')
    original = digest({'xp': xp.tolist(), 'state': state, 'history': history})
    options = proposals(adapter, pool, xp, history, state, gw, official_blank)
    control = base.select(options, None)[0]
    indices = shortlist(options, width)
    if control not in indices:
        raise ValueError('Reference action omitted')
    horizon = min(horizon, xp.shape[1], 39-gw)
    branches = []
    for index in indices:
        first = options[index]
        steps = [{'gw': gw, 'state_before': copy.deepcopy(state), 'selected': first,
                  'reward': 0. if official_blank else reward(first, pool, xp[:, 0], adapter.policy.reserve_value, gw)}]
        current = copy.deepcopy(first['after'])
        if not official_blank:
            for offset in range(1, horizon):
                future = proposals(adapter, pool, xp[:, offset:horizon], history, current, gw+offset)
                selected_index = base.select(future, None)[0]
                selected = future[selected_index]
                steps.append({'gw': gw+offset, 'state_before': current, 'options': future,
                              'selected_index': selected_index, 'selected': selected,
                              'reward': reward(selected, pool, xp[:, offset], adapter.policy.reserve_value, gw+offset)})
                current = copy.deepcopy(selected['after'])
        score = float(sum(.9**j * step['reward'] for j, step in enumerate(steps)))
        branches.append({'root_index': index, 'steps': steps, 'score': score})
    best = max(branches, key=lambda b: (b['score'], b['root_index'] == control, options[b['root_index']]['id']))
    if digest({'xp': xp.tolist(), 'state': state, 'history': history}) != original:
        raise ValueError('Input mutation')
    return {'options': options, 'control_index': control, 'shortlist': indices,
            'branches': branches, 'selected_index': best['root_index'], 'selected': options[best['root_index']],
            'horizon': horizon, 'official_blank': official_blank}
