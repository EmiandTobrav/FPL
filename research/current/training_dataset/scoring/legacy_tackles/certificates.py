"""Exact nonnegative conservation; no inference from omission or positive residual."""
from bounds import missing, counter


def zero_certificate(total, values, selected):
    try:
        total = counter({'total':total}, 'total')
        if not missing(selected) and counter({'selected': selected}, 'selected') != 0:
            return None
        actual = [counter({'value':v}, 'value') for v in values if not missing(v)]
    except ValueError:
        return None
    return 0 if sum(actual) == total else None
