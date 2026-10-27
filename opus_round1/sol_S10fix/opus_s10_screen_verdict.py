#!/usr/bin/env python3
"""S10-1 (process): screen verdict for an OFF-default search idea, and whether B qualification may start.

Rule (QA, SOL_LEFTOVERS_FOR_CLAUDE.md section 3, S10-1):
  * the idea FAILS if its single Lprime WAC300 ON screen (1000 ms/position) solves fewer than 283/300, or
  * if the deep-node guard fails: |ON/OFF - 1| > 0.20 at depth 20 or depth 22 (fixed OFF references), or
  * if a required number is missing (an unrun screen is not a pass).
  A FAILED idea is rejected and its B qualification is SKIPPED (no B build, no B bench, no B CTest).
  Cheap gates come first: d11 activation (ON d11 != OFF d11), the 5-depth node guard, then WAC; full Std/ASan on
  Lprime and B only for an idea that passed all three.
Input: JSON {"ideas": [{"name", "wac_solved", "off_nodes": {"20":..,"22":..}, "on_nodes": {...},
             "on_d11", "off_d11"}]} or --sol-consolidated <Sol's S10 consolidated results JSON>.
Output: one line per idea + JSON (--out).
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

WAC_FLOOR = 283
GUARD_LIMIT = 0.20
GUARD_DEPTHS = (20, 22)


def guard(off_nodes, on_nodes):
    """Return (status, {depth: change}) for the deep-node guard; MISSING if a guard depth is absent."""
    change = {}
    for d in GUARD_DEPTHS:
        off, on = off_nodes.get(str(d)), on_nodes.get(str(d))
        if off is None or on is None or off <= 0:
            return "MISSING", change
        change[d] = on / off - 1.0
    return ("FAIL" if any(abs(c) > GUARD_LIMIT for c in change.values()) else "PASS"), change


def verdict(idea):
    reasons = []
    off_d11, on_d11 = idea.get("off_d11"), idea.get("on_d11")
    if off_d11 is None or on_d11 is None:
        reasons.append("d11 activation not run")
    elif on_d11 == off_d11:
        reasons.append("option inert: ON d11 == OFF d11")
    g, change = guard(idea.get("off_nodes", {}), idea.get("on_nodes", {}))
    if g == "MISSING":
        reasons.append("deep-node guard not run (d20/d22 missing)")
    elif g == "FAIL":
        bad = [f"d{d} {100 * c:+.1f}%" for d, c in change.items() if abs(c) > GUARD_LIMIT]
        reasons.append("deep-node guard FAIL (" + ", ".join(bad) + ")")
    wac = idea.get("wac_solved")
    if wac is None:
        reasons.append("WAC300 ON screen not run")
    elif wac < WAC_FLOOR:
        reasons.append(f"WAC300 ON {wac}/300 < {WAC_FLOOR}")
    status = "FAIL" if reasons else "PASS"
    return {"name": idea["name"], "status": status, "reasons": reasons,
            "guard_change_percent": {str(d): round(100 * c, 3) for d, c in change.items()},
            "B_qualification": "SKIP" if status == "FAIL" else "ALLOWED"}


def from_sol_consolidated(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    ideas = []
    for f in data["features"]:
        rel = f["bases"]["Lprime"]["release"]
        ideas.append({"name": f["option"], "wac_solved": f["one_original_Lprime_WAC"]["solved"],
                      "off_nodes": rel["off_nodes"], "on_nodes": rel["on_nodes"],
                      "off_d11": rel["activation"]["off_nodes"], "on_d11": rel["activation"]["on_nodes"],
                      "sol_B_status": f["bases"]["B"].get("status")})
    return ideas


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--input")
    src.add_argument("--sol-consolidated")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    ideas = (from_sol_consolidated(a.sol_consolidated) if a.sol_consolidated
             else json.loads(Path(a.input).read_text(encoding="utf-8"))["ideas"])
    rows = []
    for idea in ideas:
        v = verdict(idea)
        if "sol_B_status" in idea:
            v["sol_ran_B_anyway"] = idea["sol_B_status"]
        rows.append(v)
        print(f"{v['name']}: {v['status']}; B qualification {v['B_qualification']}"
              + (f" (Sol ran B: {v['sol_ran_B_anyway']})" if "sol_ran_B_anyway" in v else "")
              + ("; " + "; ".join(v["reasons"]) if v["reasons"] else ""))
    if a.out:
        Path(a.out).write_text(json.dumps({"rule": {"wac_floor": WAC_FLOOR, "guard_limit": GUARD_LIMIT,
                                                    "guard_depths": list(GUARD_DEPTHS)}, "verdicts": rows}, indent=1) + "\n",
                               encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
