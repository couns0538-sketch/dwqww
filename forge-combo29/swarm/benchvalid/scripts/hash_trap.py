#!/usr/bin/env python3
"""The Hash trap: does `setoption name Hash` move the bench pin?

Two arms, because "the pin did not move" is only interesting if the option path is live.
  arm A: bench 13 after setoption Hash V, for V in {1,16,64,256,1024}
  arm B: a real `go depth` on two FENs after the same setoption. Its node count MUST
         move with Hash somewhere in the range, or setoption reached nothing and
         arm A's invariance is explained by a dead option rather than a literal 16.

Kiwipete at depth 13 is ~210k nodes, below the ~750k threshold the findings record for
Hash sensitivity, so the deeper arms are the positive control.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from uci_driver import Engine  # noqa: E402

from common import BUILD
EXE = sys.argv[1] if len(sys.argv) > 1 else str(BUILD)
KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

rows = []
for h in (1, 16, 64, 256, 1024):
    with Engine(EXE) as e:
        e.uci()
        e.isready()
        baseline = e.bench(13)["nodes"]
        e.setoption("Hash", h)
        after = e.bench(13)["nodes"]
        start14 = e.search(f"position fen {START}", "go depth 14")
        kiwi15 = e.search(f"position fen {KIWIPETE}", "go depth 15")
        rows.append({"hash_mb": h, "bench13_before_setoption": baseline,
                     "bench13_after_setoption": after,
                     "go_start_depth14": {"nodes": start14["nodes"], "bestmove": start14["bestmove"],
                                          "info_lines": start14["info_depth_lines"]},
                     "go_kiwipete_depth15": {"nodes": kiwi15["nodes"], "bestmove": kiwi15["bestmove"],
                                             "info_lines": kiwi15["info_depth_lines"]}})
    print(f"hash {h:5d}  bench13 {after}  start d14 {start14['nodes']}  kiwi d15 {kiwi15['nodes']}", flush=True)

pins = {r["bench13_after_setoption"] for r in rows}
start_nodes = {r["go_start_depth14"]["nodes"] for r in rows}
payload = {"exe": EXE,
           "bench13_distinct_values": sorted(pins),
           "bench13_invariant": len(pins) == 1,
           "go_start_d14_distinct_values": len(start_nodes),
           "rows": rows}
print(json.dumps(payload, indent=2))
