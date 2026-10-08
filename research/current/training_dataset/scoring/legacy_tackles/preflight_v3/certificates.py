"""Exact nonnegative conservation; no inference from omission or positive residual."""
from bounds import known, counter


def zero_certificate(total, values, selected):
    if not known(total) or (known(selected) and selected != 0):
        return None
    try:
        total = counter({'total':total}, 'total')
        actual = [counter({'value':v}, 'value') for v in values if known(v)]
    except ValueError:
        return None
    return 0 if sum(actual) == total else None
