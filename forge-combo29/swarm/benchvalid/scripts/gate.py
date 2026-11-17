#!/usr/bin/env python3
"""Proposed replacement gate: `forge gate` — seven checks, one process, one minute.

Design constraints, each one paid for by a measurement in evidence/:

G1  PIN    bench 11/13/16 + perft 5, sent on STDIN (argv prints nothing, exits 0).
G2  DRAW   a drawn root must return a searched move: nodes > 0, pv non-empty.
           bench has no drawn root and cannot see the bail (blind spot B9).
G3  BOOK   a booked position must emit `info string book move` and no `info depth`.
           bench never enters the UCI `go` branch, so the book is invisible (B1/B4).
G4  CLOCK  `go wtime 1000 btime 1000` must return inside a wall bound and must
           emit at least one `info depth`. bench is depth-only (B6).
G5  THREAD bench never reads Threads (Searcher(16)); a `Threads 2` search must
           differ in nodes from `Threads 1` or the option is dead (B5).
G6  REPEAT a fixed-depth search twice in one process must NOT be assumed equal
           (go_repeatability.py: 50,541 -> 11,696). The gate asserts the DOCUMENTED
           order dependence so a future change that removes it is noticed, and so
           no one builds a pin on a number that is not stable.
G7  LEAF   a halfmove-99/98 position must score as the fifty-move rule says (B8).

Exit code 0 only if every check passes. The run is timed end to end.
"""
from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from uci_driver import Engine  # noqa: E402

from common import BUILD
EXE = sys.argv[1] if len(sys.argv) > 1 else str(BUILD)
PIN = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}
KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
DRAWN = "8/8/8/8/8/1R6/8/k1K5 w - - 100 1"
# Clock 97 with a mate in 2 available. This is the band findings §2 names: the leaf
# draw rule misses mates in H > 100 - p. A one-ply shift of that rule turns this
# root from `mate 2` into `cp 0`, so the check can fire on a score CLASS, not nodes.
LEAF97 = "7k/8/6K1/8/8/8/8/6Q1 w - - 97 1"


def gate(exe: str) -> dict:
    checks = []
    t0 = time.monotonic()

    def check(cid, name, ok, detail):
        checks.append({"id": cid, "name": name, "pass": bool(ok), "detail": detail})

    with Engine(exe) as e:
        e.uci()
        e.isready()

        # G1 -- the four pins, on stdin, through the real command loop.
        g1 = {}
        for d in (11, 13, 16):
            g1[f"bench{d}"] = e.bench(d)["nodes"]
        e.send("position startpos")
        e.isready()
        e.send("go perft 5")
        out, _ = e.read_until(lambda l: l.strip().startswith("nodes ") and l.split()[0] == "nodes", 600)
        perft = None
        for line in out:
            f = line.split()
            if len(f) == 2 and f[0] == "nodes" and f[1].isdigit():
                perft = int(f[1])
        g1["perft5"] = perft
        bad = {k: v for k, v in g1.items() if v != PIN[k]}
        check("G1", "four pins on stdin", not bad, {"got": g1, "expected": PIN, "mismatched": bad})

        # G6a -- order dependence of a bare fixed-depth search (before any clear).
        first = e.search(f"position fen {KIWIPETE}", "go depth 11")
        second = e.search(f"position fen {KIWIPETE}", "go depth 11")
        check("G6", "fixed-depth go is order-dependent in one session",
              first["nodes"] is not None and second["nodes"] is not None
              and first["nodes"] != second["nodes"],
              {"first": first["nodes"], "second": second["nodes"],
               "note": "if this ever becomes equal, re-measure before pinning go"})

        # G2 -- drawn root must be searched.
        e.send("ucinewgame"); e.isready(); e.send("setoption name Clear Hash"); e.isready()
        d = e.search(f"position fen {DRAWN}", "go depth 10")
        check("G2", "drawn root returns a searched move", d["nodes"] > 0 and d["info_depth_lines"] > 0,
              {"nodes": d["nodes"], "bestmove": d["bestmove"], "info_depth_lines": d["info_depth_lines"]})

        # G5 -- Threads option must be live.
        e.send("ucinewgame"); e.isready(); e.send("setoption name Clear Hash"); e.isready()
        e.setoption("Threads", 1)
        t1 = e.search(f"position fen {START}", "go depth 12")
        e.send("ucinewgame"); e.isready(); e.send("setoption name Threads value 2"); e.isready()
        e.send("setoption name Clear Hash"); e.isready()
        t2 = e.search(f"position fen {START}", "go depth 12")
        check("G5", "Threads 2 differs from Threads 1", t1["nodes"] != t2["nodes"],
              {"t1": t1["nodes"], "t2": t2["nodes"]})
        e.setoption("Threads", 1)

        # G3 -- the book path.
        e.send("ucinewgame"); e.isready(); e.send("setoption name Book Variety value 0"); e.isready()
        b = e.search(f"position fen {START}", "go movetime 100")
        check("G3", "book move emitted with no info depth",
              b["book_move_line"] is not None and b["info_depth_lines"] == 0,
              {"book_line": b["book_move_line"], "info_depth_lines": b["info_depth_lines"]})
        e.send("ucinewgame"); e.isready(); e.send("setoption name Book Variety value 30"); e.isready()

        # G4 -- the clock path.
        t_start = time.monotonic()
        # NOT startpos: the book answers startpos in 0.5 ms with zero info lines and
        # no score (C6/C22). A clock check on a booked position measures the book.
        c = e.search(f"position fen {KIWIPETE} moves e2a6", "go wtime 1000 btime 1000")
        wall = (time.monotonic() - t_start) * 1000
        # The node FLOOR is what makes this check able to fail. With Move Overhead
        # set above the clock the engine returns in 0.5 ms with one info line and
        # 60 nodes -- it "returns inside its clock" while searching nothing.
        check("G4", "clocked search returns inside its clock AND searched",
              c["saw_bestmove"] and c["info_depth_lines"] >= 3 and wall < 900
              and c["nodes"] is not None and c["nodes"] > 5000,
              {"wall_ms": round(wall, 1), "nodes": c["nodes"], "info_depth_lines": c["info_depth_lines"]})

        # G7 -- the fifty-move leaf.
        e.send("ucinewgame"); e.isready(); e.send("setoption name Clear Hash"); e.isready()
        lf = e.search(f"position fen {LEAF97}", "go depth 8")
        check("G7", "clock-97 root with mate in 2 still reports a mate",
              lf["last_info"] is not None and " mate " in (lf["last_info"] or ""),
              {"last_info": lf["last_info"]})

    elapsed = time.monotonic() - t0
    return {"exe": exe, "checks": checks, "all_pass": all(c["pass"] for c in checks),
            "wall_seconds": round(elapsed, 3)}


if __name__ == "__main__":
    r = gate(EXE)
    for c in r["checks"]:
        print(f"{c['id']} {'PASS' if c['pass'] else 'FAIL'}  {c['name']}")
        if not c["pass"]:
            print("      ", json.dumps(c["detail"], default=str)[:300])
    print(f"\nall_pass={r['all_pass']}  wall={r['wall_seconds']}s")
    print(json.dumps(r, indent=2, default=str))
    sys.exit(0 if r["all_pass"] else 1)
