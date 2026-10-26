"""Offline paired-score diagnostics, derived directly from stated formulas.

The Gaussian LLR is approximate, not fastchess's arbitrary-profile LLR.
Wald threshold crossings are diagnostics and never authorize acceptance.
"""
from collections.abc import Sequence
import math
from numbers import Real


_LOG10 = math.log(10.0)
_C = 800.0 / _LOG10
_Z95 = 1.959963984540054
_PAIR_SCORES = (0.0, 0.25, 0.5, 0.75, 1.0)


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


def summarize_pentanomial(counts, e0=0.0, e1=10.0, units='nelo', alpha=0.05, beta=0.05):
    """Summarize counts for paired scores [0, .25, .5, .75, 1].

    Counts are completed pairs. Population variance and the pair count define
    the standard error; individual game W/D/L is not recoverable from these
    five bins. ``units`` selects nElo or logistic Elo hypotheses explicitly.
    Empty samples, zero variance, impossible hypotheses and nonfinite derived
    quantities remain null/unknown. Intervals use a fixed 95% normal/delta
    approximation; alpha and beta affect only the Wald diagnostic thresholds.
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
        'counts': counts, 'pairs': pairs, 'games': 2 * pairs,
        'score_mean': None, 'score_variance_population': None,
        'score_standard_error': None, 'score_ci95': None,
        'logistic_elo': {'estimate': None, 'ci95_delta_halfwidth': None,
                         'ci95_delta': None, 'ci95_transformed_score': None},
        'normalized_elo': {'estimate': None},
        'hypothesis': {'units': units, 'e0': e0, 'e1': e1, 'score0': None, 'score1': None},
        'gaussian_llr': {'value': None, 'model': 'approximate Gaussian paired-score',
                         'exact_fastchess': False},
        'wald_diagnostic': {'lower': math.log(beta) - math.log1p(-alpha),
                            'upper': math.log1p(-beta) - math.log(alpha),
                            'decision': 'unknown', 'diagnostic_only': True},
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
    result['logistic_elo']['ci95_transformed_score'] = [_logistic_elo(endpoint) for endpoint in score_ci]
    if any(endpoint is None for endpoint in result['logistic_elo']['ci95_transformed_score']):
        reasons.append('score interval reaches a boundary: corresponding transformed Elo endpoint is null')
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
        llr = _finite(pairs * (s1 - s0) * (2.0 * mean - s0 - s1) / (2.0 * variance))
    except OverflowError:
        llr = None
    result['gaussian_llr']['value'] = llr
    if llr is None:
        result['status'] = 'blocked'
        reasons.append('nonfinite Gaussian LLR represented as null')
        return result
    wald = result['wald_diagnostic']
    if wald['lower'] >= wald['upper']:
        result['status'] = 'blocked'
        reasons.append('Wald thresholds overlap: contradictory diagnostic decision is unknown')
        return result
    wald['decision'] = ('accept_h0_diagnostic' if llr <= wald['lower'] else
                        'accept_h1_diagnostic' if llr >= wald['upper'] else 'continue')
    return result
