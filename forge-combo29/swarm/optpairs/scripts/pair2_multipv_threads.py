"""Pair 2: MultiPV x Threads. Confirms the audit's "helpers stay idle" result.

The audit's evidence (3): a Threads-4 MultiPV-3 search is identical to Threads 1
on 5 of 5 repeats, while the MultiPV-1 control differs on 5 of 5. Source:
`Searcher::search` builds `all` from the main worker only when
`worker_limits.multipv > 1` and starts no helper threads when `multipv <= 1`
fails (search.cpp:2699-2741).

This re-runs it on this build so the citation is earned, and adds the arm the
original did not need: MPV 1 at T1 vs T4, which MUST differ, otherwise the test
cannot tell "helpers idle" from "threading never worked here".

Cells: {T1, T4} x {MPV 1, MPV 3}; 5 repeats per cell, 6 positions.
"""
import json
import os
import statistics
import sys

import grid
import uci

GO = "go depth 12"
REPEATS = 5
POS = grid.POSITIONS[:6]
ARM = [
    ("T1_MPV1", {"Threads": "1", "MultiPV": "1", "Hash": "32"}),
    ("T4_MPV1", {"Threads": "4", "MultiPV": "1", "Hash": "32"}),
    ("T1_MPV3", {"Threads": "1", "MultiPV": "3", "Hash": "32"}),
    ("T4_MPV3", {"Threads": "4", "MultiPV": "3", "Hash": "32"}),
]


def identical_all(row_a, row_b):
    """True when every run of A equals every run of B on the audit's four fields."""
    sa = {uci.sig(r) for r in row_a}
    sb = {uci.sig(r) for r in row_b}
    return len(sa) == 1 and len(sb) == 1 and sa == sb


def main():
    r = grid.grid("pair2-multipv-threads", ARM, POS, GO, repeats=REPEATS)
    out = {"grid": r["grid"], "go": GO, "repeats": REPEATS, "positions": len(POS),
           "acceptance_failures": grid.acceptance(r), "cells": {}}
    for label in r["cells"]:
        per = {}
        for pos_name, row in r["rows"][label].items():
            per[pos_name] = {"distinct_signatures": len({uci.sig(x) for x in row["runs"]}),
                             "self_differs": row["self_differs"], "self_fields": row["self_fields"],
                             "signature": list(uci.sig(row["runs"][0])),
                             "lines_per_search": [x["infos"] for x in row["runs"]]}
        out["cells"][label] = per
    comparisons = [
        ("MultiPV 3: Threads 1 vs Threads 4", "T1_MPV3", "T4_MPV3"),
        ("MultiPV 1 control: Threads 1 vs Threads 4", "T1_MPV1", "T4_MPV1"),
        ("Threads 1: MultiPV 1 vs 3", "T1_MPV1", "T1_MPV3"),
        ("Threads 4: MultiPV 1 vs 3", "T4_MPV1", "T4_MPV3"),
    ]
    out["comparisons"] = []
    for label, left, right in comparisons:
        rows = []
        for pos_name in r["rows"][left]:
            a = r["rows"][left][pos_name]["runs"]
            b = r["rows"][right][pos_name]["runs"]
            rows.append({"position": pos_name, "identical_every_run": identical_all(a, b),
                         "fields_between_first_runs": uci.moved(a[0], b[0])})
        out["comparisons"].append({"comparison": label, "rows": rows,
                                   "identical": sum(1 for x in rows if x["identical_every_run"]),
                                   "same_signature": sum(1 for x in rows if not x["fields_between_first_runs"])})
    with open(os.path.join(grid.EVID, "pair2-analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"grid pair2, {GO}, {REPEATS} repeats, {len(POS)} positions")
    print("acceptance failures:", out["acceptance_failures"] or "none")
    for label in r["cells"]:
        d = [v["distinct_signatures"] for v in out["cells"][label].values()]
        print(f"  cell {label:9s} distinct signatures per position {d}")
    for c in out["comparisons"]:
        print(f"  {c['comparison']:44s} identical (every run) {c['identical']}/{len(POS)}"
              f"   same first-run signature {c['same_signature']}/{len(POS)}")


if __name__ == "__main__":
    sys.exit(main())
