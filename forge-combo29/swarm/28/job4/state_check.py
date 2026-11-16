#!/usr/bin/env python3
"""state_check.py EXE — seat 10's rule, tested on the quantity my clock claims use.

Seat 10 reports that in ONE process, two identical unrestricted searches with nothing between them give
56,720 then 4,951 then 4,516 nodes, while three separate processes give 56,720 each; and that
`ucinewgame` restores cold exactly but `Clear Hash` does not.

My clock tables report WALL time and LAST COMPLETED DEPTH. Those would move if a later search inherited
a warm table: a warm search needs fewer nodes for the same depth, so it finishes the iteration sooner and
may reach one depth deeper inside the same time budget. So this script measures exactly that, for my
three state regimes, on the same position, with `go movetime 100`:

  A) three fresh PROCESSES, one search each                    (cold by construction)
  B) one process, `ucinewgame` + `isready` before each search  (what all my harnesses do)
  C) one process, nothing between searches                     (the case seat 10 warns about)
  D) one process, `Clear Hash` before each search              (seat 10 says this is NOT cold)

For each regime: 5 searches, the wall ms, the last completed depth, and the node count. If B == A on all
three and C differs, my harnesses are sound and I say so in the report. If B != A, every clock table of
mine needs a re-run and I must say that instead.

Usage: state_check.py EXE
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

FEN = "r1bqk2r/p1ppbppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"
GO = "go movetime 100"
N = 5


def one_search(eng):
    t0 = time.monotonic()
    eng.send(GO)
    out, ok = eng.read_until("bestmove", 60)
    t1 = time.monotonic()
    depth, nodes = 0, 0
    for line in out:
        if line.startswith("info depth"):
            f = line.split()
            depth = max(depth, int(f[f.index("depth") + 1]))
            if "nodes" in f:
                nodes = int(f[f.index("nodes") + 1])
    return (t1 - t0) * 1000.0, depth, nodes, ok


def setup(exe):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("OwnBook", "false"), ("Threads", 1), ("Hash", 16)]:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        eng.read_until("readyok", 20)
    eng.send(f"position fen {FEN}")
    eng.send("isready")
    eng.read_until("readyok", 20)
    return eng


def main() -> int:
    exe = sys.argv[1]
    results = {}

    # A: fresh process per search
    a = []
    for _ in range(N):
        eng = setup(exe)
        a.append(one_search(eng))
        eng.close()
    results["A fresh process each"] = a

    # B: one process, ucinewgame before each
    eng = setup(exe)
    b = []
    for _ in range(N):
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {FEN}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        b.append(one_search(eng))
    eng.close()
    results["B one process, ucinewgame"] = b

    # C: one process, nothing between
    eng = setup(exe)
    c = [one_search(eng) for _ in range(N)]
    eng.close()
    results["C one process, nothing between"] = c

    # D: one process, Clear Hash before each
    eng = setup(exe)
    d = []
    for _ in range(N):
        eng.send("setoption name Clear Hash")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {FEN}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        d.append(one_search(eng))
    eng.close()
    results["D one process, Clear Hash"] = d

    print(f"position: {FEN}")
    print(f"go line: {GO}, {N} searches per regime, Threads 1, Hash 16, OwnBook false")
    print()
    print("| regime | wall ms per search | last completed depth | nodes |")
    print("|---|---|---|---|")
    for name, rows in results.items():
        walls = " ".join(f"{w:.1f}" for w, _d, _n, _o in rows)
        depths = " ".join(str(d) for _w, d, _n, _o in rows)
        nodes = " ".join(str(n) for _w, _d, n, _o in rows)
        print(f"| {name} | {walls} | {depths} | {nodes} |")

    aw = [w for w, _d, _n, _o in results["A fresh process each"]]
    bw = [w for w, _d, _n, _o in results["B one process, ucinewgame"]]
    ad = [d for _w, d, _n, _o in results["A fresh process each"]]
    bd = [d for _w, d, _n, _o in results["B one process, ucinewgame"]]
    print()
    print(f"A vs B: wall medians {sorted(aw)[N//2]:.1f} vs {sorted(bw)[N//2]:.1f} ms; "
          f"depths {ad} vs {bd}")
    print(f"depth sequences identical: {ad == bd}")
    print(f"node sequences identical: "
          f"{[n for _w, _d, n, _o in results['A fresh process each']] == [n for _w, _d, n, _o in results['B one process, ucinewgame']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
