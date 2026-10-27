"""Offline paired-score statistics for Forge gates (S06 v2, stdlib only).

v2 (S06-1): the PRIMARY LLR is the exact fastchess 1.8.2 normalized-pentanomial GSPRT: LLR = N * sum_i
phat_i * log(p1_i / p0_i), where p0 / p1 are the maximum-likelihood cell probabilities under the t-value
constraints (mu - 0.5) / sigma = t0 / t1, t = nElo / (800 / ln 10) * sqrt(2) (constrained MLE, Van den Bergh,
"Comments on normalized Elo", section 4.1). ``fastchess_llr`` is a line-by-line port of fastchess
v1.8.2-alpha app/src/matchmaking/sprt/sprt.cpp (SPRT::getLLR for pentanomial counts, getLLR_normalized,
getLLR_logistic, itp; MIT License, Copyright (c) 2023 disservin): zero counts regularized to 1e-3, the MLE
fixed point started from the uniform distribution with at most 10 iterations (stop at max change < 1e-4),
theta solved by the ITP bracketing method (epsilon 1e-7; logistic 1e-3), sums in the source's order.
``converged_llr`` is the fully converged constrained MLE (port of opus_round1/sol_S44 exact_llr, numpy ->
stdlib); it is reported next to the primary value as a reference. Known answer: G120 Ptnml
[5, 74, 252, 119, 14], [0, 10] -> LLR 2.99, Elo 23.62 +/- 11.90. The Gaussian paired-score LLR of v1 is
kept as the SECONDARY cross-check (it is off by up to ~0.1 near the bounds). fastchess-style displayed
figures (Elo +/- as half the Elo span of the 95% score interval, nElo +/-, LOS) are added; v1's
delta-method interval stays as an extra.

Wald threshold crossings are diagnostics and never authorize acceptance.
v1: forge_sol_S06_statistics_20261026.py (Sol, 17aa0cae), unchanged; this file is the v2 fix.
"""
from collections.abc import Sequence
import math
from numbers import Real


_LOG10 = math.log(10.0)
_C = 800.0 / _LOG10
_Z95 = 1.959963984540054
_PAIR_SCORES = (0.0, 0.25, 0.5, 0.75, 1.0)
EXACT_MODEL = ('fastchess 1.8.2 normalized-pentanomial GSPRT (port of sprt.cpp v1.8.2-alpha getLLR/'
               'getLLR_normalized): LLR = total*sum(phat*log(p1/p0)), p0/p1 = MLE under the t-value constraints '
               't = sqrt(2)*nElo/(800/ln10); zero counts -> 1e-3')
LOGISTIC_MODEL = ('fastchess 1.8.2 logistic pentanomial GSPRT (port of sprt.cpp v1.8.2-alpha getLLR_logistic): '
                  'MLE under the expected-score constraint mu = score(Elo); zero counts -> 1e-3')


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(name + ' must be a finite real number')
    try:
        value = float(value)
    except (OverflowError, ValueError):
        raise ValueError(name + ' must be finite') from None
    if not math.isfinite(value):
        raise ValueError(name + ' must be finite')
    return value


def _finite(value):
    return value if value is not None and math.isfinite(value) else None


def _logistic_elo(score):
    if score is None or not 0.0 < score < 1.0:
        return None
    return _finite((400.0 / _LOG10) * (math.log(score) - math.log1p(-score)))


def _logistic_score(elo):
    # This algebraic split avoids exponent overflow for finite Elo bounds.
    exponent = -(elo / 400.0) * _LOG10
    if exponent >= 0.0:
        small = math.exp(-exponent)
        return small / (1.0 + small)
    return 1.0 / (1.0 + math.exp(exponent))


# ------------------------------------------------------------------ exact GSPRT (S06-1)
def _secular(phat, a, x0=None):
    """Root x of sum_i phat_i a_i / (1 + x a_i) = 0 (fishtest LLRcalc.secular): Newton inside a bisection
    bracket built from the occupied cells (an empty cell has MLE probability 0 for every x). None when the
    occupied a_i do not change sign (no interior root)."""
    occupied = [i for i, p in enumerate(phat) if p > 0.0]
    if not occupied:
        return None
    a_max = max(a[i] for i in occupied)
    a_min = min(a[i] for i in occupied)
    if not (a_max > 0.0 and a_min < 0.0):
        return None
    lo, hi = -1.0 / a_max, -1.0 / a_min
    x = x0 if x0 is not None and lo < x0 < hi else 0.0
    for _ in range(200):
        d = [1.0 + x * a[i] for i in occupied]
        f = math.fsum(phat[i] * a[i] / di for i, di in zip(occupied, d))
        fp = -math.fsum(phat[i] * a[i] * a[i] / (di * di) for i, di in zip(occupied, d))
        # f decreases strictly in x: f > 0 means the root lies to the right.
        if f > 0.0:
            lo = x
        else:
            hi = x
        xn = x - f / fp if fp != 0.0 else math.nan
        if not math.isfinite(xn) or xn <= lo or xn >= hi:
            xn = 0.5 * (lo + hi)
        if abs(xn - x) <= 1e-15 * (1.0 + abs(x)):
            return xn
        x = xn
    return x


def _mle_tvalue(phat, t, iterations=100):
    """MLE of the five cell probabilities under (mu - 0.5) / sigma = t (fishtest LLRcalc.MLE_tvalue).
    t = 0 needs one secular solve; otherwise the fixed point is iterated from phat to 1e-14."""
    if t == 0.0:
        a = [score - 0.5 for score in _PAIR_SCORES]
        x = _secular(phat, a)
        if x is None:
            return None
        return [p / (1.0 + x * ai) if p > 0.0 else 0.0 for p, ai in zip(phat, a)]
    pdf, x = list(phat), None
    for _ in range(iterations):
        mu = math.fsum(p * s for p, s in zip(pdf, _PAIR_SCORES))
        variance = math.fsum(p * s * s for p, s in zip(pdf, _PAIR_SCORES)) - mu * mu
        sigma = math.sqrt(max(variance, 1e-300))
        a = [s - 0.5 - t * sigma * (1.0 + ((mu - s) / sigma) ** 2) / 2.0 for s in _PAIR_SCORES]
        x = _secular(phat, a, x)
        if x is None:
            return None
        new = [p / (1.0 + x * ai) if p > 0.0 else 0.0 for p, ai in zip(phat, a)]
        converged = max(abs(u - v) for u, v in zip(new, pdf)) < 1e-14
        pdf = new
        if converged:
            break
    return pdf


def _mle_expected(phat, score):
    """MLE of the cell probabilities under the mean-score constraint mu = score (fishtest MLE_expected)."""
    a = [s - score for s in _PAIR_SCORES]
    x = _secular(phat, a)
    if x is None:
        return None
    return [p / (1.0 + x * ai) if p > 0.0 else 0.0 for p, ai in zip(phat, a)]


def _ieee_div(x, y):
    """C++ double division (x / +-0 -> +-inf or NaN) instead of Python's ZeroDivisionError."""
    try:
        return x / y
    except ZeroDivisionError:
        if x == 0.0 or math.isnan(x):
            return math.nan
        return math.copysign(math.inf, x) * math.copysign(1.0, y)


def _itp(f, a, b, f_a, f_b, k_1, k_2, n_0, epsilon):
    """Port of fastchess sprt.cpp itp() (Oliveira and Takahashi 2020), including its argument order."""
    if f_a > 0:
        a, b = b, a
        f_a, f_b = f_b, f_a
    n_half = math.ceil(math.log2(abs(b - a) / (2.0 * epsilon)))
    n_max = n_half + n_0
    i = 0
    while abs(b - a) > 2.0 * epsilon:
        x_half = (a + b) / 2.0
        r = epsilon * math.pow(2.0, n_max - i) - (b - a) / 2.0
        delta = k_1 * math.pow(b - a, k_2)
        x_f = _ieee_div(f_b * a - f_a * b, f_b - f_a)
        sigma = _ieee_div(x_half - x_f, abs(x_half - x_f))
        x_t = x_f + sigma * delta if delta <= abs(x_half - x_f) else x_half
        x_itp = x_t if abs(x_t - x_half) <= r else x_half - sigma * r
        f_itp = f(x_itp)
        if f_itp == 0.0:
            a = x_itp
            b = x_itp
        elif math.copysign(1.0, f_itp) < 0.0:
            a = x_itp
            f_a = f_itp
        else:
            b = x_itp
            f_b = f_itp
        i += 1
    return (a + b) / 2.0


def _seq_mean(x, p):
    result = 0.0
    for xi, pi in zip(x, p):
        result += xi * pi
    return result


def fastchess_llr(counts, e0=0.0, e1=10.0, units='nelo'):
    """fastchess v1.8.2-alpha SPRT::getLLR for pentanomial counts [LL, LD, WL+DD, WD, WW] (the primary LLR).
    units='nelo' -> model normalized (the PC gates); 'logistic' -> getLLR_logistic. None if not finite."""
    regularized = [1e-3 if c == 0 else float(c) for c in counts]
    total = 0.0
    for c in (regularized[4], regularized[3], regularized[2], regularized[1], regularized[0]):
        total += c  # source order: WW + WD + WL_DD + LD + LL
    probs = [c / total for c in regularized]
    scores = list(_PAIR_SCORES)
    n = len(scores)

    if units == 'nelo':
        def mle(mu_ref, t_star):
            p = [1.0 / n] * n
            for _ in range(10):
                mu = _seq_mean(scores, p)
                var = 0.0
                for pi, ai in zip(p, scores):
                    var += pi * (ai - mu) * (ai - mu)
                phi = []
                for ai in scores:
                    sigma = math.sqrt(var)
                    q = _ieee_div(ai - mu, sigma)
                    phi.append(ai - mu_ref - 0.5 * t_star * sigma * (1.0 + q * q))
                u, v = min(phi), max(phi)
                min_theta, max_theta = _ieee_div(-1.0, v), _ieee_div(-1.0, u)

                def f(x, phi=phi):
                    result = 0.0
                    for ph, fi in zip(probs, phi):
                        result += _ieee_div(ph * fi, 1.0 + x * fi)
                    return result
                theta = _itp(f, min_theta, max_theta, math.inf, -math.inf, 0.1, 2.0, 0.99, 1e-7)
                max_diff = 0.0
                for i in range(n):
                    new = _ieee_div(probs[i], 1.0 + theta * phi[i])
                    max_diff = max(max_diff, abs(new - p[i]))
                    p[i] = new
                if max_diff < 1e-4:
                    break
            return p
        t0 = math.sqrt(2.0) * e0 / (800.0 / math.log(10))
        t1 = math.sqrt(2.0) * e1 / (800.0 / math.log(10))
        p0, p1 = mle(0.5, t0), mle(0.5, t1)
    else:
        def mle_expected(s):
            min_theta = _ieee_div(-1.0, scores[n - 1] - s)
            max_theta = _ieee_div(-1.0, scores[0] - s)

            def f(x):
                result = 0.0
                for ai, ph in zip(scores, probs):
                    result += _ieee_div(ph * (ai - s), 1.0 + x * (ai - s))
                return result
            theta = _itp(f, min_theta, max_theta, math.inf, -math.inf, 0.1, 2.0, 0.99, 1e-3)
            return [_ieee_div(ph, 1 + theta * (ai - s)) for ai, ph in zip(scores, probs)]
        p0, p1 = mle_expected(_logistic_score(e0)), mle_expected(_logistic_score(e1))
    try:
        lpr = [math.log(q1) - math.log(q0) for q0, q1 in zip(p0, p1)]
    except ValueError:
        return None
    return _finite(total * _seq_mean(lpr, probs))


def converged_llr(counts, e0=0.0, e1=10.0, units='nelo'):
    """Fully converged constrained-MLE GSPRT LLR (S44 port; no zero-count regularization); None when
    undefined (empty, degenerate, no interior root). Reference value next to fastchess_llr."""
    pairs = sum(counts)
    if pairs <= 0:
        return None
    phat = [c / pairs for c in counts]
    if units == 'nelo':
        t0, t1 = e0 / _C * math.sqrt(2.0), e1 / _C * math.sqrt(2.0)
        p0, p1 = _mle_tvalue(phat, t0), _mle_tvalue(phat, t1)
    else:
        p0, p1 = _mle_expected(phat, _logistic_score(e0)), _mle_expected(phat, _logistic_score(e1))
    if p0 is None or p1 is None:
        return None
    try:
        terms = [ph * math.log(q1 / q0) for ph, q0, q1 in zip(phat, p0, p1) if ph > 0.0]
    except (ValueError, ZeroDivisionError):
        return None
    return _finite(pairs * math.fsum(terms))


exact_llr = fastchess_llr  # the primary LLR (S06-1)


def summarize_pentanomial(counts, e0=0.0, e1=10.0, units='nelo', alpha=0.05, beta=0.05):
    """Summarize counts for paired scores [0, .25, .5, .75, 1].

    Counts are completed pairs. Population variance and the pair count define
    the standard error; individual game W/D/L is not recoverable from these
    five bins. ``units`` selects nElo or logistic Elo hypotheses explicitly.
    Empty samples, zero variance, impossible hypotheses and nonfinite derived
    quantities remain null/unknown. Intervals use a fixed 95% normal approximation;
    alpha and beta affect only the Wald diagnostic thresholds. The Wald diagnostic
    uses the exact GSPRT LLR (primary); the Gaussian LLR is a secondary cross-check.
    """
    if (not isinstance(counts, Sequence) or isinstance(counts, (str, bytes, bytearray))
            or len(counts) != 5
            or any(isinstance(c, bool) or not isinstance(c, int) or c < 0 for c in counts)):
        raise ValueError('counts must contain exactly five nonnegative integers, excluding bool')
    e0, e1 = _number(e0, 'e0'), _number(e1, 'e1')
    alpha, beta = _number(alpha, 'alpha'), _number(beta, 'beta')
    if e0 >= e1:
        raise ValueError('hypotheses require e0 < e1')
    if not 0.0 < alpha < 1.0 or not 0.0 < beta < 1.0:
        raise ValueError('alpha and beta must be strictly between zero and one')
    if not isinstance(units, str) or units not in ('nelo', 'logistic'):
        raise ValueError("units must be 'nelo' or 'logistic'")

    counts = list(counts)
    pairs = sum(counts)
    reasons = []
    result = {
        'schema': 'forge-sol-s06-statistics-v2',
        'counts': counts, 'pairs': pairs, 'games': 2 * pairs,
        'score_mean': None, 'score_variance_population': None,
        'score_standard_error': None, 'score_ci95': None,
        'logistic_elo': {'estimate': None, 'ci95_delta_halfwidth': None,
                         'ci95_delta': None, 'ci95_transformed_score': None},
        'normalized_elo': {'estimate': None},
        'fastchess_display': {'elo': None, 'elo_error95': None, 'nelo': None, 'nelo_error95': None,
                              'los_percent': None,
                              'definition': 'Elo +/- = half the Elo span of mean +/- 1.96*se (pentanomial se); '
                                            'nElo +/- = 1.96/sqrt(2*pairs)*800/ln10; LOS = Phi((mean-0.5)/se)'},
        'hypothesis': {'units': units, 'e0': e0, 'e1': e1, 'score0': None, 'score1': None},
        'llr_primary': 'exact_llr',
        'exact_llr': {'value': None, 'model': EXACT_MODEL if units == 'nelo' else LOGISTIC_MODEL,
                      'exact_fastchess': True, 'primary': True,
                      'source': 'port of fastchess v1.8.2-alpha sprt.cpp (MIT, (c) 2023 disservin)'},
        'converged_mle_llr': {'value': None, 'role': 'reference: fully converged constrained MLE '
                              '(S44 port, no zero-count regularization)'},
        'llr_difference_exact_minus_converged': None,
        'gaussian_llr': {'value': None, 'model': 'approximate Gaussian paired-score',
                         'exact_fastchess': False, 'primary': False, 'role': 'secondary cross-check'},
        'llr_difference_exact_minus_gaussian': None,
        'wald_diagnostic': {'lower': math.log(beta) - math.log1p(-alpha),
                            'upper': math.log1p(-beta) - math.log(alpha),
                            'decision': 'unknown', 'llr_used': 'exact_llr', 'diagnostic_only': True},
        'individual_wdl': None,
        'status': 'empty' if pairs == 0 else 'ok', 'null_reasons': reasons,
        'inference': {'acceptance_authorized': False,
                      'paired_counts_identify_individual_wdl': False,
                      'low_pair_count': 0 < pairs < 30,
                      'low_pair_count_threshold': 30,
                      'ci_limitations': 'Approximate fixed 95% normal/delta intervals; '
                                        'unreliable for low counts, boundaries or zero variance; '
                                        'no sequential coverage guarantee.'},
    }
    if pairs == 0:
        reasons.append('empty sample: moments, estimates, intervals and LLR unavailable')
        return result

    probabilities = [count / pairs for count in counts]
    mean = math.fsum(p * score for p, score in zip(probabilities, _PAIR_SCORES))
    variance = math.fsum(p * (score - mean) ** 2 for p, score in zip(probabilities, _PAIR_SCORES))
    result['score_mean'] = mean
    result['score_variance_population'] = variance
    elo = _logistic_elo(mean)
    result['logistic_elo']['estimate'] = elo
    result['fastchess_display']['elo'] = elo
    if elo is None:
        reasons.append('logistic Elo point estimate is infinite at a boundary and represented as null')
    if variance == 0.0:
        result['status'] = 'degenerate'
        reasons.append('zero paired-score variance: uncertainty, nElo and LLR unavailable')
        if units == 'logistic':
            result['hypothesis'].update(score0=_logistic_score(e0), score1=_logistic_score(e1))
        return result

    standard_error = math.sqrt(variance * (1 / pairs))
    result['score_standard_error'] = standard_error
    score_ci = [mean - _Z95 * standard_error, mean + _Z95 * standard_error]
    result['score_ci95'] = score_ci
    transformed = [_logistic_elo(endpoint) for endpoint in score_ci]
    result['logistic_elo']['ci95_transformed_score'] = transformed
    if any(endpoint is None for endpoint in transformed):
        reasons.append('score interval reaches a boundary: corresponding transformed Elo endpoint is null')
    else:
        result['fastchess_display']['elo_error95'] = _finite((transformed[1] - transformed[0]) / 2.0)
    result['fastchess_display']['los_percent'] = _finite(
        100.0 * 0.5 * (1.0 + math.erf((mean - 0.5) / (standard_error * math.sqrt(2.0)))))
    if elo is not None:
        try:
            halfwidth = _finite((400.0 / (_LOG10 * mean * (1.0 - mean))) * standard_error * _Z95)
        except (OverflowError, ZeroDivisionError):
            halfwidth = None
        result['logistic_elo']['ci95_delta_halfwidth'] = halfwidth
        if halfwidth is not None:
            result['logistic_elo']['ci95_delta'] = [_finite(elo - halfwidth), _finite(elo + halfwidth)]

    scale = math.sqrt(2.0 * variance)
    result['normalized_elo']['estimate'] = _finite(_C * (mean - 0.5) / scale)
    result['fastchess_display']['nelo'] = result['normalized_elo']['estimate']
    result['fastchess_display']['nelo_error95'] = _finite(_Z95 / math.sqrt(2.0 * pairs) * _C)
    if units == 'nelo':
        s0, s1 = 0.5 + (e0 / _C) * scale, 0.5 + (e1 / _C) * scale
    else:
        s0, s1 = _logistic_score(e0), _logistic_score(e1)
    result['hypothesis'].update(score0=_finite(s0), score1=_finite(s1))
    if not (math.isfinite(s0) and math.isfinite(s1) and 0.0 <= s0 < s1 <= 1.0):
        result['status'] = 'blocked'
        reasons.append('derived hypothesis scores are out of range, indistinguishable or nonfinite; LLR unavailable')
        return result
    try:
        gaussian = _finite(pairs * (s1 - s0) * (2.0 * mean - s0 - s1) / (2.0 * variance))
    except OverflowError:
        gaussian = None
    result['gaussian_llr']['value'] = gaussian
    exact = fastchess_llr(counts, e0, e1, units)
    result['exact_llr']['value'] = exact
    converged = converged_llr(counts, e0, e1, units)
    result['converged_mle_llr']['value'] = converged
    if exact is not None and converged is not None:
        result['llr_difference_exact_minus_converged'] = exact - converged
    if exact is not None and gaussian is not None:
        result['llr_difference_exact_minus_gaussian'] = exact - gaussian
    if exact is None:
        result['status'] = 'blocked'
        reasons.append('exact GSPRT LLR undefined for this profile (no interior MLE root); '
                       'the Gaussian value is secondary and does not replace it')
        return result
    wald = result['wald_diagnostic']
    if wald['lower'] >= wald['upper']:
        result['status'] = 'blocked'
        reasons.append('Wald thresholds overlap: contradictory diagnostic decision is unknown')
        return result
    wald['decision'] = ('accept_h0_diagnostic' if exact <= wald['lower'] else
                        'accept_h1_diagnostic' if exact >= wald['upper'] else 'continue')
    return result
