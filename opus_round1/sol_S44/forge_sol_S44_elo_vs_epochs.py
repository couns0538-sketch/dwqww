#!/usr/bin/env python3
"""S44 [Sol leftover]: Elo-vs-epochs fit with the new gate points. ADVICE ONLY.

Every net gate is one unpooled effect-size point (not evidence).  For each gate the tool reads the PC's own
RESULT.md / RUN_INFO.json (read-only copies), takes the opponent, concurrency and early-stop rule from RUN_INFO
(folder names are stale: most "vs_h256e12" folders from G98 on were played against AL1), and maps the candidate
to its training run in the S30 table (data size from the run's settings dump, holdout b0.6 from its final line).

Bias correction: each gate's own stopping rule is simulated (fastchess 1.8.2 SPRT, normalized model, pentanomial,
exact GSPRT LLR = the MLE under the t-value constraint, which reproduces every printed LLR; 1500-game cap; the
queue's net early stop where RUN_INFO lists it), with the gate's own pentanomial profile tilted to each true Elo.
Reported per gate:
  - adj  : Whitehead's bias-adjusted estimate, solving E_theta[Elo at stop] = observed (all outcomes); used in fits
  - cond : the verdict-conditional bias E[Elo at stop | observed verdict, theta] - theta at theta = adj
           (the winner's curse of an H1, the small negative bias of a cap)
Fits: Elo = k * dL (dL = opponent holdout b0.6 minus candidate holdout b0.6, units 1e-4), per group, never across
opponents or concurrency classes.  Projections combine k with S30's holdout curves for e64/e96 on the same data
and for more data at e48.

Usage:
  forge_sol_S44_elo_vs_epochs.py run --gates DIR --snapshot DIR --lgf FILE --s30-table CSV --s30-fit JSON --out DIR
  forge_sol_S44_elo_vs_epochs.py check --gates DIR      (formula check: printed Elo/nElo/LLR vs recomputed)
"""

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
import time

import numpy as np

NT = 800.0 / math.log(10.0)                 # nElo per t-value unit
SC = np.array([0.0, 0.25, 0.5, 0.75, 1.0])  # pair score / 2 for Ptnml(0-2) cells
BOUND = math.log(0.95 / 0.05)               # fastchess bounds for alpha = beta = 0.05: +-2.944

# gate -> (PC folder, S30 run, family).  Family "b06" = the b0.6 fb8k/v2 net family the fits use; other blends are
# listed but not fitted.  Opponent, concurrency and rules come from RUN_INFO.json, not from these folder names.
GATES = [
    ("G90", "gate90_e16m_vs_h256e12", "resid_h256_e16_m_lr7e4_b08_s10", "b08"),
    ("G95", "gate95_e12f_vs_h256e12", "resid_h256_e12_f", "b05"),
    ("G98", "gate98_e12rec_vs_h256e12", "resid_h256_e12rec_b04_s200_fb8k", "b04"),
    ("G100", "gate100_e32f003_vs_h256e12", "resid_h256_e32_f003_bs16k_lr14e4_b06_s22_fb8k", "b06"),
    ("G100r", "gate100r_e32f003_vs_h256e12", "resid_h256_e32_f003_bs16k_lr14e4_b06_s22_fb8k", "b06"),
    ("G102", "gate102_e24f005_vs_h256e12", "resid_h256_e24_f005_bs16k_lr10e4_b06_s24_fb8k", "b06"),
    ("G103", "gate103_e16f004_vs_h256e12", "resid_h256_e16_f004_bs16k_lr14e4_b06_sol_s23_fb8k", "b06"),
    ("G104", "gate104_e48f006_vs_h256e12", "resid_h256_e48_f006_bs16k_lr10e4_b06_s25_fb8k", "b06"),
    ("G104c", "gate104_e48f006_vs_h256e12_confirm", "resid_h256_e48_f006_bs16k_lr10e4_b06_s25_fb8k", "b06"),
    ("G105", "gate105_e16f007_vs_h256e12", "resid_h256_e16_f007_bs16k_lr14e4_b06_s26_fb8k", "b06"),
    ("G106", "gate106_e20f008_vs_h256e12", "resid_h256_e20_f008_bs16k_lr12e4_b06_sol_s27_fb8k", "b06"),
    ("G107", "gate107_e16f009_vs_h256e12", "resid_h256_e16_f009_bs16k_lr14e4_b06_s28_fb8k", "b06"),
    ("G109", "gate109_e16f010_vs_h256e12", "resid_h256_e16_f010_bs16k_lr12e4_b06_s29_fb8k", "b06"),
    ("G111", "gate111_e16f012_vs_h256e12", "resid_h256_e16_f012_bs16k_lr14e4_b06_sol_s31_fb8k", "b06"),
    ("G112", "gate112_e20f014_vs_h256e12", "resid_h256_e20_f014_bs16k_lr10e4_b06_s33_fb8k", "b06"),
    ("G119", "gate119_e32f003rec_s197_vs_h256e12", "resid_h256_e32_f003rec_s197_b06_fb8k", "b06"),
    ("G120", "gate120_e32f003rec_s198_vs_h256e12", "resid_h256_e32_f003rec_s198_b06_fb8k", "b06"),
    ("G120c", "gate120_e32f003rec_s198_vs_h256e12_confirm", "resid_h256_e32_f003rec_s198_b06_fb8k", "b06"),
    ("G122", "gate122_e48f030_vs_h256e12", "resid_h256_e48_f030_bs16k_lr10e4_b06_s49_fb8k", "b06"),
    ("G123", "gate123_e48f031_vs_h256e12", "resid_h256_e48_f031_bs16k_lr10e4_b06_s331_fb8k", "b06"),
    ("G124", "gate124_e48f034_vs_AL1", "resid_h256_e48_f034_bs16k_lr10e4_b06_s334_fb8k", "b06"),
    ("G124c", "gate124_e48f034_vs_AL1_confirm", "resid_h256_e48_f034_bs16k_lr10e4_b06_s334_fb8k", "b06"),
    ("G125", "gate125_e48f042_vs_AL1", "resid_h256_e48_f042_bs16k_lr10e4_b06_s342_fb8k", "b06"),
]
# opponent name (RUN_INFO base.name) -> S30 run of the opponent's net
OPPONENT_RUNS = {
    "base_h256_e12": "resid_h256_e12_e",
    "base_AUTOLOCK_1_gate120_e32f003rec_s198": "resid_h256_e32_f003rec_s198_b06_fb8k",
}
OPPONENT_SHORT = {"base_h256_e12": "h256_e12", "base_AUTOLOCK_1_gate120_e32f003rec_s198": "AL1"}


# ----------------------------------------------------------------------------------------------- statistics
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


def simulate(shape_counts, e0, e1, cap_pairs, early, thetas, reps, seed):
    """Simulate the gate's stopping rule at each true logistic Elo in thetas (common random numbers).

    early = None or (min_games, elo_max, llr_max).  Returns per-theta dicts (per-verdict counts, means, sds) and the
    exact-LLR bookkeeping stats.
    """
    rng = np.random.default_rng(seed)
    U = rng.random((cap_pairs, reps))
    out = []
    stats = {"exact_rows": 0, "max_gap_drift": 0.0, "max_unsafe_drift": 0.0, "max_exact_minus_approx": -np.inf,
             "max_approx_minus_exact": -np.inf, "degenerate_rows": 0}
    for th in thetas:
        verdict, stop_pairs, elo_stop, st = run_rule(pair_outcomes(shape_counts, th, U), e0, e1, early)
        for k in ("exact_rows", "degenerate_rows"):
            stats[k] += st[k]
        for k in ("max_gap_drift", "max_unsafe_drift", "max_exact_minus_approx", "max_approx_minus_exact"):
            stats[k] = max(stats[k], st[k])
        rec = {"theta": float(th), "reps": reps, "mean_all": float(elo_stop.mean()), "sd_all": float(elo_stop.std()),
               "mean_games": float(2 * stop_pairs.mean())}
        for code, name in ((0, "cap"), (1, "H1"), (2, "H0"), (3, "H0-early")):
            sel = verdict == code
            rec["n_" + name] = int(sel.sum())
            rec["mean_" + name] = float(elo_stop[sel].mean()) if sel.any() else None
            rec["sd_" + name] = float(elo_stop[sel].std()) if sel.sum() > 1 else None
        out.append(rec)
    return out, stats


def solve_increasing(xs, ys, target):
    """Linear interpolation of x where y(x) = target on an increasing grid; None if outside."""
    for i in range(len(xs) - 1):
        y0, y1 = ys[i], ys[i + 1]
        if y0 is None or y1 is None:
            continue
        if (y0 - target) * (y1 - target) <= 0 and y1 != y0:
            return xs[i] + (target - y0) * (xs[i + 1] - xs[i]) / (y1 - y0), i
    return None, None


def interp(xs, ys, x):
    pts = [(a, b) for a, b in zip(xs, ys) if b is not None]
    for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
        if a0 <= x <= a1:
            return b0 + (x - a0) * (b1 - b0) / (a1 - a0)
    return None


# ----------------------------------------------------------------------------------------------- parsing
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def parse_result(path):
    t = open(path, encoding="utf-8-sig").read()
    g = {}
    m = re.search(r"Settings: fastchess ([0-9.]+), ([0-9.+]+) timemargin=([0-9]+), Threads=1 Hash=16 OwnBook=false, "
                  r"(\S+) order=random start=([0-9]+), srand ([0-9]+), ([0-9]+)-game cap, concurrency ([0-9]+), "
                  r"SPRT (\w+) \[(-?[0-9.]+),(-?[0-9.]+)\]", t)
    if not m:
        raise ValueError("settings line not found: " + path)
    g.update(fastchess=m.group(1), tc=m.group(2), book=m.group(4), openings_start=int(m.group(5)),
             srand=int(m.group(6)), cap_games=int(m.group(7)), conc=int(m.group(8)), sprt_model=m.group(9),
             elo0=float(m.group(10)), elo1=float(m.group(11)))
    m = re.search(r"Games: ([0-9]+)\s+W/L/D \(candidate view\): ([0-9]+) / ([0-9]+) / ([0-9]+)", t)
    g.update(games=int(m.group(1)), W=int(m.group(2)), L=int(m.group(3)), D=int(m.group(4)))
    m = re.search(r"Ptnml\(0-2\): \[([^\]]*)\]\s+complete pairs = ([0-9]+)", t)
    g["ptnml"] = [int(x) for x in m.group(1).split(",")]
    g["pairs"] = int(m.group(2))
    m = re.search(r"Elo: (-?[0-9.]+) \+/- ([0-9.]+)\s+nElo: (-?[0-9.]+) \+/- ([0-9.]+)", t)
    g.update(elo=float(m.group(1)), elo_err=float(m.group(2)), nelo=float(m.group(3)), nelo_err=float(m.group(4)))
    m = re.search(r"LLR: (-?[0-9.]+)\s+bounds", t)
    g["llr"] = float(m.group(1))
    m = re.search(r"\*\*Verdict: ([^*]*)\*\*", t)
    v = m.group(1)
    g["verdict_text"] = v.strip()
    g["verdict"] = ("H1" if v.startswith("H1 accepted") else "H0-early" if v.startswith("H0-early")
                    else "H0" if v.startswith("H0 accepted") else "cap" if v.lower().startswith("cap") else "other")
    m = re.search(r"Time losses: ([0-9]+)\s+Crashes/disconnects/stalls/illegal: ([0-9]+)", t)
    g.update(time_losses=int(m.group(1)), crashes=int(m.group(2)))
    g["clean"] = ": CLEAN" in t
    g["result_md_sha256"] = sha256_file(path)
    return g


def parse_run_info(path):
    j = json.load(open(path, encoding="utf-8-sig"))
    c, b = j.get("candidate", {}), j.get("base", {})
    es = j.get("early_stop")
    return {"cand_name": c.get("name"), "cand_exe": os.path.basename(str(c.get("exe"))),
            "cand_sha256": str(c.get("sha256", "")).lower(), "base_name": b.get("name"),
            "base_exe": os.path.basename(str(b.get("exe"))), "base_sha256": str(b.get("sha256", "")).lower(),
            "book_sha256": str((j.get("book") or {}).get("sha256", "")).lower() if isinstance(j.get("book"), dict) else "",
            "early_stop": [es["games"], es["elo_max"], es["llr_max"]] if es else None,
            "run_info_cap": j.get("cap_games"), "run_info_conc": j.get("concurrency"),
            "run_info_sha256": sha256_file(path)}


def load_s30(path):
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["run"]] = r
    return rows


def snapshot_lines(snap_dir, gate):
    """1-based line numbers of the gate's row in the 13:35 snapshot files (None if absent)."""
    out = {}
    pats = {"GATE_RESULTS.csv": '"%s",' % gate, "GATE_RESULTS.md": "| %s |" % gate, "GATE_RESULTS.html": ">%s<" % gate}
    for name, pat in pats.items():
        line = None
        with open(os.path.join(snap_dir, name), encoding="utf-8-sig") as f:
            for i, s in enumerate(f, 1):
                if (s.startswith(pat) if name.endswith(".csv") else pat in s):
                    line = i
                    break
        out[name] = line
    return out


def lgf_line(lgf, gate):
    with open(lgf, encoding="utf-8-sig") as f:
        for i, s in enumerate(f, 1):
            if s.startswith("| %s |" % gate):
                return i
    return None


# ----------------------------------------------------------------------------------------------- fits
def wls(points, intercept):
    """Weighted least squares y = (c +) k x with weights 1/se^2; se inflated by sqrt(chi2/dof) if > 1."""
    x = np.array([p["x"] for p in points])
    y = np.array([p["y"] for p in points])
    w = 1.0 / np.array([p["se"] for p in points]) ** 2
    X = np.column_stack([np.ones_like(x), x]) if intercept else x[:, None]
    A = X.T @ (w[:, None] * X)
    beta = np.linalg.solve(A, X.T @ (w * y))
    resid = y - X @ beta
    dof = len(x) - X.shape[1]
    chi2 = float(np.sum(w * resid ** 2))
    cov = np.linalg.inv(A)
    infl = max(1.0, math.sqrt(chi2 / dof)) if dof > 0 else 1.0
    cov = cov * infl ** 2
    res = {"n": len(x), "dof": dof, "chi2": chi2, "inflation": infl}
    if intercept:
        res.update(c=float(beta[0]), c_se=float(math.sqrt(cov[0, 0])), k=float(beta[1]), k_se=float(math.sqrt(cov[1, 1])))
    else:
        res.update(c=0.0, c_se=0.0, k=float(beta[0]), k_se=float(math.sqrt(cov[0, 0])))
    return res


def epoch_curve(points, alphas=None):
    """S30's fit L(E) = Linf + A E^-alpha (alpha grid 0.1..3, least squares on Linf, A)."""
    alphas = alphas or [i / 10 for i in range(1, 31)]
    best = None
    for al in alphas:
        xs = np.array([p["epochs"] ** -al for p in points])
        ys = np.array([p["b06"] for p in points])
        X = np.column_stack([np.ones_like(xs), xs])
        beta, *_ = np.linalg.lstsq(X, ys, rcond=None)
        sse = float(np.sum((ys - X @ beta) ** 2))
        if best is None or sse < best[0]:
            best = (sse, al, float(beta[0]), float(beta[1]))
    sse, al, linf, a = best
    return {"alpha": al, "Linf": linf, "A": a, "sse": sse}


def curve_at(fit, e):
    return fit["Linf"] + fit["A"] * e ** -fit["alpha"]


# ----------------------------------------------------------------------------------------------- run
def build_points(args):
    s30 = load_s30(args.s30_table)
    pts = []
    for gate, folder, run, fam in GATES:
        d = os.path.join(args.gates, folder)
        g = {"gate": gate, "folder": folder, "run": run, "family": fam}
        g.update(parse_result(os.path.join(d, "RESULT.md")))
        g.update(parse_run_info(os.path.join(d, "RUN_INFO.json")))
        if g["run_info_conc"] is not None and int(g["run_info_conc"]) != g["conc"]:
            raise ValueError("%s: concurrency differs between RESULT.md and RUN_INFO.json" % gate)
        g["opponent"] = OPPONENT_SHORT[g["base_name"]]
        r = s30[run]
        o = s30[OPPONENT_RUNS[g["base_name"]]]
        g.update(epochs=int(r["epochs"]), train_positions=int(r["train_positions"]), settings_dump=r["train_where"],
                 holdout_b06=float(r["b06"]), holdout_where=r["where"], lr=r["lr"], blend_end=r["blend-end"],
                 seed=r["seed"], opp_run=OPPONENT_RUNS[g["base_name"]], opp_holdout_b06=float(o["b06"]),
                 opp_holdout_where=o["where"])
        g["dL_1e4"] = (g["opp_holdout_b06"] - g["holdout_b06"]) * 1e4
        g["snapshot_1335"] = snapshot_lines(args.snapshot, gate)
        g["lgf_line"] = lgf_line(args.lgf, gate)
        g["group"] = "%s conc%d" % (g["opponent"], g["conc"])
        elo, err, nelo = ptnml_stats(g["ptnml"])
        g["recomputed"] = {"elo": elo, "elo_err": err, "nelo": nelo,
                           "llr": float(exact_llr([g["ptnml"]], g["elo0"], g["elo1"])[0])}
        pts.append(g)
    return pts


def bias_for(g, reps, seed, step):
    obs = g["elo"]
    lo = math.floor((obs - 22.0) / step) * step
    hi = min(math.ceil((obs + 14.0) / step) * step, 40.0)
    thetas = sorted(set([round(lo + i * step, 6) for i in range(int(round((hi - lo) / step)) + 1)] + [10.0]))
    early = tuple(g["early_stop"]) if g["early_stop"] else None
    t0 = time.time()
    sim, stats = simulate(g["ptnml"], g["elo0"], g["elo1"], g["cap_games"] // 2, early, thetas, reps, seed)
    th = [s["theta"] for s in sim]
    m_all = [s["mean_all"] for s in sim]
    adj, i = solve_increasing(th, m_all, obs)
    res = {"thetas": th, "sim": sim, "exact_llr_stats": stats, "seconds": time.time() - t0,
           "reps": reps, "seed": seed, "early_stop_modelled": early}
    if adj is None:
        res["adj"] = None
        return res
    slope = (m_all[i + 1] - m_all[i]) / (th[i + 1] - th[i])
    sd = interp(th, [s["sd_all"] for s in sim], adj)
    res["adj"] = adj
    res["adj_se"] = sd / slope if slope > 0 else None
    res["bias_at_adj"] = obs - adj
    v = g["verdict"]
    cm = [s["mean_" + v] if s["n_" + v] >= 200 else None for s in sim]
    c_at = interp(th, cm, adj)
    res["cond_bias_at_adj"] = (c_at - adj) if c_at is not None else None
    s10 = [s for s in sim if s["theta"] == 10.0][0]
    res["cond_bias_at_true10"] = (s10["mean_" + v] - 10.0) if s10["mean_" + v] is not None and s10["n_" + v] >= 200 else None
    res["p_verdict_at_adj"] = interp(th, [s["n_" + v] / s["reps"] for s in sim], adj)
    cond_solve, _ = solve_increasing(th, cm, obs)
    res["cond_matching_estimate"] = cond_solve
    return res


def project(fit, s30fit, epoch_pts, draws, seed):
    """Elo gain ranges for the next-run options, Monte Carlo over k and the S30 holdout-curve uncertainty."""
    rng = np.random.default_rng(seed)
    full = epoch_curve(epoch_pts)
    loo = [epoch_curve([p for j, p in enumerate(epoch_pts) if j != i]) for i in range(len(epoch_pts))]
    l48 = [curve_at(f, 48) for f in [full] + loo]
    opts = {}
    for e in (64, 96):
        gains = [curve_at(f, 48) - curve_at(f, e) for f in [full] + loo]
        opts["e%d same data" % e] = {"dL_1e4_central": (curve_at(full, 48) - curve_at(full, e)) * 1e4,
                                     "dL_1e4_range": [min(gains) * 1e4, max(gains) * 1e4], "compute_vs_e48": e / 48.0}
    dc = s30fit["data_curve_e48"]["fit"]["b06 = c + s*ln(positions)"]
    s_mu = -dc["s"]
    s_se = (dc["s_ci95"][1] - dc["s_ci95"][0]) / (2 * 1.959963984540054)
    for f in (1.10, 1.25, 1.50, 2.00):
        opts["e48 data x%.2f" % f] = {"dL_1e4_central": s_mu * math.log(f) * 1e4,
                                       "dL_1e4_ci95": [(s_mu - 1.96 * s_se) * math.log(f) * 1e4,
                                                       (s_mu + 1.96 * s_se) * math.log(f) * 1e4],
                                       "compute_vs_e48": f}
    ks = rng.normal(fit["k"], fit["k_se"], draws)
    for name, o in opts.items():
        if "dL_1e4_range" in o:
            dl = rng.uniform(o["dL_1e4_range"][0], o["dL_1e4_range"][1], draws)
        else:
            dl = rng.normal(o["dL_1e4_central"], (o["dL_1e4_ci95"][1] - o["dL_1e4_ci95"][0]) / 3.92, draws)
        g = ks * dl
        o["elo_central"] = fit["k"] * o["dL_1e4_central"]
        o["elo_p10_p50_p90"] = [float(np.percentile(g, q)) for q in (10, 50, 90)]
        o["elo_p2.5_p97.5"] = [float(np.percentile(g, q)) for q in (2.5, 97.5)]
    return {"epoch_fit_full": full, "epoch_fit_loo": loo, "L48_fits": l48, "options": opts}


def cmd_check(args):
    worst = {"elo": 0.0, "err": 0.0, "nelo": 0.0, "llr": 0.0}
    for gate, folder, run, fam in GATES:
        g = parse_result(os.path.join(args.gates, folder, "RESULT.md"))
        elo, err, nelo = ptnml_stats(g["ptnml"])
        llr = float(exact_llr([g["ptnml"]], g["elo0"], g["elo1"])[0])
        d = {"elo": abs(elo - g["elo"]), "err": abs(err - g["elo_err"]), "nelo": abs(nelo - g["nelo"]), "llr": abs(llr - g["llr"])}
        for k in worst:
            worst[k] = max(worst[k], d[k])
        print("%-6s Elo %7.2f/%7.2f err %5.2f/%5.2f nElo %7.2f/%7.2f LLR %6.2f/%7.3f" % (
            gate, g["elo"], elo, g["elo_err"], err, g["nelo"], nelo, g["llr"], llr))
    print("max |printed - recomputed|:", json.dumps({k: round(v, 4) for k, v in worst.items()}))
    ok = worst["elo"] <= 0.006 and worst["err"] <= 0.006 and worst["nelo"] <= 0.006 and worst["llr"] <= 0.006
    print("CHECK", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def cmd_run(args):
    os.makedirs(args.out, exist_ok=True)
    pts = build_points(args)
    bias = {}
    for g in pts:
        seed = args.seed + int(re.sub(r"\D", "", g["gate"])) * 10 + (1 if g["gate"].endswith(("c", "r")) else 0)
        b = bias_for(g, args.reps, seed, args.step)
        bias[g["gate"]] = b
        st = b["exact_llr_stats"]
        print("%-6s %-14s %-8s obs %7.2f adj %s cond-bias@adj %s (%.0fs, exact rows %d, unsafe drift %.4f, "
              "degenerate %d)" % (
                  g["gate"], g["group"], g["verdict"], g["elo"],
                  "%.2f +- %.2f" % (b["adj"], b["adj_se"]) if b.get("adj") is not None else "n/a",
                  "%.2f" % b["cond_bias_at_adj"] if b.get("cond_bias_at_adj") is not None else "n/a",
                  b["seconds"], st["exact_rows"], st["max_unsafe_drift"], st["degenerate_rows"]), flush=True)
        if st["max_unsafe_drift"] > 0.5 * 0.3:
            print("WARNING: gap drift between exact evaluations is above half the band; lower refresh", flush=True)
    for g in pts:
        b = bias[g["gate"]]
        g["adj"] = b.get("adj")
        g["adj_se"] = b.get("adj_se")
    groups = {}
    for g in pts:
        if g["family"] == "b06":
            groups.setdefault(g["group"], []).append(g)
    fits = {}
    for name, gs in sorted(groups.items()):
        for label, key, sekey in (("adjusted", "adj", "adj_se"), ("raw", "elo", None)):
            P = [{"x": g["dL_1e4"], "y": g[key], "se": (g[sekey] if sekey else g["elo_err"] / 1.959963984540054)}
                 for g in gs if g[key] is not None]
            for icpt in (False, True):
                if icpt and len(set(round(p["x"], 6) for p in P)) < 3:
                    continue
                fits["%s | %s | %s" % (name, label, "c + k dL" if icpt else "k dL")] = wls(P, icpt)
    s30fit = json.load(open(args.s30_fit, encoding="utf-8"))
    epts = s30fit["epoch_curve_fixed_data"]["points"]
    full = epoch_curve(epts)
    ref = s30fit["epoch_curve_fixed_data"]["fit_L(E)=Linf+A*E^-alpha"]
    if abs(curve_at(full, 64) - ref["L64"]) > 1e-12:
        raise ValueError("epoch-curve refit does not reproduce S30's L64")
    proj = {}
    for name in sorted(fits):
        if "| adjusted |" in name:
            proj[name] = project(fits[name], s30fit, epts, args.draws, args.seed)
    out = {"tool": "forge_sol_S44_elo_vs_epochs", "advice_only": True, "points": pts, "bias": bias, "fits": fits,
           "projections": proj, "args": {k: v for k, v in vars(args).items() if k != "func"},
           "s30_epoch_fit_check": {"L64_refit": curve_at(full, 64), "L64_s30": ref["L64"]}}
    with open(os.path.join(args.out, "s44_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    with open(os.path.join(args.out, "s44_points.csv"), "w", newline="", encoding="utf-8") as f:
        cols = ["gate", "group", "opponent", "conc", "family", "run", "epochs", "train_positions", "settings_dump",
                "holdout_b06", "holdout_where", "opp_holdout_b06", "dL_1e4", "games", "W", "D", "L", "ptnml", "elo",
                "elo_err", "nelo", "llr", "verdict", "adj", "adj_se", "cand_exe", "cand_sha256", "base_exe",
                "base_sha256", "book_sha256", "early_stop", "snapshot_1335", "lgf_line", "result_md_sha256"]
        w = csv.writer(f)
        w.writerow(cols)
        for g in pts:
            w.writerow([json.dumps(g[c]) if isinstance(g[c], (list, dict)) else g[c] for c in cols])
    print("wrote", os.path.join(args.out, "s44_results.json"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--gates", required=True)
    c.set_defaults(func=cmd_check)
    r = sub.add_parser("run")
    r.add_argument("--gates", required=True)
    r.add_argument("--snapshot", required=True)
    r.add_argument("--lgf", required=True)
    r.add_argument("--s30-table", required=True)
    r.add_argument("--s30-fit", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--reps", type=int, default=6000)
    r.add_argument("--step", type=float, default=2.0)
    r.add_argument("--draws", type=int, default=200000)
    r.add_argument("--seed", type=int, default=20261027)
    r.set_defaults(func=cmd_run)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
