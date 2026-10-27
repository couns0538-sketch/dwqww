"""scipy.special stand-ins: logsumexp (1-D / any shape, reduced over all elements) and log_ndtr (scalar or array)."""
import math

import numpy as np


def logsumexp(a):
    a = np.asarray(a, dtype=float)
    m = np.max(a)
    if not np.isfinite(m):
        return float(m) if m == -np.inf or np.isnan(m) else float("inf")
    return float(m + np.log(np.sum(np.exp(a - m))))


_SQRT2 = math.sqrt(2.0)
_LOG_SQRT_2PI = 0.5 * math.log(2.0 * math.pi)


def _log_ndtr_scalar(x):
    x = float(x)
    if math.isnan(x):
        return float("nan")
    if x > 6.0:
        # log(1 - q) with q = Phi(-x) tiny: log1p(-q)
        return math.log1p(-0.5 * math.erfc(x / _SQRT2))
    if x > -20.0:
        return math.log(0.5 * math.erfc(-x / _SQRT2))
    # asymptotic series of log Phi(x) for x -> -inf (SciPy uses the same expansion)
    z = x * x
    s, term, k = 1.0, 1.0, 1
    while k < 30:
        term *= -(2 * k - 1) / z
        if abs(term) < 1e-17:
            break
        s += term
        k += 1
    return -0.5 * z - math.log(-x) - _LOG_SQRT_2PI + math.log(s)


def log_ndtr(x):
    if np.ndim(x) == 0:
        return _log_ndtr_scalar(x)
    return np.vectorize(_log_ndtr_scalar, otypes=[float])(x)
