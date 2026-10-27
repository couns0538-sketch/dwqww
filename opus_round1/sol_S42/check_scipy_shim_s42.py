#!/usr/bin/env python3
"""Validate the numpy-only SciPy shim: Sol's UNCHANGED S33 planner re-runs his six frozen validation cells and must
reproduce his receipt (forge_sol_S33_six_cell_validation_20261026.json): Monte-Carlo outcome probabilities and mean
games EXACTLY, analytic probabilities / mean games within 1e-6. Also runs the shim's own unit checks.
usage: python -I -B check_scipy_shim_s42.py  (from anywhere; paths are relative to this file)"""
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scipy_shim"))
sys.path.insert(0, str(HERE / "sol_S33"))
import numpy as np  # noqa: E402
import scipy  # noqa: E402  (the shim)
from scipy.integrate import quad  # noqa: E402
from scipy.optimize import brentq  # noqa: E402
from scipy.special import log_ndtr, logsumexp  # noqa: E402

PLANNER = HERE / "sol_S33" / "forge_sol_S33_sprt_planner_20261026.py"
RECEIPT = HERE / "sol_S33" / "forge_sol_S33_six_cell_validation_20261026.json"
PINS = {PLANNER.name: "008819d5387cdd5ac5d512bb2ebafd09f141aafc9b6904cba2f73a8373634d03",
        "forge_sol_S06_statistics_20261026.py": "4598c5839519af2ed4680b074669d097b9616dfe7c03c1afb7622b276efecb8a",
        RECEIPT.name: "a1fee477dd067ba06cde45df52b782e8fbdc75a29929f843f494a23c677931a3"}


def main():
    out = {"shim": scipy.SHIM, "pins": {}, "unit": {}, "cells": []}
    for name, pin in PINS.items():
        h = hashlib.sha256((HERE / "sol_S33" / name).read_bytes()).hexdigest()
        out["pins"][name] = h == pin
    # shim unit checks against closed forms
    out["unit"]["logsumexp"] = abs(logsumexp(np.array([-np.inf, 0.0, math.log(3.0)])) - math.log(4.0)) < 1e-15
    out["unit"]["brentq_sqrt2"] = abs(brentq(lambda x: x * x - 2, 0, 2, xtol=1e-13) - math.sqrt(2)) < 1e-13
    out["unit"]["log_ndtr_0"] = abs(log_ndtr(0.0) - math.log(0.5)) < 1e-15
    out["unit"]["log_ndtr_tail"] = abs(log_ndtr(-30.0) - (-454.3212439955)) < 1e-6 and abs(log_ndtr(8.0) + 6.22096057427e-16) < 1e-20
    out["unit"]["quad_gauss"] = abs(quad(lambda t: math.exp(-t * t), 0, 5, epsabs=1e-12, epsrel=1e-12)[0] - math.sqrt(math.pi) / 2 * math.erf(5)) < 1e-12
    import importlib.util
    spec = importlib.util.spec_from_file_location("s33planner", PLANNER)
    P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
    ref = json.loads(RECEIPT.read_text(encoding="utf-8"))
    res = P.run_validation(runs=20000, seed=P.VALIDATION_SEED)
    worst_analytic = 0.0; mc_exact = True
    for got, want in zip(res["cells"], ref["cells"]):
        same_mc = got["mc"] == want["mc"] and got["mc_mean_games"] == want["mc_mean_games"] and got["mc_median_games"] == want["mc_median_games"]
        d_an = max(abs(got["analytic"][k] - want["analytic"][k]) for k in ("H1", "H0", "cap"))
        d_mean = abs(got["analytic_mean_games"] - want["analytic_mean_games"])
        mc_exact &= same_mc; worst_analytic = max(worst_analytic, d_an)
        out["cells"].append({"id": got["id"], "mc_identical": same_mc, "mc": got["mc"], "receipt_mc": want["mc"],
                             "analytic_max_abs_diff": d_an, "analytic_mean_games_abs_diff": d_mean,
                             "analytic_median_games": [got["analytic_median_games"], want["analytic_median_games"]]})
    out["validation_status_recomputed"] = res["status"]
    out["mc_all_identical"] = mc_exact; out["analytic_worst_abs_diff"] = worst_analytic
    out["unit"] = {k: bool(v) for k, v in out["unit"].items()}
    ok = all(out["pins"].values()) and all(out["unit"].values()) and mc_exact and worst_analytic <= 1e-6 \
        and all(c["analytic_mean_games_abs_diff"] <= 1e-3 for c in out["cells"]) and res["status"] == "PASS"
    out["result"] = "PASS" if ok else "FAIL"
    print(json.dumps(out, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
