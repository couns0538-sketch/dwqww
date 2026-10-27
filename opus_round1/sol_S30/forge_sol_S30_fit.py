"""S30 part 1 fits on final_table.csv (from forge_sol_S30_log_curves.py). Deterministic (fixed seed bootstrap).

  python -I -B forge_sol_S30_fit.py --final F:/opus_scratch/sol_S30/out/final_table.csv --out fit.json

1. Seed spread: runs with the same recipe AND the same training-data size (hidden, epochs, lr, blend-end, batch,
   warmup, train positions), different seeds: sd and range of the FINAL b0.6 / teacher losses. Pooled sd over groups.
2. Data size at a fixed recipe (H256, e48, lr 7.07e-4, blend-end 0.6, batch 8192, warmup 300): least squares
   b0.6 = c + s*ln(train_positions), bootstrap over runs (2000 resamples) for s and for predictions at 250M / 300M.
3. Epochs at a fixed data size (137,381,087 positions, blend-end 0.6, H256): the FINAL losses per epoch count (the
   learning rates differ, so this is not a clean single-factor comparison), and the fit L(E) = Linf + A * E^-alpha
   (alpha grid 0.1..3, least squares on Linf, A) with a leave-one-out range for L(64).
Every number keeps the file:line of its FINAL line.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path

import random

FIXED_E48 = {"shape": "256", "epochs": "48", "lr": "7.07e-4", "blend-end": "0.6", "batch-size": "8192", "warmup-steps": "300"}
FIXED_DATA = 137381087


def load(path: Path) -> list[dict]:
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    for r in rows:
        r["teacher"], r["b06"] = float(r["teacher"]), float(r["b06"])
        r["train_positions"] = int(r["train_positions"]) if r["train_positions"] else None
    return rows


def ols(xs, ys):
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return my - slope * mx, slope


def seed_spread(rows):
    keys = ("shape", "epochs", "lr", "blend-end", "batch-size", "warmup-steps", "train_positions")
    groups = {}
    for r in rows:
        if r["shape"] and r["train_positions"]:
            groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    out, pooled_num, pooled_den = [], {"b06": 0.0, "teacher": 0.0}, 0
    for key, members in sorted(groups.items(), key=lambda kv: [str(x) for x in kv[0]]):
        if len(members) < 2:
            continue
        entry = dict(zip(keys, key))
        entry["runs"] = [f"{m['run']} ({m['where']})" for m in members]
        for metric in ("b06", "teacher"):
            values = [m[metric] for m in members]
            entry[f"{metric}_sd"] = statistics.stdev(values)
            entry[f"{metric}_range"] = max(values) - min(values)
            pooled_num[metric] += statistics.variance(values) * (len(values) - 1)
        pooled_den += len(members) - 1
        out.append(entry)
    pooled = {f"{m}_pooled_sd": math.sqrt(pooled_num[m] / pooled_den) for m in pooled_num} if pooled_den else {}
    return out, pooled


def data_curve(rows, seed):
    family = [r for r in rows if all(r[k] == v for k, v in FIXED_E48.items()) and r["train_positions"]]
    xs = [math.log(r["train_positions"]) for r in family]
    ys = [r["b06"] for r in family]
    c, s = ols(xs, ys)
    rng = random.Random(seed)
    slopes, p250, p300 = [], [], []
    for _ in range(2000):
        pick = [rng.randrange(len(family)) for _ in family]
        bx, by = [xs[i] for i in pick], [ys[i] for i in pick]
        if len(set(bx)) < 2:
            continue
        bc, bs = ols(bx, by)
        slopes.append(bs)
        p250.append(bc + bs * math.log(250e6))
        p300.append(bc + bs * math.log(300e6))

    def ci(v):
        v = sorted(v)
        return [v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]]

    return {"recipe": FIXED_E48, "runs": len(family), "points": [{"run": r["run"], "where": r["where"], "train_positions": r["train_positions"],
                                                                  "b06": r["b06"], "teacher": r["teacher"]} for r in family],
            "fit": {"b06 = c + s*ln(positions)": {"c": c, "s": s, "s_ci95": ci(slopes),
                    "b06_change_per_doubling": s * math.log(2), "b06_change_per_doubling_ci95": [x * math.log(2) for x in ci(slopes)],
                    "pred_250M": c + s * math.log(250e6), "pred_250M_ci95": ci(p250),
                    "pred_300M": c + s * math.log(300e6), "pred_300M_ci95": ci(p300)}}}


def epoch_curve(rows):
    pts = [r for r in rows if r["shape"] == "256" and r["train_positions"] == FIXED_DATA and r["blend-end"] == "0.6"]
    pts.sort(key=lambda r: (int(r["epochs"]), r["run"]))
    out = {"train_positions": FIXED_DATA, "points": [{"run": r["run"], "where": r["where"], "epochs": int(r["epochs"]), "lr": r["lr"],
                                                       "seed": r["seed"], "b06": r["b06"], "teacher": r["teacher"]} for r in pts]}

    def fit(points):
        best = None
        for i in range(1, 31):
            alpha = i / 10
            xs = [p["epochs"] ** -alpha for p in points]
            ys = [p["b06"] for p in points]
            linf, a = ols(xs, ys)
            sse = sum((linf + a * x - y) ** 2 for x, y in zip(xs, ys))
            if best is None or sse < best[0]:
                best = (sse, alpha, linf, a)
        return best

    if len({p["epochs"] for p in out["points"]}) >= 3:
        sse, alpha, linf, a = fit(out["points"])
        loo = []
        for i in range(len(out["points"])):
            sub = out["points"][:i] + out["points"][i + 1:]
            if len({p["epochs"] for p in sub}) >= 3:
                _, al, li, aa = fit(sub)
                loo.append(li + aa * 64 ** -al)
        out["fit_L(E)=Linf+A*E^-alpha"] = {"alpha": alpha, "Linf": linf, "A": a, "sse": sse, "L64": linf + a * 64 ** -alpha,
                                           "L64_leave_one_out_range": [min(loo), max(loo)] if loo else None}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--final", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20261027)
    args = ap.parse_args(argv)
    if args.out.exists():
        ap.error("--out must be a new file")
    rows = load(args.final)
    spread, pooled = seed_spread(rows)
    result = {"tool": "forge_sol_S30_fit", "final_table": str(args.final), "seed_spread_groups": spread, "seed_spread_pooled": pooled,
              "data_curve_e48": data_curve(rows, args.seed), "epoch_curve_fixed_data": epoch_curve(rows)}
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    d = result["data_curve_e48"]["fit"]["b06 = c + s*ln(positions)"]
    print(f"seed spread pooled: {pooled}")
    print(f"e48 data curve ({result['data_curve_e48']['runs']} runs): b0.6 per doubling {d['b06_change_per_doubling']:.6f} "
          f"CI {d['b06_change_per_doubling_ci95']}; pred 250M {d['pred_250M']:.6f} CI {d['pred_250M_ci95']}")
    e = result["epoch_curve_fixed_data"]
    print(f"epochs at {FIXED_DATA}: {[(p['epochs'], p['lr'], p['b06']) for p in e['points']]}")
    print(f"L(E) fit: {e.get('fit_L(E)=Linf+A*E^-alpha')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
