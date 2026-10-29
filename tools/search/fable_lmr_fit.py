#!/usr/bin/env python3
"""Statistical fit of the LmrTableV2 formula (job FB2-J3).

Input: the CSV written by a FORGE_LMR_STATS build (`FORGE_LMR_STATS_OUT=<csv> forge.exe` + `bench N` ... `quit`):
one row per LMR decision with depth, move count, history, improving, cut_node, tt_pv, quiet, reduced_depth and
raised (1 when the reduced-depth search returned a score above alpha, i.e. the reduction was "too much" and a
re-search followed).

Model: logistic regression of P(raised) on x = [1, ln depth, ln moves, ln depth * ln moves, history / 16384,
improving, cut_node, tt_pv], fitted separately for quiet and noisy moves by Newton-Raphson (IRLS) in numpy.
Output: the coefficients, the sample mean of the log-odds, calibration tables (history and move-count deciles:
predicted vs observed raise rate), the deviance / null deviance, and a C++ snippet for src/search.cpp
(`fb2::LmrV2Quiet` / `fb2::LmrV2Noisy`). The reduction in the engine is
    r = base(depth, moves) + scale * (mean_logodds - logodds(x)),  rounded, >= 0
with `scale` chosen so that one standard deviation of the fitted log-odds moves the reduction by --sigma-plies
(default 0.75 ply); that keeps the average reduction of the lock's table and redistributes it by the fitted
probability that the move raises alpha.

    fable_lmr_fit.py <stats.csv> [--sigma-plies 0.75] [--out fit.json] [--snippet lmr_v2_fit.inc]
"""
import argparse
import json
import sys

import numpy as np


def load(path):
    data = np.genfromtxt(path, delimiter=",", names=True, dtype=np.int64)
    return data


def design(d):
    ld = np.log(np.maximum(d["depth"], 1).astype(np.float64))
    lm = np.log(np.maximum(d["moves"], 1).astype(np.float64))
    h = np.clip(d["history"], -16384, 16384).astype(np.float64) / 16384.0
    X = np.column_stack([np.ones(len(d)), ld, lm, ld * lm, h, d["improving"].astype(np.float64),
                         d["cut_node"].astype(np.float64), d["tt_pv"].astype(np.float64)])
    return X


NAMES = ["intercept", "ln_depth", "ln_moves", "ln_product", "history", "improving", "cut_node", "tt_pv"]


def fit_logistic(X, y, iters=25, ridge=1e-6):
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        z = X @ w
        p = 1.0 / (1.0 + np.exp(-z))
        g = X.T @ (p - y) + ridge * w
        W = p * (1.0 - p)
        H = (X * W[:, None]).T @ X + ridge * np.eye(X.shape[1])
        step = np.linalg.solve(H, g)
        w -= step
        if np.max(np.abs(step)) < 1e-9:
            break
    z = X @ w
    p = 1.0 / (1.0 + np.exp(-z))
    eps = 1e-12
    deviance = -2.0 * float(np.sum(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps)))
    pbar = float(y.mean())
    null = -2.0 * float(np.sum(y * np.log(pbar + eps) + (1 - y) * np.log(1 - pbar + eps)))
    return w, z, p, deviance, null


def calibration(values, p, y, bins=10):
    order = np.argsort(values)
    chunks = np.array_split(order, bins)
    rows = []
    for c in chunks:
        if len(c) == 0:
            continue
        rows.append({"n": int(len(c)), "x_mean": float(values[c].mean()), "pred": float(p[c].mean()), "obs": float(y[c].mean())})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--sigma-plies", type=float, default=0.75)
    ap.add_argument("--out")
    ap.add_argument("--snippet")
    args = ap.parse_args()
    d = load(args.csv)
    result = {"rows": int(len(d)), "sigma_plies": args.sigma_plies, "models": {}}
    snippet = []
    for name, quiet in (("quiet", 1), ("noisy", 0)):
        sel = d["quiet"] == quiet
        sub = d[sel]
        if len(sub) < 1000:
            print(f"{name}: only {len(sub)} rows, skipped")
            continue
        X = design(sub)
        y = sub["raised"].astype(np.float64)
        w, z, p, dev, null = fit_logistic(X, y)
        sd = float(z.std())
        scale = args.sigma_plies / sd if sd > 0 else 0.0
        model = {"rows": int(len(sub)), "raise_rate": float(y.mean()), "coefficients": dict(zip(NAMES, map(float, w))),
                 "mean_logodds": float(z.mean()), "sd_logodds": sd, "scale": scale,
                 "deviance": dev, "null_deviance": null, "pseudo_r2": 1.0 - dev / null if null > 0 else 0.0,
                 "calibration_history": calibration(X[:, 4], p, y), "calibration_moves": calibration(X[:, 2], p, y),
                 "calibration_depth": calibration(X[:, 1], p, y)}
        # the reduction shift implied for a few reference moves
        ref = []
        for depth, moves, hist in ((6, 8, 0), (6, 8, 8000), (6, 8, -8000), (12, 20, 0), (12, 20, 8000), (12, 20, -8000), (3, 4, 0)):
            x = np.array([1.0, np.log(depth), np.log(moves), np.log(depth) * np.log(moves), hist / 16384.0, 0.0, 1.0, 0.0])
            lo = float(x @ w)
            ref.append({"depth": depth, "moves": moves, "history": hist, "logodds": lo, "p_raise": 1.0 / (1.0 + np.exp(-lo)),
                        "shift_plies": scale * (z.mean() - lo)})
        model["reference_shifts"] = ref
        result["models"][name] = model
        c = model["coefficients"]
        snippet.append(f"LmrV2Model LmrV2{name.capitalize()}{{{c['intercept']:.6f}, {c['ln_depth']:.6f}, {c['ln_moves']:.6f}, {c['ln_product']:.6f}, "
                       f"{c['history']:.6f}, {c['improving']:.6f}, {c['cut_node']:.6f}, {c['tt_pv']:.6f}, {model['mean_logodds']:.6f}, {scale:.6f}}};")
        print(f"{name}: rows {len(sub)} raise rate {y.mean():.4f} pseudo-R2 {model['pseudo_r2']:.4f} sd(logodds) {sd:.3f} scale {scale:.3f}")
        print("  coefficients " + ", ".join(f"{k}={v:.4f}" for k, v in c.items()))
        print("  history deciles (pred/obs): " + " ".join(f"{r['pred']:.3f}/{r['obs']:.3f}" for r in model["calibration_history"]))
        print("  moves deciles (pred/obs):   " + " ".join(f"{r['pred']:.3f}/{r['obs']:.3f}" for r in model["calibration_moves"]))
        print("  reference shifts: " + "; ".join(f"d{r['depth']} m{r['moves']} h{r['history']}: {r['shift_plies']:+.2f}" for r in ref))
    if args.out:
        with open(args.out, "w", newline="\n") as f:
            json.dump(result, f, indent=1, sort_keys=True)
    if args.snippet:
        with open(args.snippet, "w", newline="\n") as f:
            f.write("// generated by tools/search/fable_lmr_fit.py\n" + "\n".join(snippet) + "\n")
    print("\n".join(snippet))


if __name__ == "__main__":
    main()
