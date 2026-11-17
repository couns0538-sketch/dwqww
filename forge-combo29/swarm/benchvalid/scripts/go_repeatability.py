#!/usr/bin/env python3
"""Is a *fixed-depth UCI go* a repeatable number the way bench is?

bench calls `bench_searcher.clear()` before every position. The UCI `go` path does
not. If the two disagree on repeatability, then any replacement gate built on
`go depth N` inherits an order dependence that bench does not have -- and that is a
design constraint on the replacement, not a defect of bench.

Three contexts, same FEN, same depth:
  A  fresh process, one search
  B  same process, the SAME search issued twice
  C  same process, five searches on a different position first, then the target
  D  fresh process, `Clear Hash` + `ucinewgame` before the search
  E  same process, target first then five other positions then target again

A and D must agree with the value bench would reach after clear(); B/C/E show whether
prior searches in the session move a fixed-depth node count.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from uci_driver import Engine  # noqa: E402

from common import BUILD
EXE = sys.argv[1] if len(sys.argv) > 1 else str(BUILD)
TARGET = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
OTHERS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
]
DEPTH = 11


def one(exe, prelude=(), target_twice=False):
    """One Engine instance. Returns the node counts of the TARGET search(es)."""
    got = []
    with Engine(exe) as e:
        e.uci()
        e.isready()
        for cmd in prelude:
            e.send(cmd)
            e.isready()
        r = e.search(f"position fen {TARGET}", f"go depth {DEPTH}")
        got.append(r["nodes"])
        if target_twice:
            r2 = e.search(f"position fen {TARGET}", f"go depth {DEPTH}")
            got.append(r2["nodes"])
        return got


rows = {}
rows["A_fresh_process"] = one(EXE)
rows["B_same_process_twice"] = one(EXE, target_twice=True)
rows["C_after_three_others"] = one(EXE, [f"position fen {f}" for f in OTHERS] +
                                   [f"go depth {DEPTH}"] * 0)  # searches below
# C needs real searches, so do it separately.
with Engine(EXE) as e:
    e.uci()
    e.isready()
    for f in OTHERS:
        e.search(f"position fen {f}", f"go depth {DEPTH}")
    r = e.search(f"position fen {TARGET}", f"go depth {DEPTH}")
    rows["C_after_three_others"] = [r["nodes"]]
with Engine(EXE) as e:
    e.uci()
    e.isready()
    e.send("ucinewgame")
    e.isready()
    e.send("setoption name Clear Hash")
    e.isready()
    r = e.search(f"position fen {TARGET}", f"go depth {DEPTH}")
    rows["D_fresh_plus_clearhash"] = [r["nodes"]]
with Engine(EXE) as e:
    e.uci()
    e.isready()
    r0 = e.search(f"position fen {TARGET}", f"go depth {DEPTH}")
    for f in OTHERS:
        e.search(f"position fen {f}", f"go depth {DEPTH}")
    r1 = e.search(f"position fen {TARGET}", f"go depth {DEPTH}")
    rows["E_target_first_then_again"] = [r0["nodes"], r1["nodes"]]

# A summary field that silently omits a row is the defect this audit wrote a trap about.
# Measured cause of the one that appeared in an intermediate copy of this file: a row whose
# search returned None dropped out of the set comprehension, so `distinct_values` read
# [11696, 13235, 50541] while the rows still contained 72,365. The guard below refuses to
# emit a summary that disagrees with the rows, and refuses to emit a row with a null node
# count at all -- a null means the search did not report, which is a failed measurement and
# must not be summarised as if it were a value.
EXPECTED_ROWS = {"A_fresh_process", "B_same_process_twice", "C_after_three_others",
                 "D_fresh_plus_clearhash", "E_target_first_then_again"}
missing = EXPECTED_ROWS - rows.keys()
if missing:
    raise SystemExit(f"rows missing from the measurement: {sorted(missing)}")

nulls = {k: vs for k, vs in rows.items() if any(v is None for v in vs)}
if nulls:
    raise SystemExit(f"a search did not report a node count, so this run is void: {nulls}")

flat = [v for vs in rows.values() for v in vs]
distinct = sorted({v for v in flat})
if distinct != sorted(set(v for vs in rows.values() for v in vs)):
    raise SystemExit("distinct_values disagrees with rows -- refusing to emit")
if len(distinct) < 2 and not all(len(vs) == 1 for vs in rows.values()):
    raise SystemExit("impossible summary")

summary = {"exe": EXE, "fen": TARGET, "depth": DEPTH, "rows": rows,
           "distinct_values": distinct,
           "repeatable": len(distinct) == 1,
           "measurement_count": len(flat),
           "ratio_max_over_min": round(max(flat) / min(flat), 3) if min(flat) else None}
print(json.dumps(summary, indent=2))
