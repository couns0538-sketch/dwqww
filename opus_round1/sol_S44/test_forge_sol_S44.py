#!/usr/bin/env python3
"""Tests for forge_sol_S44_elo_vs_epochs.py (run: python -I -B test_forge_sol_S44.py [GATES_DIR])."""

import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forge_sol_S44_elo_vs_epochs as m  # noqa: E402

GATES_DIR = sys.argv[1] if len(sys.argv) > 1 else r"F:\opus_scratch\sol_S44\inputs\gates"
SCL = [0.0, 0.25, 0.5, 0.75, 1.0]


# scalar reference: a line-by-line port of fishtest LLRcalc (MLE_tvalue, secular by bisection, LLR_normalized)
def _stats(p):
    mu = sum(s * q for s, q in zip(SCL, p))
    return mu, sum(q * (s - mu) ** 2 for s, q in zip(SCL, p))


def _secular(pdf):
    v = min(a for a, p in pdf if p > 0)
    w = max(a for a, p in pdf if p > 0)
    lo, hi = -1 / w, -1 / v
    f = lambda x: sum(p * a / (1 + x * a) for a, p in pdf)  # noqa: E731
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _mle(phat, s):
    pdf = [1.0 / 5] * 5
    for _ in range(200):
        prev = pdf
        mu, var = _stats(pdf)
        sg = math.sqrt(var)
        pdf1 = [(a - 0.5 - s * sg * (1 + ((mu - a) / sg) ** 2) / 2, q) for a, q in zip(SCL, phat)]
        x = _secular(pdf1)
        pdf = [phat[i] / (1 + x * pdf1[i][0]) for i in range(5)]
        if max(abs(prev[i] - pdf[i]) for i in range(5)) < 1e-14:
            break
    return pdf


def ref_llr(counts, e0, e1):
    n = sum(counts)
    phat = [c / n for c in counts]
    p0 = _mle(phat, e0 / m.NT * math.sqrt(2))
    p1 = _mle(phat, e1 / m.NT * math.sqrt(2))
    return n * sum(q * math.log(b / a) for q, a, b in zip(phat, p0, p1) if q > 0)


def test_exact_llr_equals_reference():
    rnd = random.Random(7)
    rows = [[5, 74, 252, 119, 14], [3, 47, 197, 92, 10], [9, 79, 226, 66, 1], [0, 3, 10, 6, 1], [1, 0, 4, 0, 2]]
    for _ in range(40):
        rows.append([rnd.randint(0, 20), rnd.randint(1, 150), rnd.randint(1, 450), rnd.randint(1, 160), rnd.randint(0, 20)])
    got = m.exact_llr(rows, 0.0, 10.0)
    for r, g in zip(rows, got):
        assert abs(g - ref_llr(r, 0.0, 10.0)) < 1e-9, (r, g, ref_llr(r, 0.0, 10.0))
    got = m.exact_llr(rows, -3.0, 1.0)
    for r, g in zip(rows, got):
        assert abs(g - ref_llr(r, -3.0, 1.0)) < 1e-9


def test_printed_gate_statistics_reproduced():
    if not os.path.isdir(GATES_DIR):
        print("  SKIP (no gate copies)")
        return
    for gate, folder, run, fam in m.GATES:
        g = m.parse_result(os.path.join(GATES_DIR, folder, "RESULT.md"))
        elo, err, nelo = m.ptnml_stats(g["ptnml"])
        llr = float(m.exact_llr([g["ptnml"]], g["elo0"], g["elo1"])[0])
        assert abs(elo - g["elo"]) <= 0.006 and abs(err - g["elo_err"]) <= 0.006, gate
        assert abs(nelo - g["nelo"]) <= 0.006 and abs(llr - g["llr"]) <= 0.006, (gate, llr, g["llr"])
        assert 2 * sum(g["ptnml"]) == g["games"] == g["W"] + g["D"] + g["L"], gate


def test_fast_rule_equals_brute_force():
    rng = np.random.default_rng(3)
    U = rng.random((750, 300))
    cases = [([3, 47, 197, 92, 10], th, (750, -8.0, -1.5)) for th in (0.0, 10.0, 25.0, 40.0)]
    cases += [([9, 79, 226, 66, 1], th, (750, -8.0, -1.5)) for th in (-14.0, -6.0)]
    cases += [([4, 132, 450, 152, 12], th, None) for th in (-10.0, 8.0)]
    for shape, th, early in cases:
        cats = m.pair_outcomes(shape, th, U)
        v1, s1, e1, st = m.run_rule(cats, 0.0, 10.0, early)
        v2, s2, e2, _ = m.run_rule(cats, 0.0, 10.0, early, brute=True)
        assert np.array_equal(v1, v2) and np.array_equal(s1, s2) and np.allclose(e1, e2), (shape, th)
        print("  theta %6.1f verdicts %s exact rows %d gap drift %.4f unsafe drift %.4f" % (
            th, np.bincount(v1, minlength=4).tolist(), st["exact_rows"], st["max_gap_drift"], st["max_unsafe_drift"]))
        assert st["max_unsafe_drift"] < 0.15, st


def test_tilt_hits_target_mean():
    shape = np.array([5, 74, 252, 119, 14], float) / 464
    for th in (-30.0, 0.0, 12.5, 40.0):
        p = m.tilt(shape, m.score_of_elo(th))
        assert abs(float(p @ m.SC) - m.score_of_elo(th)) < 1e-12 and abs(p.sum() - 1) < 1e-12


def test_h1_selected_mean_above_true_elo():
    sim, _ = m.simulate([5, 74, 252, 119, 14], 0.0, 10.0, 750, (750, -8.0, -1.5), [10.0], 1500, 11)
    s = sim[0]
    assert s["n_H1"] > 100 and s["mean_H1"] > 10.0, s
    assert s["mean_cap"] < 10.0, s


def test_epoch_curve_reproduces_s30():
    pts = [(16, 0.014367), (16, 0.01439), (16, 0.014389), (20, 0.014375), (20, 0.014373), (24, 0.014357), (48, 0.014341)]
    f = m.epoch_curve([{"epochs": e, "b06": b} for e, b in pts])
    assert f["alpha"] == 0.9 and abs(m.curve_at(f, 64) - 0.014334782805350669) < 1e-12, f


def test_wls_through_origin_and_intercept():
    P = [{"x": 1.0, "y": 2.0, "se": 1.0}, {"x": 2.0, "y": 4.0, "se": 1.0}, {"x": 3.0, "y": 6.0, "se": 1.0}]
    r = m.wls(P, False)
    assert abs(r["k"] - 2.0) < 1e-12 and r["inflation"] == 1.0
    P = [{"x": 0.0, "y": 1.0, "se": 1.0}, {"x": 1.0, "y": 3.0, "se": 1.0}, {"x": 2.0, "y": 5.0, "se": 1.0}]
    r = m.wls(P, True)
    assert abs(r["c"] - 1.0) < 1e-12 and abs(r["k"] - 2.0) < 1e-12


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        print(t.__name__)
        t()
    print("%d/%d PASS" % (len(tests), len(tests)))
