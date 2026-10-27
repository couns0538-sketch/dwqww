#!/usr/bin/env python3
"""S-A6: check an SPSA plan JSON against the S15 tunables catalog and print its schedule and QA-slot budget.

Checks (exit 1 on any error):
  - the catalog file matches the sha256 in the plan;
  - every catalog parameter is in exactly one stage or one exclusion group, and no unknown names appear;
  - every SPSA parameter has default within [min, max], a range of at least 50 units, and 1 <= c_end <= 10% of range.
Warnings (no failure): the first perturbation (c_1 = c_end * N^gamma) crosses a range bound, so it is clamped.

Schedule (Spall / fishtest style): N = games / (2 * pairs_per_iteration) iterations, A = A_frac * N,
c_k = c / (k + 1)^gamma with c = c_end * N^gamma, a_k = a / (A + k + 1)^alpha with a = r_end * c_end^2 * (A + N)^alpha.
Budget: seconds per game per slot = 2 * (share * base + inc * moves_per_side), calibrated so 10+0.1 gives the measured
29 s; hours = games * seconds / concurrency / 3600.

usage: python -I -B opus_sa6_plan_check.py --plan <plan.json> [--out <new dir>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sec_per_game(tc: str, share: float, moves: float) -> float:
    base, inc = (float(x) for x in tc.split("+"))
    return 2.0 * (share * base + inc * moves)


def check(plan: dict, catalog: dict) -> dict:
    errors, warnings = [], []
    cat = {p["name"]: p for p in catalog["parameters"]}
    seen: dict[str, str] = {}
    for st in plan["stages"]:
        for name in st["params"]:
            if name in seen:
                errors.append(f"{name} in both {seen[name]} and {st['name']}")
            seen[name] = st["name"]
    for group, names in plan["excluded"].items():
        for name in names:
            if name in seen:
                errors.append(f"{name} in both {seen[name]} and excluded:{group}")
            seen[name] = f"excluded:{group}"
    unknown = sorted(set(seen) - set(cat))
    missing = sorted(set(cat) - set(seen))
    if unknown:
        errors.append(f"unknown parameters: {unknown}")
    if missing:
        errors.append(f"catalog parameters not assigned: {missing}")

    sch = plan["spsa_schedule"]
    tp = plan["throughput"]
    cal = sec_per_game("10+0.1", tp["engine_share_of_base"], tp["moves_per_side"])
    if abs(cal - tp["measured_sec_per_game_per_slot_10+0.1"]) > 0.5:
        errors.append(f"throughput model gives {cal:.1f} s at 10+0.1, measured {tp['measured_sec_per_game_per_slot_10+0.1']}")
    stages_out = []
    for st in plan["stages"]:
        n_iter = st["games"] // (2 * st["pairs_per_iteration"])
        A = sch["A_frac"] * n_iter
        sec = sec_per_game(st["tc"], tp["engine_share_of_base"], tp["moves_per_side"])
        hours = st["games"] * sec / st["concurrency"] / 3600.0
        rows = []
        for name, c_end in st["params"].items():
            p = cat.get(name)
            if p is None:
                continue
            lo, hi, d = p["minimum"], p["maximum"], p["default"]
            rng = hi - lo
            if not lo <= d <= hi:
                errors.append(f"{name}: default {d} outside [{lo}, {hi}]")
            if rng < 50:
                errors.append(f"{name}: range {rng} < 50 units (too coarse for SPSA)")
            if not (1 <= c_end <= 0.1 * rng):
                errors.append(f"{name}: c_end {c_end} not in [1, {0.1 * rng:g}]")
            c = c_end * n_iter ** sch["gamma"]
            a = sch["r_end"] * c_end ** 2 * (A + n_iter) ** sch["alpha"]
            if d - c < lo or d + c > hi:
                warnings.append(f"{name}: first perturbation +-{c:.1f} around {d} crosses [{lo}, {hi}] (clamped)")
            rows.append({"name": name, "default": d, "min": lo, "max": hi, "c_end": c_end,
                         "c_end_frac_of_range": c_end / rng, "c_1": c, "a": a})
        stages_out.append({"name": st["name"], "params": len(st["params"]), "games": st["games"], "tc": st["tc"],
                           "concurrency": st["concurrency"], "iterations": n_iter, "A": A,
                           "sec_per_game_per_slot": sec, "qa_slot_hours": hours, "rows": rows})
    val = plan["validation"]
    stc_h = val["stc_gate"]["cap_games"] * sec_per_game(val["stc_gate"]["tc"], tp["engine_share_of_base"], tp["moves_per_side"]) / val["stc_gate"]["concurrency"] / 3600
    ltc_h = val["ltc_confirm"]["cap_games"] * sec_per_game(val["ltc_confirm"]["tc"], tp["engine_share_of_base"], tp["moves_per_side"]) / val["ltc_confirm"]["concurrency"] / 3600
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "assigned": {k: sum(1 for v in seen.values() if v == k) for k in sorted(set(seen.values()))},
            "catalog_params": len(cat), "stages": stages_out,
            "validation_hours_max": {"stc_gate": stc_h, "ltc_confirm": ltc_h},
            "total_qa_slot_hours_max": sum(s["qa_slot_hours"] for s in stages_out) + stc_h + ltc_h}


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    plan = json.loads(a.plan.read_text(encoding="utf-8"))
    cat_path = (a.plan.parent / plan["catalog"]).resolve()
    data = cat_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != plan["catalog_sha256"]:
        print(f"FAIL catalog sha256 mismatch: {cat_path}")
        return 1
    res = check(plan, json.loads(data.decode("utf-8")))
    for s in res["stages"]:
        print(f"stage {s['name']}: {s['params']} params, {s['games']:,} games at {s['tc']} conc {s['concurrency']}: "
              f"{s['iterations']:,} iterations (A {s['A']:.0f}), {s['sec_per_game_per_slot']:.1f} s/game/slot, "
              f"{s['qa_slot_hours']:.1f} QA-slot hours")
        for r in s["rows"]:
            print(f"  {r['name']:<24} default {r['default']:>6} [{r['min']}, {r['max']}] c_end {r['c_end']:>4} "
                  f"({100 * r['c_end_frac_of_range']:.1f}% of range) c_1 {r['c_1']:.1f} a {r['a']:.3g}")
    v = res["validation_hours_max"]
    print(f"validation (caps): STC gate {v['stc_gate']:.1f} h, LTC confirm {v['ltc_confirm']:.1f} h; "
          f"total at most {res['total_qa_slot_hours_max']:.1f} QA-slot hours")
    print(f"assignment: {res['assigned']} of {res['catalog_params']} catalog parameters")
    for w in res["warnings"]:
        print("WARNING", w)
    for e in res["errors"]:
        print("ERROR", e)
    if a.out:
        a.out.mkdir(parents=True, exist_ok=False)
        (a.out / "plan_check.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"RESULT {'PASS' if res['ok'] else 'FAIL'}")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
