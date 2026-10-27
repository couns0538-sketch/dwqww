"""fastchess 1.8.2 exact GSPRT (normalized pentanomial) for the S33 v2 cross-check of advice cells. ADVICE ONLY.

The functions between the COPY markers are copied VERBATIM from the Opus S44 tool
(forge_sol_S44_elo_vs_epochs.py, working-tree snapshot SHA256 306f435c7ab3c40537a64d55a160f2fed203bfb8293a9a0606414b069eeb3b81),
which reproduces the printed LLR of 23 real Forge gates. oc_cell() is new: it samples pairs from the gate profile
tilted exactly as Sol's S33 planner does (shape ratios kept, no +0.5 smoothing) and applies the exact-LLR stopping
rule, so the only difference to Sol's approx model is the LLR itself. numpy only.
"""
import math

import numpy as np

NT = 800.0 / math.log(10.0)                 # nElo per t-value unit
SC = np.array([0.0, 0.25, 0.5, 0.75, 1.0])  # pair score / 2 for Ptnml(0-2) cells
BOUND = math.log(0.95 / 0.05)               # fastchess bounds for alpha = beta = 0.05: +-2.944
MODEL_LABEL = 'exact fastchess 1.8.2 GSPRT (normalized pentanomial), S44 implementation'

# ---- COPY BEGIN (verbatim from S44 306f435c) ----
def elo_of_score(s):
    s = min(max(s, 1e-12), 1 - 1e-12)
    return -400.0 * math.log10(1.0 / s - 1.0)


def score_of_elo(e):
    return 1.0 / (1.0 + 10.0 ** (-e / 400.0))


def ptnml_stats(pt):
    """fastchess-style Elo, Elo 95% error, nElo from Ptnml(0-2) [LL, LD, WL+DD, WD, WW]."""
    n = float(sum(pt))
    p = np.asarray(pt, float) / n
    a = float(p @ SC)
    var = float(p @ SC ** 2 - a * a)
    se = math.sqrt(var / n)
    elo = elo_of_score(a)
    err = (elo_of_score(a + 1.959963984540054 * se) - elo_of_score(a - 1.959963984540054 * se)) / 2.0
    nelo = (a - 0.5) / math.sqrt(2.0 * var) * NT
    return elo, err, nelo


def _secular(phat, a, x0=None):
    """Vectorised root x of sum_i phat_i a_i / (1 + x a_i) = 0 (fishtest LLRcalc.secular), Newton in a bisection
    bracket.  The bracket uses the occupied cells only (an empty cell has MLE probability 0 for any x); rows with no
    sign change in a get NaN."""
    pos = phat > 0
    amax = np.where(pos, a, -np.inf).max(axis=1)
    amin = np.where(pos, a, np.inf).min(axis=1)
    ok = (amax > 0) & (amin < 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        lo = np.where(ok, -1.0 / amax, -1.0)
        hi = np.where(ok, -1.0 / amin, 1.0)
    x = np.zeros(a.shape[0]) if x0 is None else np.where(np.isfinite(x0) & (x0 > lo) & (x0 < hi), x0, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        for _ in range(80):
            d = 1.0 + x[:, None] * a
            q = np.where(pos, phat / d, 0.0)
            f = (q * a).sum(axis=1)
            fp = -(q * a * a / d).sum(axis=1)
            lo = np.where(f > 0, x, lo)
            hi = np.where(f > 0, hi, x)
            xn = x - f / fp
            bad = ~np.isfinite(xn) | (xn <= lo) | (xn >= hi)
            xn = np.where(bad, 0.5 * (lo + hi), xn)
            done = np.abs(xn - x) <= 1e-15 * (1.0 + np.abs(x))
            x = xn
            if done[ok].all():
                break
    x[~ok] = np.nan
    return x


def _mle_tvalue(phat, s, iters=60):
    """MLE of the cell probabilities under (mu - 0.5) / sigma = s (fishtest LLRcalc.MLE_tvalue), vectorised.
    s = 0 needs a single secular solve (a does not depend on the pdf); otherwise the fixed-point loop is
    warm-started from phat."""
    pos = phat > 0
    if s == 0.0:
        a = np.broadcast_to(SC[None, :] - 0.5, phat.shape)
        x = _secular(phat, a)
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(pos, phat / (1.0 + x[:, None] * a), 0.0)
    pdf = phat.copy()
    x = None
    with np.errstate(divide="ignore", invalid="ignore"):
        for _ in range(iters):
            mu = pdf @ SC
            sigma = np.sqrt(np.maximum(pdf @ SC ** 2 - mu * mu, 1e-300))
            a = SC[None, :] - 0.5 - s * sigma[:, None] * (1.0 + ((mu[:, None] - SC[None, :]) / sigma[:, None]) ** 2) / 2.0
            x = _secular(phat, a, x)
            new = np.where(pos, phat / (1.0 + x[:, None] * a), 0.0)
            conv = np.nanmax(np.abs(new - pdf)) < 1e-14 if np.isfinite(new).any() else True
            pdf = new
            if conv:
                break
    return pdf


def exact_llr(counts, e0, e1):
    """fastchess 1.8.2 normalized-model pentanomial LLR (exact GSPRT), counts shape (m, 5); NaN if degenerate."""
    counts = np.atleast_2d(np.asarray(counts, float))
    n = counts.sum(axis=1)
    phat = counts / n[:, None]
    t0 = e0 / NT * math.sqrt(2.0)
    t1 = e1 / NT * math.sqrt(2.0)
    p0 = _mle_tvalue(phat, t0)
    p1 = _mle_tvalue(phat, t1)
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = np.where(phat > 0, phat * np.log(p1 / p0), 0.0)
    return n * terms.sum(axis=1)


def approx_llr(counts, e0, e1):
    """Normal approximation of the same LLR (used only to find the rows that need the exact value)."""
    n = counts.sum(axis=1)
    phat = counts / n[:, None]
    a = phat @ SC
    var = np.maximum(phat @ SC ** 2 - a * a, 1e-12)
    s0 = 0.5 + e0 * np.sqrt(2 * var) / NT
    s1 = 0.5 + e1 * np.sqrt(2 * var) / NT
    return (s1 - s0) * (2 * a - s0 - s1) / (var / n) / 2.0


def elo_rows(counts):
    n = counts.sum(axis=1)
    a = np.clip((counts @ SC) / n, 1e-12, 1 - 1e-12)
    return -400.0 * np.log10(1.0 / a - 1.0)


def tilt(shape, target):
    """Exponential tilt p_i ~ shape_i * exp(lam * s_i) with mean pair score = target."""
    lo, hi = -80.0, 80.0
    for _ in range(200):
        lam = (lo + hi) / 2.0
        w = shape * np.exp(lam * SC)
        m = float((w / w.sum()) @ SC)
        if m < target:
            lo = lam
        else:
            hi = lam
    w = shape * np.exp(lam * SC)
    return w / w.sum()


def run_rule(cats, e0, e1, early, brute=False, band=0.3, window=1.0, refresh=3, warmup=150):
    """Apply the gate's stopping rule to pair outcomes cats (cap_pairs, reps) -> verdict, stop pairs, Elo, stats.

    Exact LLR decides every stop.  To save time it is evaluated (a) every pair for rows whose estimated exact LLR
    (approx + that row's last measured exact-minus-approx gap) is within `band` of a threshold, and (b) at least
    every `refresh` pairs (every pair before `warmup` pairs, where one pair moves the state a lot) for rows whose
    approx LLR is within `window` of a threshold.  `brute=True` evaluates the exact LLR for every row at every pair
    (reference for the test).  stats["max_gap_drift"] is the largest change of a row's gap between evaluations at
    most `refresh` pairs apart after `warmup`; stats["max_unsafe_drift"] is the largest such change in the direction
    that could hide a crossing (exact rising against the estimate for LLR > 0, falling for LLR < 0).  It must stay
    well below `band`.
    """
    cap_pairs, reps = cats.shape
    counts = np.zeros((reps, 5))
    active = np.arange(reps)
    verdict = np.zeros(reps, np.int8)            # 0 cap, 1 H1, 2 H0, 3 H0-early
    stop_pairs = np.full(reps, cap_pairs)
    elo_stop = np.zeros(reps)
    gap = np.zeros(reps)
    last = np.full(reps, -10 ** 9)
    st = {"exact_rows": 0, "max_gap_drift": 0.0, "max_unsafe_drift": 0.0, "max_exact_minus_approx": -np.inf,
          "max_approx_minus_exact": -np.inf, "degenerate_rows": 0}
    for n in range(1, cap_pairs + 1):
        if active.size == 0:
            break
        counts[active, cats[n - 1, active]] += 1.0
        if n < 8:
            continue
        c = counts[active]
        la = approx_llr(c, e0, e1)
        el = elo_rows(c)
        ezone = (el < early[1]) if (early is not None and 2 * n >= early[0]) else np.zeros(active.size, bool)
        if brute:
            need = np.ones(active.size, bool)
        else:
            est = la + gap[active]
            need = (est > BOUND - band) | (est < -BOUND + band) | (ezone & (est < early[2] + band) if early else False)
            wide = (la > BOUND - window) | (la < -BOUND + window) | (ezone & (la < early[2] + window) if early else False)
            need |= wide & (n - last[active] >= (refresh if n >= warmup else 1))
        if not need.any():
            continue
        idx = np.nonzero(need)[0]
        lx = exact_llr(c[idx], e0, e1)
        bad = ~np.isfinite(lx)
        if bad.any():
            st["degenerate_rows"] += int(bad.sum())
            lx = np.where(bad, la[idx], lx)
        rows = active[idx]
        g = lx - la[idx]
        recent = ((n - last[rows]) <= refresh) & (n > warmup)
        if recent.any():
            dg = g[recent] - gap[rows][recent]
            st["max_gap_drift"] = max(st["max_gap_drift"], float(np.max(np.abs(dg))))
            st["max_unsafe_drift"] = max(st["max_unsafe_drift"], float(np.max(np.where(la[idx][recent] > 0, dg, -dg))))
        st["max_exact_minus_approx"] = max(st["max_exact_minus_approx"], float(np.max(g)))
        st["max_approx_minus_exact"] = max(st["max_approx_minus_exact"], float(np.max(-g)))
        st["exact_rows"] += int(idx.size)
        gap[rows] = g
        last[rows] = n
        h1 = lx >= BOUND
        h0 = lx <= -BOUND
        eh0 = ~h1 & ~h0 & ezone[idx] & (lx < early[2]) if early is not None else np.zeros(idx.size, bool)
        stop = h1 | h0 | eh0
        if stop.any():
            sr = rows[stop]
            verdict[sr] = np.where(h1[stop], 1, np.where(h0[stop], 2, 3))
            stop_pairs[sr] = n
            elo_stop[sr] = el[idx[stop]]
            keep = np.ones(active.size, bool)
            keep[idx[stop]] = False
            active = active[keep]
    if active.size:
        elo_stop[active] = elo_rows(counts[active])
    return verdict, stop_pairs, elo_stop, st


def pair_outcomes(shape_counts, theta, U):
    """Pair results (indices into SC) for true logistic Elo theta from uniforms U, by tilting the gate's profile
    (observed Ptnml + 0.5 per cell) to the matching mean pair score."""
    shape = np.asarray(shape_counts, float) + 0.5
    shape /= shape.sum()
    p = tilt(shape, score_of_elo(theta))
    cdf = np.cumsum(p)
    cdf[-1] = 1.0 + 1e-12
    return np.searchsorted(cdf, U, side="right").astype(np.int8)

# ---- COPY END ----


def oc_cell(counts, true_elo, e0, e1, cap_games, runs, seed):
    """Operating characteristics of one SPRT design under the exact GSPRT stopping rule (no early stop)."""
    shape = np.asarray(counts, float)
    shape = shape / shape.sum()
    p = tilt(shape, score_of_elo(true_elo))
    cdf = np.cumsum(p)
    cdf[-1] = 1.0 + 1e-12
    rng = np.random.default_rng(seed)
    cats = np.searchsorted(cdf, rng.random((cap_games // 2, runs)), side='right').astype(np.int8)
    verdict, stop_pairs, elo_stop, stats = run_rule(cats, e0, e1, None)
    games = 2 * stop_pairs
    out = {'model': MODEL_LABEL, 'true_elo': true_elo, 'e0': e0, 'e1': e1, 'cap_games': cap_games, 'runs': runs,
           'seed': seed, 'P_H1': float(np.mean(verdict == 1)), 'P_H0': float(np.mean(verdict == 2)),
           'P_cap': float(np.mean(verdict == 0)), 'mean_games': float(games.mean()),
           'median_games': float(np.median(games)), 'exact_llr_stats': {k: float(v) for k, v in stats.items()}}
    return out
