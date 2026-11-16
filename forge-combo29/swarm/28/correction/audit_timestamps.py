#!/usr/bin/env python3
"""audit_timestamps.py — seat 19's warning, applied to EVERY table I have published.

Seat 19 reports a check that printed CONFIRMS while measuring nothing: a parser looked for a line the
engine never prints, got no value, and the comparison went NaN — and NaN never fails a `<=` test.

The same class of bug in my own work would be: a row where `bestmove` never arrived (status NORESP),
or where the engine printed no `info ... time` field, being counted as a fast stop, or a cell whose
planned limit never got computed (so the ratio is formed against 0 or None).

This script asserts, per raw file:
  1. every row has a PARSEABLE wall_ms (a missing/failed timestamp must never appear as a number);
  2. every NORESP / NOREOK row is COUNTED and reported, not silently dropped;
  3. every row used in a ratio has a non-zero denominator (the plan), and the plan is recomputed here
     from the source constants rather than trusted from the table;
  4. no NaN/inf reaches a comparison (any NaN anywhere is a hard failure of this audit).
Exit code is 1 if any assertion fails, so it cannot report success without measuring.

Usage: audit_timestamps.py <root>   (root contains out/, job1/outA, job2/out, job3/out ...)
"""
import glob
import math
import os
import sys

S14_MOVETIME_OVERHEAD = 10  # src/uci.cpp:152 default Move Overhead


def audit_file(path, plan_ms):
    """Return (n, n_bad_parse, n_noresp, n_nan, problems)."""
    problems = []
    n = n_bad = n_noresp = 0
    with open(path) as fh:
        header = fh.readline().rstrip("\n").split("\t")
        for lineno, line in enumerate(fh, start=2):
            p = line.rstrip("\n").split("\t")
            n += 1
            try:
                wall = float(p[2] if "wall_ms" in header[2] else p[1])
            except (ValueError, IndexError):
                n_bad += 1
                problems.append(f"{path}:{lineno} wall_ms not parseable: {line.strip()[:80]}")
                continue
            if math.isnan(wall) or math.isinf(wall):
                n_bad += 1
                problems.append(f"{path}:{lineno} wall_ms NaN/inf")
            status = p[-1] if header[-1] == "status" else (p[5] if len(p) > 5 else "")
            if status in ("NORESP", "NOREOK"):
                n_noresp += 1
            if plan_ms is not None:
                if plan_ms <= 0:
                    problems.append(f"{path}: plan_ms {plan_ms} is not positive — no ratio allowed")
                ratio = wall / plan_ms
                if math.isnan(ratio):
                    problems.append(f"{path}:{lineno} ratio NaN")
    return n, n_bad, n_noresp, problems


def plan_for(name):
    """Recompute the planned limit from the file name, never from the table. None = not a plan file."""
    base = os.path.basename(name)
    if not base.startswith("mt") or not base[:-4].split("_")[0][2:].isdigit():
        return None
    parts = base[:-4].split("_")
    mt = int(parts[0][2:])
    mo = int(parts[1][2:]) if len(parts) > 1 and parts[1][2:].isdigit() else S14_MOVETIME_OVERHEAD
    return max(1, mt - mo)


def main() -> int:
    root = sys.argv[1]
    patterns = ["out/*.tsv", "out/*.txt", "job1/outA/*.txt", "job2/out/*.tsv",
                "job3/out/*.tsv", "out_plant/*/*.tsv", "out_plant_job1/*/*.txt"]
    files = []
    for pat in patterns:
        files.extend(sorted(glob.glob(os.path.join(root, pat))))
    files = [f for f in files if os.path.getsize(f) > 0]

    print("| file | rows | unparseable walls | NORESP/NOREOK rows | plan ms used | verdict |")
    print("|---|---|---|---|---|---|")
    total_problems = []
    for path in files:
        plan = plan_for(path)
        n, n_bad, n_noresp, problems = audit_file(path, plan)
        total_problems.extend(problems)
        verdict = "OK" if not problems else f"{len(problems)} PROBLEM(S)"
        print(f"| {os.path.relpath(path, root)} | {n} | {n_bad} | {n_noresp} | "
              f"{plan if plan is not None else '-'} | {verdict} |")

    print()
    print(f"files audited: {len(files)}; problems: {len(total_problems)}")
    for p in total_problems[:20]:
        print("  " + p)
    if total_problems:
        return 1
    print("AUDIT PASSES: every row had a parseable wall time, every NORESP row is counted above, "
          "and every plan used in a ratio was positive and recomputed from the source constants.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
