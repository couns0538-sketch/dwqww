#!/usr/bin/env python3
"""Emit the failure register: every conversion failure with its position and move list.

The brief requires that a conversion failure be replayable, so this writes, for each
failure, the start FEN, the exact table's verdict and DTM where one exists, the
engine's budget, the ply count, the bail count, and the full SAN move list.

Two kinds of row are kept apart on purpose:
  * a WON position that did not convert -- the conversion failure;
  * a DRAWN position where the engine DEFENDING lost -- a different defect, and one
    the conversion rate must not be allowed to hide.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter

PROD = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fx/prod"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/fx/failures.json"


def main():
    fail = []
    for d in sorted(glob.glob(os.path.join(PROD, "*"))):
        if not os.path.isdir(d):
            continue
        cell = os.path.basename(d)
        for f in sorted(glob.glob(os.path.join(d, "*.jsonl"))):
            for line in open(f):
                r = json.loads(line)
                exp = r.get("expected")
                res = r["result"]
                if exp == "win" and res not in ("converted", "converted_after_timeout"):
                    kind = "won_position_not_converted"
                elif exp == "draw" and res != "drawn":
                    kind = "drawn_position_lost"
                else:
                    continue
                fail.append({
                    "kind": kind,
                    "cell": cell,
                    "family": r.get("family"),
                    "arm": r.get("arm"),
                    "go": r.get("go"),
                    "net": r.get("net"),
                    "fen": r["start_fen"],
                    "expected": exp,
                    "result": res,
                    "term": r["term"],
                    "n_plies": r["n_plies"],
                    "n_moves": (r["n_plies"] + 1) // 2,
                    "n_bails": r.get("n_bails"),
                    "dtm_moves_from_start": r.get("dtm_moves_start"),
                    "final_fen": r.get("final_fen"),
                    "moves": r.get("moves"),
                    "sans": r.get("sans"),
                })

    counts = Counter((x["cell"], x["kind"]) for x in fail)
    by_fam = Counter((x["family"], x["kind"]) for x in fail)
    json.dump({"n": len(fail),
               "by_cell": {f"{a}/{b}": c for (a, b), c in counts.items()},
               "by_family": {f"{a}/{b}": c for (a, b), c in by_fam.items()},
               "failures": fail}, open(OUT, "w"), indent=1)
    print(f"{len(fail)} failures -> {OUT}")
    for (fam, kind), c in sorted(by_fam.items()):
        print(f"  {fam:6s} {kind:26s} {c}")


if __name__ == "__main__":
    main()
