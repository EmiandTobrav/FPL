"""Learn a chip waiting-value component; forecasts and all other rules are fixed."""
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

CHIPS = ('triple_captain', 'bench_boost')
FEATURES = ['remaining_half', 'bank', 'free_transfers', 'has_squad',
            'current_pool_peak', 'future_pool_peak', 'owned_bottom4', 'current_pool_spread']


def features(pool, xp, state, gw):
    """Only frozen origin information and the manager's own state enter here."""
    xp = np.asarray(xp, float)
    if xp.shape[0] != len(pool) or not np.isfinite(xp).all(): raise ValueError('Invalid forecast')
    owned = set(map(int, state['owned']))
    valid = pool.can_buy.to_numpy(bool) | pool.pid.isin(owned).to_numpy()
    current = xp[valid, 0]
    if not len(current): raise ValueError('No eligible forecast pool')
    held = xp[pool.pid.isin(owned).to_numpy(), 0]
    end = 19 if gw <= 19 else 38
    horizon = min(xp.shape[1], end - gw + 1)
    future = xp[valid, 1:horizon]
    result = [(end - gw) / 18., state['bank'] / 1000., state['ft'] / 5., float(bool(owned)),
              float(current.max()), float(future.max()) if future.size else float(current.max()),
              float(np.sort(held)[:4].sum()) if len(held) else 0., float(current.std())]
    if not np.isfinite(result).all(): raise ValueError('Nonfinite policy features')
    return result


def fit(samples, cutoff, alpha=10.):
    """Separate fixed Ridge fits, using only completed prior-season labels."""
    import pandas as pd
    cutoff = pd.Timestamp(cutoff)
    models = {}
    for chip in CHIPS:
        rows = [r for r in samples if r['chip'] == chip and pd.Timestamp(r['label_available_at']) < cutoff]
        if not rows:
            models[chip] = None
            continue
        if any(pd.Timestamp(r['forecast_at']) >= cutoff for r in rows): raise ValueError('Future training origin')
        X = np.asarray([r['features'] for r in rows], float); y = np.asarray([r['wait_bonus'] for r in rows], float)
        scale = StandardScaler().fit(X)
        ridge = Ridge(alpha=alpha).fit(scale.transform(X), y)
        models[chip] = {'rows': len(rows), 'alpha': alpha, 'mean': scale.mean_.tolist(), 'scale': scale.scale_.tolist(),
            'coef': ridge.coef_.tolist(), 'intercept': float(ridge.intercept_),
            'training_seasons': sorted({r['season'] for r in rows}),
            'latest_label_available_at': max(r['label_available_at'] for r in rows),
            'latest_training_forecast_at': max(r['forecast_at'] for r in rows)}
    return models


def predict(model, x):
    value = float((np.asarray(x) - model['mean']) / model['scale'] @ np.asarray(model['coef']) + model['intercept'])
    if not np.isfinite(value): raise ValueError('Nonfinite learned value')
    return max(0., value)


def attach(adapter, models, pool, xp, state, gw):
    original = adapter.policy.reserve_value
    x = features(pool, xp, state, gw)
    trace = []
    def learned_reserve(chip, round_number):
        if round_number != gw: raise ValueError('Unexpected policy origin')
        model = models.get(chip)
        base = float(original(chip, round_number))
        value = base if model is None else predict(model, x)
        trace.append({'chip': chip, 'old_reserve': base, 'reserve': value, 'learned': model is not None,
                      'features': x if model is not None else None})
        return value
    adapter.policy.reserve_value = learned_reserve
    return trace
