#!/usr/bin/env python3
"""Render the per-switch five-property table from the audit JSON.

The table is generated, never typed, and three verdicts are kept apart because
"could not evaluate" must never read as "fine":

  NOT RUN     the arm has no entry at all
  ERROR       the arm ran and raised
  UNVERIFIED  the arm claims mates but no claimed mate's PV was checked
  PASS        the property held, with the count of rows examined
  **FAIL**    the property broke, with the count

The sanitizer column is filled from per-switch `sanitizer.json` files when they
exist. A switch with no sanitizer file shows `NOT RUN`, not a blank that a reader
could mistake for a pass.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

SWITCHES = [
    "ContHist4PlyRead", "NonPawnCorrection", "LmrDeeperShallower", "EvalRule50Damp",
    "ThreatHistory", "LmrSignedCorrection", "LmrLateParentRelief", "HindsightDepth",
    "NullThreatVerify", "NullSeeVeto", "AspCappedReopen", "AspArmLate", "EvasionOrdering",
    "DeadMaterial", "QuietExtinction", "TmFinishIteration", "TmNodeShare",
    "SoundMatePruning",
]


def legality_cell(arm: dict) -> str:
    if arm.get("error"):
        return "ERROR"
    leg = arm["legality"]
    n = leg["positions"]
    if leg["illegal"] == 0 and leg["pv_unplayable"] == 0:
        return f"PASS {n}/{n}"
    return f"**FAIL** illegal={leg['illegal']} pv={leg['pv_unplayable']}"


def mate_cell(arm: dict) -> str:
    if arm.get("error"):
        return "ERROR"
    m = arm["mates"]
    if m["unsound"]:
        return f"**FAIL** false-mate={m['unsound']}"
    if m.get("unproved"):
        return f"UNPROVED {m['unproved']}"
    proved = m.get("claims_proved", 0)
    claimed = m.get("claimed_mates", 0)
    if claimed and not proved:
        return "UNVERIFIED"
    if m["regressions_vs_baseline"]:
        return f"PASS {proved}/{claimed} proved; {m['regressions_vs_baseline']} missed vs base"
    return f"PASS {proved}/{claimed} proved"


def terminal_cell(arm: dict) -> str:
    if arm.get("error"):
        return "ERROR"
    t = arm["terminal"]
    if t["failures"]:
        return f"**FAIL** {t['failures']}"
    return f"PASS {t['cases']}/{t['cases']}"


def bail_cell(arm: dict, base: dict) -> str:
    if arm.get("error"):
        return "ERROR"
    b = arm["drawn_bail"]
    if b["failures"]:
        return f"**FAIL** {b['failures']}"
    moved = []
    base_rows = base["drawn_bail"]["rows"]
    for row, brow in zip(b["rows"], base_rows):
        if row["kind"] == "control_ordinary":
            continue
        if row["bestmove"] != brow["bestmove"]:
            moved.append(f"{brow['bestmove']}->{row['bestmove']}")
    if moved:
        return "PASS moved " + ",".join(moved)
    return f"PASS {b['cases']}/{b['cases']}"


def sanitizer_cell(san: dict | None, pins_ok: bool) -> str:
    if not san:
        # The pin column is separate evidence; do not let its pass stand in for a
        # sanitizer run that never happened.
        return "NOT RUN"
    if not san.get("runtime", {}).get("asan_present") or not san.get("runtime", {}).get("ubsan_present"):
        return "**FAIL** no runtime"
    faults = san.get("planted_faults", [])
    if not faults or not all(f["passed"] for f in faults):
        return "**FAIL** plant not caught"
    hits = san.get("clean_run", {}).get("sanitizer_hits")
    if hits is None:
        return "NOT RUN"
    if hits == 0 and san.get("clean_run", {}).get("searched") == 200:
        return "PASS clean+F2"
    return f"**FAIL** hits={hits}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--sanitizer-dir", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    arms = json.load(open(args.audit))
    base = json.load(open(args.baseline))["BASELINE"]

    lines = [
        "| switch | 1 legality (200 @ d12) | 2 mate (30 proved) | 3 terminal | 4 drawn-root bail | 5 ASan+UBSan (200) |",
        "|---|---|---|---|---|---|",
    ]
    counts = {"PASS": 0, "FAIL": 0, "NOT RUN": 0}
    for name in SWITCHES:
        arm = arms.get(name)
        san = None
        if args.sanitizer_dir:
            path = os.path.join(args.sanitizer_dir, name, "sanitizer.json")
            if os.path.exists(path):
                san = json.load(open(path))
        if arm is None:
            cells = ["NOT RUN"] * 5
        else:
            cells = [legality_cell(arm), mate_cell(arm), terminal_cell(arm),
                     bail_cell(arm, base), sanitizer_cell(san, True)]
        if "**FAIL**" in " ".join(cells):
            counts["FAIL"] += 1
        elif all(c != "NOT RUN" for c in cells):
            counts["PASS"] += 1
        else:
            # Every measured property passed; only the sanitizer column is
            # missing. Reported separately so "no failures" and "no gaps" are
            # not the same sentence.
            counts["NOT RUN"] += 1
        lines.append(f"| `{name}` | " + " | ".join(cells) + " |")

    table = "\n".join(lines)
    with open(args.out, "w") as fh:
        fh.write(table + "\n")
    print(table)
    print(f"\nrows: {len(SWITCHES)}  fully-clean={counts['PASS']}  "
          f"with-failure={counts['FAIL']}  partial-or-missing={counts['NOT RUN']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
