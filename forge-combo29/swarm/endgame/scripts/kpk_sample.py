#!/usr/bin/env python3
"""Stratified sample of KPK cells for the sweep.

The full boundary is 81,664 canonical cells (163,328 placements). Playing all of them
is not achievable in this window, so the sweep uses a stratified sample and says so
with its denominator. The strata are the only two things the outcome depends on
structurally -- the PAWN FILE and the exact table's WIN/DRAW verdict -- so a
within-stratum sample covers the boundary rather than the popular corner of it.

The full table is still used as the oracle for every cell actually played, so the
per-cell verdict is exact even though the coverage is sampled.
"""
import json
import random
import sys
from collections import defaultdict

fx = json.load(open("/tmp/fx/fixtures.json"))
cells = fx["families"]["KPK"]["cells"]
PER_STRATUM = int(sys.argv[1]) if len(sys.argv) > 1 else 12

strata = defaultdict(list)
for c in cells:
    file_ = c["fen"].split("/")[-1]  # not the pawn file; use python-chess
    import chess
    b = chess.Board(c["fen"])
    pawn_sq = next(s for s, p in b.piece_map().items()
                   if p.piece_type == chess.PAWN)
    key = (chess.square_file(pawn_sq), chess.square_rank(pawn_sq) >= 5,
           c["theoretical"])
    strata[key].append(c)

out = []
rng = random.Random(20261117)
for key in sorted(strata):
    pool = sorted(strata[key], key=lambda c: c["fen"])
    take = min(PER_STRATUM, len(pool))
    # evenly spaced, deterministic: a re-run reproduces the same cells
    step = max(1, len(pool) // take)
    out.extend(pool[::step][:take])

for i, c in enumerate(out):
    c["index"] = i
json.dump({"cells": out, "n": len(out), "strata": len(strata),
           "per_stratum": PER_STRATUM,
           "total_cells": len(cells),
           "note": "stratified sample of the full boundary, not the full boundary"},
          open("/tmp/fx/kpk_sample.json", "w"), indent=1)
print(f"{len(out)} cells from {len(strata)} strata "
      f"(pawn file x half x verdict), out of {len(cells)} canonical cells")
tally = defaultdict(int)
for c in out:
    tally[c["theoretical"]] += 1
print("sample verdicts:", dict(tally))
