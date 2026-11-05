#!/usr/bin/env python3
"""llr_project.py - from the current pentanomial counts of a gate, project the games to a decision and the chance
to decide before the cap (seeded simulation of the exact fastchess GSPRT). PLANNING ONLY (queue ordering),
never a stop rule: a gate stops only by its own SPRT or its cap.

usage: python -I -B llr_project.py --ptnml "30 686 1509 744 31" [--bounds 0 10] [--alpha 0.05 --beta 0.05]
                                   [--cap-games 6000] [--paths 1000] [--seed 1] [--mode dirichlet|plugin] [--step 1] [--json OUT]
       python -I -B llr_project.py --gate GATE_DIR [same options]   (counts, bounds and cap from the folder's log block / RUN_INFO)

Model: each simulated path draws its pair-score probabilities p (5 cells) from Dirichlet(counts + 1) (the posterior
of the current counts under a flat prior; --mode plugin uses the observed frequencies with 1e-3 per empty cell
instead), then plays future pairs from p and recomputes the EXACT fastchess LLR (normalized model, reference MLE
iteration; vectorised over paths) after every --step pairs until a bound is crossed or the cap is reached.
Reported: P(H1 before cap), P(H0 before cap), P(no decision at the cap), quantiles of the additional games to a
decision, and the Brownian closed form of notes/T12/sprt_model.md as a sanity column. Numbers depend on the
current counts being representative; with few pairs they are wide.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as gl  # noqa: E402

SC = np.array(gl.SC)
NT = gl.NT


def mle_vec(phat, s):
    """Vectorised reference MLE: phat (P,5) -> pdf (P,5) under (mu-0.5)/sigma = s; 10 fixed-point steps, each a
    60-step bisection of the secular equation sum_i phat_i a_i / (1 + x a_i) = 0."""
    P = phat.shape[0]
    pdf = np.full((P, 5), 0.2)
    for _ in range(10):
        mu = pdf @ SC
        var = np.maximum(pdf @ (SC * SC) - mu * mu, 1e-300)
        sigma = np.sqrt(var)
        a = SC[None, :] - 0.5 - s * sigma[:, None] * (1.0 + ((mu[:, None] - SC[None, :]) / sigma[:, None]) ** 2) / 2.0
        amax = a.max(axis=1)
        amin = a.min(axis=1)
        lo = -1.0 / amax
        hi = -1.0 / amin
        for _ in range(60):
            x = 0.5 * (lo + hi)
            f = (phat * a / (1.0 + x[:, None] * a)).sum(axis=1)
            pos = f > 0
            lo = np.where(pos, x, lo)
            hi = np.where(pos, hi, x)
        x = 0.5 * (lo + hi)
        pdf = phat / (1.0 + x[:, None] * a)
        pdf /= pdf.sum(axis=1, keepdims=True)
    return pdf


def llr_vec(counts, e0, e1):
    reg = np.maximum(counts, 1e-3)
    n = reg.sum(axis=1)
    phat = reg / n[:, None]
    p0 = mle_vec(phat, e0 / NT * math.sqrt(2.0))
    p1 = mle_vec(phat, e1 / NT * math.sqrt(2.0))
    return n * (phat * np.log(p1 / p0)).sum(axis=1)


def brownian(pt, e0, e1, lo, hi, llr0):
    """Brownian closed forms from the current pair-score estimate: P(H1) and expected pairs to a bound."""
    st = gl.ptnml_stats(pt)
    if not st:
        return None
    k = math.sqrt(2.0) * math.log(10.0) / 800.0
    dt = (e1 - e0) * k
    th = (st['score'] - 0.5) / math.sqrt(st['var'])
    d = dt * (th - (e0 + e1) * k / 2.0)        # drift per pair
    v = dt * dt                                 # variance per pair
    if abs(d) < 1e-12:
        p1 = (llr0 - lo) / (hi - lo)
        et = ((hi - llr0) * (llr0 - lo)) / v
    else:
        g = -2.0 * d / v
        p1 = (math.exp(g * llr0) - math.exp(g * lo)) / (math.exp(g * hi) - math.exp(g * lo))
        et = (p1 * hi + (1 - p1) * lo - llr0) / d
    return {'p_h1': round(p1, 3), 'expected_more_pairs': round(et, 1), 'drift_per_pair': d}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ptnml')
    ap.add_argument('--gate')
    ap.add_argument('--bounds', nargs=2, type=float)
    ap.add_argument('--alpha', type=float, default=0.05)
    ap.add_argument('--beta', type=float, default=0.05)
    ap.add_argument('--cap-games', type=int)
    ap.add_argument('--paths', type=int, default=1000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--mode', choices=['dirichlet', 'plugin'], default='dirichlet')
    ap.add_argument('--step', type=int, default=1)
    ap.add_argument('--json')
    a = ap.parse_args()
    if a.json and os.path.exists(a.json):
        print(f'llr_project: {a.json} exists (never overwritten)', file=sys.stderr)
        return 2
    pt, e0, e1, cap, src = None, None, None, a.cap_games, 'arguments'
    if a.gate:
        pgn, log_p, ri_p, cfg_p, res_p = gl.find_gate_files(a.gate)
        info = gl.load_run_info(ri_p)
        cfg = gl.load_config(cfg_p)
        log = gl.parse_log(log_p) if log_p else None
        block = log['block'] if log else None
        if block and block.get('ptnml'):
            pt = block['ptnml']
            src = f'log block of {os.path.basename(a.gate)} ({block.get("games")} games)'
        b = gl.gate_bounds(info, cfg, block)
        if b:
            e0, e1 = b[0], b[1]
            a.alpha, a.beta = b[2], b[3]
        cap = cap or info.get('cap_games') or (2 * cfg.get('rounds') if cfg.get('rounds') else None)
    if a.ptnml:
        pt = [int(x) for x in a.ptnml.replace(',', ' ').split()]
    if a.bounds:
        e0, e1 = a.bounds
    if pt is None or len(pt) != 5 or e0 is None:
        print('llr_project: need --ptnml "a b c d e" and --bounds e0 e1 (or --gate with a log block)', file=sys.stderr)
        return 2
    if not cap:
        cap = 3000
    lo, hi = gl.sprt_bounds(a.alpha, a.beta)
    n0 = sum(pt)
    llr0 = gl.exact_llr(pt, e0, e1) if n0 else 0.0
    cap_pairs = cap // 2
    more = max(0, cap_pairs - n0)
    st = gl.ptnml_stats(pt)
    print(f'current: {n0} pairs ({2 * n0} games) Ptnml {pt}  LLR {llr0:.3f} bounds ({lo:.3f}, {hi:.3f}) [{e0:g}, {e1:g}] nElo  cap {cap} games -> {more} more pairs possible  source {src}')
    if st:
        print(f'         Elo {st["elo"]:+.2f} +/- {st["elo_err"]:.2f}  nElo {st["nelo"]:+.2f} +/- {st["nelo_err"]:.2f}')
    if llr0 >= hi or llr0 <= lo:
        print(f'already decided: LLR {llr0:.3f} is beyond a bound ({"H1" if llr0 >= hi else "H0"})')
        return 0
    bw = brownian(pt, e0, e1, lo, hi, llr0) if n0 else None
    if more == 0:
        print('at the cap: no more pairs can be played (UNPROVEN at the cap is the recorded state)')
        return 0
    rng = np.random.default_rng(a.seed)
    P = a.paths
    if a.mode == 'dirichlet':
        probs = rng.dirichlet(np.array(pt, dtype=float) + 1.0, size=P)
    else:
        reg = np.maximum(np.array(pt, dtype=float), 1e-3)
        probs = np.tile(reg / reg.sum(), (P, 1))
    counts = np.tile(np.array(pt, dtype=float), (P, 1))
    decided = np.zeros(P, dtype=np.int8)       # 0 open, 1 H1, -1 H0
    stop_at = np.full(P, -1, dtype=np.int64)   # additional pairs at the decision
    cum = probs.cumsum(axis=1)
    t0 = time.time()
    k = 0
    while k < more and (decided == 0).any():
        for _ in range(a.step):
            if k >= more:
                break
            u = rng.random(P)
            cell = (u[:, None] > cum).sum(axis=1)
            cell = np.minimum(cell, 4)
            open_ = decided == 0
            counts[open_, cell[open_]] += 1.0
            k += 1
        llr = llr_vec(counts, e0, e1)
        up = (decided == 0) & (llr >= hi)
        dn = (decided == 0) & (llr <= lo)
        decided[up] = 1
        decided[dn] = -1
        stop_at[up | dn] = k
    el = time.time() - t0
    p_h1 = float((decided == 1).mean())
    p_h0 = float((decided == -1).mean())
    p_cap = float((decided == 0).mean())
    dec = stop_at[stop_at > 0]
    q = {}
    if dec.size:
        q = {'p50': int(np.percentile(dec, 50)), 'p90': int(np.percentile(dec, 90)), 'mean': round(float(dec.mean()), 1)}
    out = {'source': src, 'ptnml': pt, 'pairs': n0, 'llr': round(llr0, 4), 'bounds_nelo': [e0, e1], 'alpha': a.alpha, 'beta': a.beta,
           'cap_games': cap, 'more_pairs_possible': more, 'paths': P, 'seed': a.seed, 'mode': a.mode, 'step': a.step,
           'p_h1_before_cap': round(p_h1, 3), 'p_h0_before_cap': round(p_h0, 3), 'p_no_decision_at_cap': round(p_cap, 3),
           'additional_pairs_to_decision_if_decided': q, 'brownian': bw, 'seconds': round(el, 1)}
    print(f'projection ({a.mode}, {P} paths, seed {a.seed}, step {a.step} pair, {el:.1f} s): P(H1 before cap) {p_h1:.3f}  P(H0 before cap) {p_h0:.3f}  '
          f'P(no decision at cap {cap}) {p_cap:.3f}')
    if q:
        print(f'additional pairs to a decision (decided paths): median {q["p50"]} (= {2 * q["p50"]} games), p90 {q["p90"]} ({2 * q["p90"]} games), mean {q["mean"]}')
    if bw:
        print(f'Brownian sanity (plug-in drift, no cap): P(H1) {bw["p_h1"]}, expected more pairs {bw["expected_more_pairs"]}')
    print('planning only: queue ordering. Never a stop rule.')
    if a.json:
        with open(a.json, 'w', newline='\n') as f:
            json.dump(out, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
