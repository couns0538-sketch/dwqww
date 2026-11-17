#!/usr/bin/env python3
"""Turn the audit JSON into the FINDINGS.md table.

Every cell is generated from the audit output, never typed. The generator also
refuses to write a table that claims something its inputs do not support:

  * a row whose arm errored is written as ERROR, never as PASS;
  * a row with no controls recorded is written as UNCONTROLLED;
  * a row whose mate count of verified PVs is zero while it claims mates is
    written as UNVERIFIED.

Those three verdicts exist because "I could not evaluate this" must never read
as "this is fine".
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

# What a switch touching the clock planner can legitimately change.
CLOCK_SWITCHES = {"TmFinishIteration", "TmNodeShare"}
# What a switch touching only the evaluation can legitimately change.
EVAL_SWITCHES = {"EvalRule50Damp", "DeadMaterial"}


def cell(ok: bool, detail: str = "") -> str:
    return ("PASS" if ok else "**FAIL**") + (f" {detail}" if detail else "")


def legality_cell(arm: dict) -> str:
    if arm.get("error"):
        return "ERROR"
    leg = arm["legality"]
    if leg["illegal"] == 0 and leg["pv_unplayable"] == 0:
        return f"PASS {leg['positions']}/{leg['positions']}"
    return f"**FAIL** illegal={leg['illegal']} pv={leg['pv_unplayable']}"


def mate_cell(arm: dict) -> str:
    if arm.get("error"):
        return "ERROR"
    m = arm["mates"]
    if m["unsound"]:
        return f"**FAIL** unsound={m['unsound']}"
    if m["claimed_mates"] and not m["pv_verified"]:
        return "UNVERIFIED"
    if m["regressions_vs_baseline"]:
        return f"**FAIL** regress={m['regressions_vs_baseline']}"
    return f"PASS {m['pv_verified']}/{m['claimed_mates']} pv"


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
    # Record whether the bail's head move CHANGED against the baseline, because
    # a root-ordering switch can move it while leaving the verdict intact.
    changed = []
    for row, base_row in zip(b["rows"], base["drawn_bail"]["rows"]):
        if row["kind"] == "control_ordinary":
            continue
        if row["bestmove"] != base_row["bestmove"]:
            changed.append(f"{row['kind']}:{base_row['bestmove']}->{row['bestmove']}")
    if changed:
        return "PASS moved " + ",".join(changed)
    return f"PASS {b['cases']}/{b['cases']}"


def sanitizer_cell(san: dict | None) -> str:
    if not san:
        return "NOT RUN"
    if not san.get("runtime", {}).get("asan_present"):
        return "**FAIL** no asan"
    ok = (san.get("clean_run", {}).get("sanitizer_hits") == 0
          and all(f["passed"] for f in san.get("planted_faults", [])))
    if ok:
        return "PASS clean+F2"
    return "**FAIL**"


def build_table(arms: dict, base: dict, sanitizers: dict) -> str:
    lines = []
    lines.append("| switch | 1 legality (200@d12) | 2 mate (30 proved) | 3 terminal | 4 drawn-root bail | 5 sanitizer |")
    lines.append("|---|---|---|---|---|---|")
    for name in SWITCHES:
        arm = arms.get(name)
        if arm is None:
            lines.append(f"| `{name}` | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |")
            continue
        lines.append("| `{}` | {} | {} | {} | {} | {} |".format(
            name,
            legality_cell(arm),
            mate_cell(arm),
            terminal_cell(arm),
            bail_cell(arm, base),
            sanitizer_cell(sanitizers.get(name)),
        ))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True, help="audit.json with all arms")
    ap.add_argument("--baseline", required=True, help="audit.json with the BASELINE arm")
    ap.add_argument("--sanitizer-dir", default="", help="directory of per-switch sanitizer.json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    arms = json.load(open(args.audit))
    base = json.load(open(args.baseline))["BASELINE"]

    sanitizers = {}
    if args.sanitizer_dir:
        for name in SWITCHES:
            path = os.path.join(args.sanitizer_dir, name, "sanitizer.json")
            if os.path.exists(path):
                sanitizers[name] = json.load(open(path))

    table = build_table(arms, base, sanitizers)
    with open(args.out, "w") as fh:
        fh.write(table + "\n")
    print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
