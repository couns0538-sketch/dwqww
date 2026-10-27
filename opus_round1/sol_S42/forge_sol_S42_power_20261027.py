#!/usr/bin/env python3
"""S42 power estimate (MODEL, ADVICE ONLY; Opus 5.5, 2026-10-27).

1. Fit a per-game outcome model on a real gate's games, with each opening scored by OUR engine (from
   `forge_sol_S42_book_v2_20261027.py gate`). The candidate's game result follows an ordered-logistic (BayesElo-style)
   model with draw width d:
       x = Delta + s*(c*e + w)   (s = +1 if the candidate has White, -1 if Black; e = White-POV exit eval in cp)
       P(win) = F(x - d), P(loss) = F(-x - d), P(draw) = 1 - P(win) - P(loss),  F(t) = 1/(1 + 10^(-t/400)).
   Maximum likelihood (numpy Nelder-Mead), standard errors from the numerical Hessian, and a likelihood-ratio test
   against the same model without the opening term (c = 0).
2. Pair (two games, colours reversed, same opening) = independent games given the opening; the book's pentanomial is
   the average over its openings. Checked against the gate's observed pentanomial (chi-square, 4 df).
3. For each book (the gate's own openings, a seeded current-book sample, the candidate v2 book) and a strength
   difference Delta, the predicted profile goes to Sol's S33 planner UNCHANGED (sol_S33/, sha-pinned) with the
   numpy-only SciPy shim (scipy_shim/, validated by check_scipy_shim_s42.py). The planner's true Elo is set to the
   profile's own logistic Elo, so its exponential tilt is the identity and the profile is used as predicted.
   Comparing books at the same Delta is the point: the same engine pair scores differently on different books.
usage: python -I -B forge_sol_S42_power_20261027.py --gate-games CSV --current-sample CSV --new-book-meta CSV --out NEW_DIR
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scipy_shim"))
import numpy as np  # noqa: E402

DATE = "20261027"
SCORES = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
C_NELO = 800.0 / math.log(10.0)
PLANNER = HERE / "sol_S33" / "forge_sol_S33_sprt_planner_20261026.py"
PLANNER_SHA = "008819d5387cdd5ac5d512bb2ebafd09f141aafc9b6904cba2f73a8373634d03"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def F(t):
    return 1.0 / (1.0 + np.power(10.0, -t / 400.0))


def game_probs(x, d):
    pw = F(x - d); pl = F(-x - d)
    return pl, 1.0 - pw - pl, pw


def nll(theta, e, s, pts, use_eval=True):
    delta, c, w, ld = theta
    d = math.exp(ld)
    x = delta + s * ((c * e if use_eval else 0.0) + w)
    pl, pd, pw = game_probs(x, d)
    p = np.where(pts == 1.0, pw, np.where(pts == 0.0, pl, pd))
    if np.any(p <= 0):
        return 1e18
    return float(-np.sum(np.log(p)))


def nelder_mead(f, x0, step, tol=1e-12, maxiter=20000):
    n = len(x0); pts = [np.array(x0, float)]
    for i in range(n):
        x = np.array(x0, float); x[i] += step[i]; pts.append(x)
    vals = [f(p) for p in pts]
    it = 0
    for it in range(maxiter):
        order = np.argsort(vals); pts = [pts[i] for i in order]; vals = [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) <= tol * (abs(vals[0]) + 1.0) and max(float(np.max(np.abs(p - pts[0]))) for p in pts[1:]) < 1e-9:
            break
        cen = np.mean(pts[:-1], axis=0)
        xr = cen + (cen - pts[-1]); fr = f(xr)
        if fr < vals[0]:
            xe = cen + 2.0 * (cen - pts[-1]); fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = cen + 0.5 * (pts[-1] - cen); fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                for i in range(1, n + 1):
                    pts[i] = pts[0] + 0.5 * (pts[i] - pts[0]); vals[i] = f(pts[i])
    order = np.argsort(vals)
    return pts[order[0]], vals[order[0]], it


def hessian(f, x, h):
    n = len(x); H = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            ei = np.zeros(n); ej = np.zeros(n); ei[i] = h[i]; ej[j] = h[j]
            H[i, j] = (f(x + ei + ej) - f(x + ei - ej) - f(x - ei + ej) + f(x - ei - ej)) / (4 * h[i] * h[j])
    return H


def pair_profile(evals, delta, c, w, d):
    E = np.asarray(evals, float)
    l1, d1, w1 = game_probs(delta + c * E + w, d)      # candidate White
    l2, d2, w2 = game_probs(delta - c * E - w, d)      # candidate Black
    prof = np.stack([l1 * l2, l1 * d2 + d1 * l2, d1 * d2 + w1 * l2 + l1 * w2, w1 * d2 + d1 * w2, w1 * w2], axis=1)
    return prof.mean(axis=0)


def stats_of(p):
    mu = float(p @ SCORES); var = float(p @ (SCORES - mu) ** 2)
    elo = 400.0 * math.log10(mu / (1.0 - mu)); nelo = C_NELO * (mu - 0.5) / math.sqrt(2.0 * var)
    return mu, var, elo, nelo


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-games", required=True); ap.add_argument("--gate-label", default="G119")
    ap.add_argument("--observed-ptnml", required=True, help="e.g. 9,130,435,163,13")
    ap.add_argument("--current-sample", required=True); ap.add_argument("--new-book-meta", required=True)
    ap.add_argument("--deltas", default="0,5,10,15"); ap.add_argument("--runs", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=2026102742); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} exists and is not empty")
    out.mkdir(parents=True, exist_ok=True)
    if sha(PLANNER) != PLANNER_SHA:
        sys.exit("planner sha256 differs from Sol's frozen file")
    spec = importlib.util.spec_from_file_location("s33planner", PLANNER)
    P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)

    rows = read_csv(a.gate_games)
    e = np.array([float(r["eval_white_cp"]) for r in rows]); s = np.array([1.0 if r["cand_is_white"] == "1" else -1.0 for r in rows])
    pts = np.array([float(r["cand_points"]) for r in rows])
    e_clip = np.clip(e, -1000, 1000)                       # mate-like scores do not dominate the fit
    f_full = lambda t: nll(t, e_clip, s, pts, True)
    f_null = lambda t: nll(t, e_clip, s, pts, False)
    x0 = [0.0, 0.5, 0.0, math.log(200.0)]; step = [20.0, 0.3, 20.0, 0.3]
    th, v, it = nelder_mead(f_full, x0, step)
    th0, v0, it0 = nelder_mead(f_null, x0, step)
    H = hessian(f_full, th, np.array([0.5, 0.005, 0.5, 0.005]))
    try:
        cov = np.linalg.inv(H); se = [float(math.sqrt(max(cov[i, i], 0.0))) for i in range(4)]
    except np.linalg.LinAlgError:
        se = [float("nan")] * 4
    delta, c, w, d = float(th[0]), float(th[1]), float(th[2]), float(math.exp(th[3]))
    fit = {"games": int(len(rows)), "pairs": int(len(rows) // 2), "Delta_elo": delta, "c_elo_per_cp": c, "w_elo_white": w, "draw_width_d": d,
           "se": {"Delta_elo": se[0], "c_elo_per_cp": se[1], "w_elo_white": se[2], "log_d": se[3]},
           "neg_loglik": v, "neg_loglik_without_eval": v0, "likelihood_ratio_chi2_1df": 2 * (v0 - v), "iterations": [it, it0],
           "note": "eval clipped to +-1000 cp; pairs treated as independent games given the opening"}
    # goodness of fit on the gate's own openings
    rounds = {}
    for r in rows:
        rounds.setdefault(r["round"], float(r["eval_white_cp"]))
    gate_evals = np.clip(np.array(list(rounds.values())), -1000, 1000)
    obs = np.array([int(x) for x in a.observed_ptnml.split(",")], float); n_pairs = obs.sum()
    pred = pair_profile(gate_evals, delta, c, w, d) * n_pairs
    chi2 = float(np.sum((obs - pred) ** 2 / pred))
    fit["gof_gate_openings"] = {"observed": obs.astype(int).tolist(), "predicted": [round(x, 1) for x in pred], "chi2_4df": chi2}
    books = {f"{a.gate_label}_openings": gate_evals,
             "current_book_sample": np.clip(np.array([float(r["eval_white_cp"]) for r in read_csv(a.current_sample)]), -1000, 1000),
             "candidate_v2_book": np.clip(np.array([float(r["eval_white_cp"]) for r in read_csv(a.new_book_meta)]), -1000, 1000)}
    deltas = [float(x) for x in a.deltas.split(",")]
    table = []; cell = 0
    for name, ev in books.items():
        for dl in deltas:
            p = pair_profile(ev, dl, c, w, d)
            mu, var, elo, nelo = stats_of(p)
            mc = P.simulate_cell(p.tolist(), elo, 0.0, 10.0, 1500, runs=a.runs, seed=a.seed + cell)
            an = P.analytic_cell(p.tolist(), elo, 0.0, 10.0, 1500)
            an3 = P.analytic_cell(p.tolist(), elo, 0.0, 10.0, 3000)
            table.append({"book": name, "openings": int(len(ev)), "Delta_model_elo": dl, "profile": [round(float(x), 6) for x in p],
                          "share_1_1_pairs": round(float(p[2]), 4), "pair_score": round(mu, 5), "logistic_elo": round(elo, 3),
                          "nelo": round(nelo, 3), "sd_pair": round(math.sqrt(var), 5),
                          "c1500_mc": mc["probabilities"], "c1500_mc_mean_games": mc["mean_games"], "c1500_analytic": an["probabilities"],
                          "c1500_analytic_mean_games": an["mean_games"], "c3000_analytic": an3["probabilities"], "c3000_analytic_mean_games": an3["mean_games"],
                          "seed": a.seed + cell})
            cell += 1
    # sensitivity (analytic profiles only, no MC): books whose openings all sit at +-E cp, at Delta = 10
    base_p = pair_profile(books["current_book_sample"], 10.0, c, w, d); _, _, _, base_nelo = stats_of(base_p)
    sens = []
    for E in (0, 25, 50, 75, 100, 125, 150, 200, 250, 300, 400):
        ev = np.array([float(E), -float(E)])
        p = pair_profile(ev, 10.0, c, w, d); mu, var, elo, nelo = stats_of(p)
        sens.append({"abs_eval_cp": E, "share_1_1_pairs": round(float(p[2]), 4), "pair_score": round(mu, 5), "nelo_at_delta10": round(nelo, 3),
                     "games_for_equal_power_vs_current_book": round((base_nelo / nelo) ** 2, 3) if nelo > 0 else None})
    # Sol's own reference cell: measured G119 profile tilted to +9.5 (the planner's convention)
    ref = P.simulate_cell(P.PROFILES["G119"]["counts"], 9.5, 0.0, 10.0, 1500, runs=a.runs, seed=P.VALIDATION_SEED)
    res = {"tool": "forge_sol_S42_power_" + DATE, "tool_sha256": sha(__file__), "planner_sha256": sha(PLANNER),
           "shim": "numpy-only SciPy shim (scipy_shim/), see check_scipy_shim_s42.py", "inputs": {k: sha(getattr(a, k)) for k in ("gate_games", "current_sample", "new_book_meta")},
           "fit": fit, "abs_eval_mean": {k: round(float(np.mean(np.abs(v))), 2) for k, v in books.items()},
           "protocols": {"c1500": "[0,10] nElo, cap 1500 games (Monte-Carlo, runs per cell, + analytic)", "c3000": "[0,10] nElo, cap 3000 games (analytic only)"},
           "table": table, "sensitivity_fixed_abs_eval_delta10": sens, "reference_G119_measured_tilted_9p5_c1500": {"probabilities": ref["probabilities"], "mean_games": ref["mean_games"]},
           "label": "MODEL ESTIMATE / ADVICE: no games were played; no Elo or speed claim"}
    (out / f"forge_sol_S42_power_{DATE}.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    md = ["| book | Delta | 1-1 pairs | pair score | logistic Elo | nElo | P(H1) c1500 MC | P(H0) | P(cap) | mean games | P(H1) c3000 analytic | mean games c3000 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in table:
        m = t["c1500_mc"]; m3 = t["c3000_analytic"]
        md.append(f"| {t['book']} | {t['Delta_model_elo']:+.0f} | {t['share_1_1_pairs']:.3f} | {t['pair_score']:.4f} | {t['logistic_elo']:+.2f} | "
                  f"{t['nelo']:+.2f} | {m['H1']:.4f} | {m['H0']:.4f} | {m['cap']:.4f} | {t['c1500_mc_mean_games']:.0f} | {m3['H1']:.4f} | {t['c3000_analytic_mean_games']:.0f} |")
    md += ["", "Sensitivity (model, analytic, Delta = 10): every opening at +-E cp", "",
           "| abs eval E (cp) | 1-1 pairs | nElo | games for equal power vs current book |", "|---|---|---|---|"]
    md += [f"| {x['abs_eval_cp']} | {x['share_1_1_pairs']:.3f} | {x['nelo_at_delta10']:+.2f} | {x['games_for_equal_power_vs_current_book']} |" for x in sens]
    (out / f"forge_sol_S42_power_table_{DATE}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"fit": fit, "abs_eval_mean": res["abs_eval_mean"]}, indent=1)); print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
