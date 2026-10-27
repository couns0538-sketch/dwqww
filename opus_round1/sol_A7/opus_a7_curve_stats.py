#!/usr/bin/env python3
"""A7 long-training recipe: statistics from the PC's finished H256 runs (read-only inputs).

Inputs: final_table.csv / epoch_curves.csv / seed_spread.csv written by the S30 parser (opus-sol-S30,
forge_sol_S30_log_curves.py) over F:\\forge_nnue_train\\runs, plus the run logs themselves for throughput
("Finished: X positions in Ys") and memory ("MEM ... trainer_private=") lines.

Outputs (to --out, which must not exist): a7_stats.json and a7_tables.md. Deterministic (bootstrap seed fixed).
Every number carries the run log file:line it comes from (the S30 'where' columns).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

SEED_SD_FALLBACK = 7.1e-6  # S30 pooled seed sd of FINAL b0.6 (13 groups), used only if no group has >= 2 members


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fnum(x: str) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def is_main_recipe(r: dict) -> bool:
    """H256 residual, blend-end 0.6, batch 8192, self-play only (no Sol independent data)."""
    return (r.get("shape") == "256" and fnum(r.get("blend-end")) == 0.6 and r.get("batch-size") == "8192"
            and "_sol_" not in r["run"] and fnum(r.get("b06")) is not None and fnum(r.get("train_positions")))


def pooled_seed_sd(spread: list[dict]) -> tuple[float, int, int]:
    """Pooled within-group sd of FINAL b0.6 over recipe groups with >= 2 members (sum of squares / dof)."""
    ss, dof, groups = 0.0, 0, 0
    for g in spread:
        n = int(g["runs"])  # S30's seed_spread.csv: "runs" = count, "members" = the run list
        sd = fnum(g["b06_sd"])
        if n >= 2 and sd is not None:
            ss += (n - 1) * sd * sd
            dof += n - 1
            groups += 1
    return (math.sqrt(ss / dof) if dof else SEED_SD_FALLBACK), groups, dof


def ols(y: np.ndarray, cols: list[np.ndarray]) -> np.ndarray:
    X = np.column_stack([np.ones_like(y)] + cols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def fit_with_ci(rows: list[dict], with_lr: bool, reps: int, seed: int) -> dict:
    y = np.array([float(r["b06"]) for r in rows])
    ln = np.array([math.log2(float(r["train_positions"]) / 1e8) for r in rows])
    le = np.array([math.log2(float(r["epochs"]) / 48.0) for r in rows])
    cols = [ln, le]
    names = ["intercept", "per_doubling_data", "per_doubling_epochs"]
    if with_lr:
        cols.append(np.array([math.log2(float(r["lr"]) / 7.07e-4) for r in rows]))
        names.append("per_doubling_lr")
    beta = ols(y, cols)
    resid = y - np.column_stack([np.ones_like(y)] + cols) @ beta
    rng = np.random.default_rng(seed)
    boots = []
    n = len(y)
    for _ in range(reps):
        idx = rng.integers(0, n, n)
        cb = [c[idx] for c in cols]
        if np.linalg.matrix_rank(np.column_stack([np.ones(n)] + cb)) < len(cb) + 1:
            continue
        boots.append(ols(y[idx], cb))
    boots = np.array(boots)
    lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
    out = {"n_runs": n, "residual_sd": float(np.sqrt(np.sum(resid ** 2) / max(1, n - len(beta)))),
           "bootstrap_reps_used": int(len(boots)), "coef": {}}
    for i, nm in enumerate(names):
        out["coef"][nm] = {"est": float(beta[i]), "ci95": [float(lo[i]), float(hi[i])]}
    # predictions at N = 240M: e64 - e48 and e96 - e48 (b0.6 change; negative = better)
    for e in (64, 96):
        d = math.log2(e / 48.0)
        out[f"pred_e{e}_minus_e48"] = {"est": float(beta[2] * d),
                                       "ci95": sorted([float(lo[2] * d), float(hi[2] * d)])}
    for mult in (1.5, 2.0):
        d = math.log2(mult)
        out[f"pred_data_x{mult}_at_e48"] = {"est": float(beta[1] * d),
                                            "ci95": sorted([float(lo[1] * d), float(hi[1] * d)])}
    return out


def plateau_stats(curves: list[dict], finals: dict[str, dict], sd: float) -> list[dict]:
    by_run: dict[str, list[dict]] = {}
    for c in curves:
        by_run.setdefault(c["run"], []).append(c)
    rows = []
    for run, cs in sorted(by_run.items()):
        f = finals.get(run)
        if not f or not is_main_recipe(f) or int(f["epochs"]) < 16:
            continue
        cs = sorted(cs, key=lambda c: int(c["epoch"]))
        # resumed runs can repeat an epoch: keep the last line per epoch
        last = {}
        for c in cs:
            last[int(c["epoch"])] = c
        eps = sorted(last)
        E = int(f["epochs"])
        if not eps or eps[-1] != E:
            continue
        b = {e: float(last[e]["b06"]) for e in eps}
        final_sub = b[E]
        plateau = next(e for e in eps if abs(b[e] - final_sub) <= sd)
        q = E - max(1, round(0.25 * E))
        imp_last25 = (b[q] - final_sub) if q in b else None
        best_ep = min(eps, key=lambda e: (b[e], e))
        rows.append({"run": run, "epochs": E, "train_positions": int(float(f["train_positions"])),
                     "final_subset_b06": final_sub, "final_full_b06": float(f["b06"]),
                     "plateau_epoch": plateau, "plateau_frac": plateau / E,
                     "subset_b06_gain_last25pct": imp_last25, "best_subset_epoch": best_ep,
                     "best_minus_final": b[best_ep] - final_sub,
                     "where_final": f["where"], "where_last_epoch": last[E]["where"]})
    return rows


FIN_RE = re.compile(r"^Finished: ([\d,]+) positions in (\d+)s")
MEM_RE = re.compile(r"^MEM (.*?) trainer_private=([\d.]+)GB sys_avail=([\d.]+)GB")


def log_resources(runs_dir: Path, names: list[str]) -> list[dict]:
    out = []
    for name in names:
        logs = [runs_dir / f"{name}.log"] + sorted(runs_dir.glob(f"{name}.resume*.log"))
        fin, mems, trainer = None, [], None
        cmd = runs_dir / f"{name}.cmd.txt"
        if cmd.exists():
            t = cmd.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"python -u (\S+\.py)", t)
            trainer = m.group(1) if m else None
        for lp in logs:
            if not lp.exists():
                continue
            for i, line in enumerate(lp.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                m = FIN_RE.match(line)
                if m:
                    fin = {"positions": int(m.group(1).replace(",", "")), "seconds": int(m.group(2)),
                           "where": f"{lp.name}:{i}"}
                m = MEM_RE.match(line)
                if m:
                    mems.append({"tag": m.group(1), "private_gb": float(m.group(2)), "avail_gb": float(m.group(3)),
                                 "where": f"{lp.name}:{i}"})
        row = {"run": name, "trainer": trainer, "resume_logs": len(logs) - 1}
        if fin and fin["seconds"] > 0:
            row.update({"finished_positions": fin["positions"], "finished_seconds": fin["seconds"],
                        "pos_per_s": fin["positions"] / fin["seconds"], "where_finished": fin["where"]})
        if mems:
            row.update({"mem_first": mems[0], "mem_last": mems[-1],
                        "mem_max_private_gb": max(m["private_gb"] for m in mems)})
        out.append(row)
    return out


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--curves", type=Path, required=True, help="dir with the S30 parser's CSVs")
    ap.add_argument("--runs", type=Path, required=True, help="PC runs dir (read-only)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=False)

    finals_list = read_csv(a.curves / "final_table.csv")
    curves = read_csv(a.curves / "epoch_curves.csv")
    spread = read_csv(a.curves / "seed_spread.csv")
    finals = {r["run"]: r for r in finals_list}
    sd, groups, dof = pooled_seed_sd(spread)

    main_rows = [r for r in finals_list if is_main_recipe(r)]
    by_e: dict[int, list[dict]] = {}
    for r in main_rows:
        by_e.setdefault(int(r["epochs"]), []).append(r)
    epoch_table = []
    for e in sorted(by_e):
        rs = by_e[e]
        b = np.array([float(r["b06"]) for r in rs])
        n = np.array([float(r["train_positions"]) for r in rs])
        epoch_table.append({"epochs": e, "runs": len(rs), "b06_mean": float(b.mean()),
                            "b06_sd": float(b.std(ddof=1)) if len(rs) > 1 else None,
                            "b06_min": float(b.min()), "train_min": int(n.min()), "train_max": int(n.max()),
                            "lrs": sorted({r["lr"] for r in rs}),
                            "best_run": min(rs, key=lambda r: float(r["b06"]))["run"],
                            "best_where": min(rs, key=lambda r: float(r["b06"]))["where"]})

    fit_main = fit_with_ci(main_rows, with_lr=False, reps=a.reps, seed=a.seed)
    fit_lr = fit_with_ci(main_rows, with_lr=True, reps=a.reps, seed=a.seed)
    e48 = [r for r in main_rows if r["epochs"] == "48"]
    fit_e48_data = None
    if len(e48) >= 3:
        y = np.array([float(r["b06"]) for r in e48])
        x = np.array([math.log2(float(r["train_positions"]) / 1e8) for r in e48])
        beta = ols(y, [x])
        rng = np.random.default_rng(a.seed)
        bs = []
        for _ in range(a.reps):
            idx = rng.integers(0, len(y), len(y))
            if np.ptp(x[idx]) == 0:
                continue
            bs.append(ols(y[idx], [x[idx]])[1])
        lo, hi = np.percentile(bs, [2.5, 97.5])
        fit_e48_data = {"n_runs": len(e48), "per_doubling_data": float(beta[1]), "ci95": [float(lo), float(hi)],
                        "train_min": int(min(float(r["train_positions"]) for r in e48)),
                        "train_max": int(max(float(r["train_positions"]) for r in e48))}

    plateaus = plateau_stats(curves, finals, sd)
    res = log_resources(a.runs, [r["run"] for r in main_rows])
    v3b = [r for r in res if r.get("trainer") == "train_resid_v3b.py" and "pos_per_s" in r]
    v3b_e48 = [r for r in v3b if finals[r["run"]]["epochs"] == "48"]

    out = {"seed_sd_b06": sd, "seed_sd_groups": groups, "seed_sd_dof": dof,
           "main_recipe_filter": "shape 256, blend-end 0.6, batch 8192, no _sol_ runs",
           "main_runs": len(main_rows), "epoch_table": epoch_table,
           "fit_data_epochs": fit_main, "fit_data_epochs_lr": fit_lr, "fit_e48_data_only": fit_e48_data,
           "plateaus": plateaus,
           "plateau_summary": {
               "runs": len(plateaus),
               "median_plateau_frac": float(np.median([p["plateau_frac"] for p in plateaus])) if plateaus else None,
               "max_plateau_frac": float(max(p["plateau_frac"] for p in plateaus)) if plateaus else None,
               "best_is_last_epoch_runs": sum(1 for p in plateaus if p["best_subset_epoch"] == p["epochs"]),
           },
           "resources": res,
           "v3b_throughput": {
               "runs": len(v3b), "pos_per_s_mean": float(np.mean([r["pos_per_s"] for r in v3b])) if v3b else None,
               "pos_per_s_min": float(min(r["pos_per_s"] for r in v3b)) if v3b else None,
               "pos_per_s_max": float(max(r["pos_per_s"] for r in v3b)) if v3b else None,
               "e48_runs": len(v3b_e48),
               "e48_max_private_gb": float(max(r.get("mem_max_private_gb", 0) for r in v3b_e48)) if v3b_e48 else None}}
    (a.out / "a7_stats.json").write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")

    md = ["# A7 statistics (generated by opus_a7_curve_stats.py; inputs read-only)", "",
          f"Pooled seed sd of FINAL full-holdout b0.6: **{sd:.2e}** ({groups} recipe groups, {dof} dof).", "",
          "## Final full-holdout b0.6 by epoch count (H256, blend-end 0.6, batch 8192, self-play only)", "",
          "| epochs | runs | mean b0.6 | sd | best b0.6 (run, log:line) | train positions | lr |", "|---|---|---|---|---|---|---|"]
    for t in epoch_table:
        sd_s = f"{t['b06_sd']:.2e}" if t["b06_sd"] is not None else "-"
        md.append(f"| {t['epochs']} | {t['runs']} | {t['b06_mean']:.6f} | {sd_s} | {t['b06_min']:.6f} ({t['best_where']}) | "
                  f"{t['train_min']:,}-{t['train_max']:,} | {', '.join(t['lrs'])} |")
    md += ["", "## Fits (OLS, bootstrap 95% CI)", ""]
    for nm, f in (("b0.6 ~ log2 data + log2 epochs", fit_main), ("+ log2 lr", fit_lr)):
        c = f["coef"]
        md.append(f"- {nm} ({f['n_runs']} runs, residual sd {f['residual_sd']:.2e}): per doubling of data "
                  f"{c['per_doubling_data']['est']:+.2e} [{c['per_doubling_data']['ci95'][0]:+.2e}, {c['per_doubling_data']['ci95'][1]:+.2e}]; "
                  f"per doubling of epochs {c['per_doubling_epochs']['est']:+.2e} [{c['per_doubling_epochs']['ci95'][0]:+.2e}, {c['per_doubling_epochs']['ci95'][1]:+.2e}]"
                  + (f"; per doubling of lr {c['per_doubling_lr']['est']:+.2e} [{c['per_doubling_lr']['ci95'][0]:+.2e}, {c['per_doubling_lr']['ci95'][1]:+.2e}]" if "per_doubling_lr" in c else ""))
        md.append(f"  - predicted e64 - e48: {f['pred_e64_minus_e48']['est']:+.2e} {f['pred_e64_minus_e48']['ci95']}; "
                  f"e96 - e48: {f['pred_e96_minus_e48']['est']:+.2e} {f['pred_e96_minus_e48']['ci95']}; "
                  f"1.5x data at e48: {f['pred_data_x1.5_at_e48']['est']:+.2e}; 2x data: {f['pred_data_x2.0_at_e48']['est']:+.2e}")
    if fit_e48_data:
        md.append(f"- e48 runs only, b0.6 ~ log2 data ({fit_e48_data['n_runs']} runs, {fit_e48_data['train_min']:,}-{fit_e48_data['train_max']:,} positions): "
                  f"{fit_e48_data['per_doubling_data']:+.2e} per doubling [{fit_e48_data['ci95'][0]:+.2e}, {fit_e48_data['ci95'][1]:+.2e}]")
    ps = out["plateau_summary"]
    md += ["", "## Plateau: first epoch whose subset b0.6 is within one seed sd of the last epoch's", "",
           f"{ps['runs']} runs; median plateau at {ps['median_plateau_frac']:.2f} of the run, latest at {ps['max_plateau_frac']:.2f}; "
           f"the last epoch is the best subset epoch in {ps['best_is_last_epoch_runs']} runs.", "",
           "| run | epochs | train positions | plateau epoch | gain in last 25% | best subset epoch (best - final) | last epoch line |",
           "|---|---|---|---|---|---|---|"]
    for p in plateaus:
        g = f"{p['subset_b06_gain_last25pct']:+.2e}" if p["subset_b06_gain_last25pct"] is not None else "-"
        md.append(f"| {p['run']} | {p['epochs']} | {p['train_positions']:,} | {p['plateau_epoch']} ({p['plateau_frac']:.2f}) | {g} | "
                  f"{p['best_subset_epoch']} ({p['best_minus_final']:+.1e}) | {p['where_last_epoch']} |")
    vt = out["v3b_throughput"]
    md += ["", "## v3b throughput and memory (Finished / MEM lines)", "",
           f"{vt['runs']} finished v3b runs: {vt['pos_per_s_mean']:,.0f} positions/s mean "
           f"(min {vt['pos_per_s_min']:,.0f}, max {vt['pos_per_s_max']:,.0f}), whole run incl. holdout evaluation; "
           f"e48 runs: {vt['e48_runs']}, highest trainer_private {vt['e48_max_private_gb']} GB.", "",
           "| run | trainer | pos/s | Finished line | first MEM | last MEM |", "|---|---|---|---|---|---|"]
    for r in res:
        if "pos_per_s" not in r:
            continue
        mf, ml = r.get("mem_first"), r.get("mem_last")
        mfs = f"{mf['private_gb']} GB ({mf['where']})" if mf else "-"
        mls = f"{ml['private_gb']} GB ({ml['where']})" if ml else "-"
        md.append(f"| {r['run']} | {r['trainer']} | {r['pos_per_s']:,.0f} | {r['where_finished']} | {mfs} | {mls} |")
    (a.out / "a7_tables.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"seed sd {sd:.3e}; main runs {len(main_rows)}; plateaus {len(plateaus)}; v3b finished {len(v3b)}")
    print(f"fit: data {fit_main['coef']['per_doubling_data']['est']:+.3e} epochs {fit_main['coef']['per_doubling_epochs']['est']:+.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
