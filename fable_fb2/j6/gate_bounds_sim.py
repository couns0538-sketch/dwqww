#!/usr/bin/env python3
"""FB2-J6: SPRT design numbers for the Forge PC gate (fastchess 1.8.2, normalized model, pentanomial).

Simulates truncated SPRTs (bounds in nElo, a = b = 0.05 -> +-ln 19) with the normal-approximation GSPRT
LLR per pair (the exact GSPRT differs by <= 0.1 at the stops, see forge-gate-stats), using the pentanomial profile
of a typical AL1-era gate tilted to a true pair-score mean, for several designs and true Elo values.
Outputs: P(H1), P(H0), P(cap), expected games, expected gate hours at the measured throughput, and a candidate
ranking by expected Elo per gate hour under stated priors. Writes JSON + a Markdown table.
"""
import json
import math
import sys

import numpy as np

rng = np.random.default_rng(20261028)
CELLS = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
BASE_PTNML = np.array([8, 113, 483, 135, 11], float)          # gate38 (AL1 era, 10+0.1, conc 8, 77% draws)
BASE_P = BASE_PTNML / BASE_PTNML.sum()
GAMES_PER_HOUR = 1500.0 / (92.5 / 60.0)                         # gates 36 -> 37 -> 38: 92-93 min per 1500 games
C = math.log(10) / 800.0


def tilt(p, target_mean):
    """Exponential tilting of the pentanomial cell probabilities to a given pair-score mean."""
    lo, hi = -40.0, 40.0
    for _ in range(100):
        t = (lo + hi) / 2
        q = p * np.exp(t * CELLS)
        q /= q.sum()
        if (q * CELLS).sum() < target_mean:
            lo = t
        else:
            hi = t
    q = p * np.exp(((lo + hi) / 2) * CELLS)
    return q / q.sum()


def mean_of_elo(elo):
    return 1.0 / (1.0 + 10 ** (-elo / 400.0))


def nelo_bounds_to_means(nelo0, nelo1, var):
    s = math.sqrt(2.0 * var)
    return 0.5 + nelo0 * C * s, 0.5 + nelo1 * C * s


def simulate(design, true_elo, runs=4000):
    elo0, elo1, cap = design["elo0"], design["elo1"], design["cap"]
    pairs_cap = cap // 2
    q = tilt(BASE_P, mean_of_elo(true_elo))
    var = float((q * CELLS ** 2).sum() - (q * CELLS).sum() ** 2)
    # fastchess normalized: elo0/elo1 are nElo; the pair-score means they correspond to depend on the variance
    mu0, mu1 = nelo_bounds_to_means(elo0, elo1, var)
    draws = rng.choice(5, size=(runs, pairs_cap), p=q)
    scores = CELLS[draws]
    csum = np.cumsum(scores, axis=1)
    n = np.arange(1, pairs_cap + 1)
    xbar = csum / n
    llr = n * (mu1 - mu0) * (xbar - (mu0 + mu1) / 2.0) / var
    b = math.log(19.0)
    hit_h1 = llr >= b
    hit_h0 = llr <= -b
    first_h1 = np.where(hit_h1.any(axis=1), hit_h1.argmax(axis=1), pairs_cap)
    first_h0 = np.where(hit_h0.any(axis=1), hit_h0.argmax(axis=1), pairs_cap)
    stop = np.minimum(first_h1, first_h0)
    outcome = np.where(stop >= pairs_cap, 2, np.where(first_h1 < first_h0, 1, 0))   # 1 = H1, 0 = H0, 2 = cap
    games = 2 * np.minimum(stop + 1, pairs_cap)
    return {"p_h1": float((outcome == 1).mean()), "p_h0": float((outcome == 0).mean()), "p_cap": float((outcome == 2).mean()),
            "mean_games": float(games.mean()), "hours": float(games.mean() / GAMES_PER_HOUR), "var": var,
            "mu0": mu0, "mu1": mu1, "elo_of_mu1": -400 * math.log10(1 / mu1 - 1), "elo_of_mu0": -400 * math.log10(1 / mu0 - 1)}


DESIGNS = [
    {"name": "[0,10] cap 1500 (current queue)", "elo0": 0, "elo1": 10, "cap": 1500},
    {"name": "[0,5] cap 1500 (R3-3 proposal)", "elo0": 0, "elo1": 5, "cap": 1500},
    {"name": "[0,5] cap 4000", "elo0": 0, "elo1": 5, "cap": 4000},
    {"name": "[0,10] cap 3000", "elo0": 0, "elo1": 10, "cap": 3000},
    {"name": "[-3,1] non-regression cap 3000", "elo0": -3, "elo1": 1, "cap": 3000},
    {"name": "[-5,5] cap 2000", "elo0": -5, "elo1": 5, "cap": 2000},
    {"name": "[2,12] cap 1500", "elo0": 2, "elo1": 12, "cap": 1500},
    {"name": "[0,15] cap 1000", "elo0": 0, "elo1": 15, "cap": 1000},
    {"name": "[0,10] cap 6000", "elo0": 0, "elo1": 10, "cap": 6000},
    {"name": "[0,10] cap 8000", "elo0": 0, "elo1": 10, "cap": 8000},
    {"name": "[0,20] cap 1500 (large effects, nets)", "elo0": 0, "elo1": 20, "cap": 1500},
    {"name": "[-10,0] non-regression cap 3000", "elo0": -10, "elo1": 0, "cap": 3000},
]
TRUE_ELOS = [-10, -5, 0, 3, 5, 8, 10, 15]


def main():
    out = {"games_per_hour": GAMES_PER_HOUR, "base_ptnml": BASE_PTNML.tolist(), "designs": []}
    lines = ["| design | true Elo | P(H1) | P(H0) | P(cap) | E[games] | E[hours] |", "|---|---|---|---|---|---|---|"]
    for d in DESIGNS:
        row = {"name": d["name"], "elo0": d["elo0"], "elo1": d["elo1"], "cap": d["cap"], "cells": {}}
        for e in TRUE_ELOS:
            r = simulate(d, e)
            row["cells"][str(e)] = r
            lines.append(f"| {d['name']} | {e:+d} | {r['p_h1']:.2f} | {r['p_h0']:.2f} | {r['p_cap']:.2f} | {r['mean_games']:.0f} | {r['hours']:.1f} |")
        out["designs"].append(row)
        print(d["name"], " ".join(f"e{e:+d}:H1 {row['cells'][str(e)]['p_h1']:.2f}/H0 {row['cells'][str(e)]['p_h0']:.2f}/cap {row['cells'][str(e)]['p_cap']:.2f}/{row['cells'][str(e)]['mean_games']:.0f}g" for e in TRUE_ELOS))
    # candidate ranking: prior on the true Elo (mean, sd), expected accepted Elo per expected gate hour under a design
    candidates = [
        ("J1 v3 net (standalone H512, current best ckpt)", -15.0, 25.0, "holdout b0.6 0.0161 vs AL1 0.0144 at ckpt 1; S44: ~5 Elo per 1e-4 -> about -80 now; 1.17x NPS adds ~ +25; prior widens as training continues"),
        ("J3 CorrHistV2", 3.0, 5.0, "continuation correction history on top of pawn/material (typical +2..+6 in other engines)"),
        ("J3 SingularV2", 2.0, 5.0, "triple/PV-double extensions and multicut"),
        ("J3 LmrTableV2", 1.0, 6.0, "fitted LMR redistribution (observational fit, could go either way)"),
        ("J3 TtPruneV2", 2.0, 5.0, "pruning guards, cut-node IIR, opponent-worsening RFP, improving margins"),
        ("J4 TimeManV2", 2.0, 4.0, "time usage closer to the plan at fast TC; small"),
        ("R3 O2 AVX2 kernels (quiet runner +3% NPS)", 1.5, 1.0, "node-exact speed, +3% NPS ~ +1.5 Elo"),
        ("R3 NOZERO (+1.6% NPS)", 0.8, 0.8, "node-exact speed"),
        ("R3 CorrMargins / CorrExt / CuckooRep / HistRework (search changes)", 2.0, 5.0, "R3-3 class B entries"),
        ("R3 MaterialKeyTable / SPEEDSTACK / LazyAcc (<= +0.5% NPS)", 0.2, 0.3, "node-exact speed, tiny"),
    ]
    out["ranking"] = []
    rank_lines = ["| candidate | prior Elo (mean +- sd) | P(H1) under [0,10] cap 6000 | E[Elo accepted] | E[hours] | Elo per gate hour |", "|---|---|---|---|---|---|"]
    design = next(d for d in DESIGNS if d["name"] == "[0,10] cap 6000")
    for name, mean, sd, note in candidates:
        # integrate over the prior with 9 quantile points
        qs = np.array([0.05, 0.15, 0.3, 0.4, 0.5, 0.6, 0.7, 0.85, 0.95])
        from statistics import NormalDist
        elos = [mean + sd * NormalDist().inv_cdf(q) for q in qs]
        w = np.array([0.1, 0.1, 0.1, 0.1, 0.2, 0.1, 0.1, 0.1, 0.1])
        p_h1 = 0.0
        gain = 0.0
        hours = 0.0
        for e, wi in zip(elos, w):
            r = simulate(design, e, runs=1500)
            p_h1 += wi * r["p_h1"]
            gain += wi * r["p_h1"] * max(e, 0.0)
            hours += wi * r["hours"]
        per_hour = gain / max(hours, 1e-9)
        out["ranking"].append({"candidate": name, "prior_mean": mean, "prior_sd": sd, "p_h1": p_h1, "expected_accepted_elo": gain, "expected_hours": hours, "elo_per_hour": per_hour, "note": note})
        rank_lines.append(f"| {name} | {mean:+.1f} +- {sd:.1f} | {p_h1:.2f} | {gain:.2f} | {hours:.1f} | {per_hour:.3f} |")
    out["ranking"].sort(key=lambda r: -r["elo_per_hour"])
    json.dump(out, open(sys.argv[1], "w", newline="\n"), indent=1, sort_keys=True)
    with open(sys.argv[2], "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n\n" + "\n".join(rank_lines) + "\n")
    print("\n".join(rank_lines))


if __name__ == "__main__":
    main()
