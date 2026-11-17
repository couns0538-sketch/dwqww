#!/usr/bin/env python3
"""How much of the engine does a bench pin exercise, and what can it NOT see?

Answers the question by coverage, not by argument. Three workloads on the same
instrumented build:
  bench      : exactly what `bench 13` runs (8 FENs, depth 13, clear() between)
  engine_wide: a workload built to reach every reachable path -- book, clock,
               drawn root, book off, fixed depth, a mate, the fifty-move band
  empty      : uci + isready only, the floor

The comparison is `bench` vs `engine_wide`: any function or line the wide set reaches
and bench does not is a place a bench pin cannot detect a change. The reverse
(what only bench reaches) is not interesting for a gate.

Run with cov/ built at --coverage. Writes JSON with per-file and per-function detail.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

from common import COV as _COV
COV = str(_COV)
WORK = {}


def workload(name: str, cmds: list[str]) -> pathlib.Path:
    p = pathlib.Path(__file__).resolve().parent / f"cmd_{name}.txt"
    p.write_text("\n".join(cmds) + "\n")
    return p


BOOKED = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
DRAWN = "8/8/8/8/8/1R6/8/k1K5 w - - 100 1"
MATE = "7k/8/6K1/8/8/8/8/6Q1 w - - 97 1"
ENDGAME = "6k1/5p1p/8/8/8/8/5P1P/3R2K1 b - - 98 1"
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"

CMDS = {
    "bench": ["uci", "isready", "bench 13", "quit"],
    "empty": ["uci", "isready", "quit"],
    "pins_only": ["uci", "isready", "bench 11", "bench 13", "position startpos", "go perft 5", "quit"],
    "combined": ["uci", "isready", "bench 11", "bench 13",
                 "position startpos", "go perft 5",
                 "ucinewgame", "isready", "setoption name Book Variety value 0", "isready",
                 f"position fen {BOOKED}", "go movetime 100",
                 "setoption name OwnBook value false", "isready", "ucinewgame", "isready",
                 f"position fen {BOOKED}", "go depth 10",
                 f"position fen {DRAWN}", "go depth 10",
                 f"position fen {MATE}", "go depth 8",
                 f"position fen {ENDGAME} moves e7e8q", "go depth 8",
                 f"position fen {KIWI} moves e2a6", "go wtime 1000 btime 1000",
                 "ucinewgame", "isready", "setoption name Threads value 2", "isready",
                 "setoption name Clear Hash", "isready", f"position fen {KIWI}", "go depth 12",
                 "setoption name Threads value 1", "isready",
                 "ucinewgame", "isready", "setoption name MultiPV value 2", "isready",
                 f"position fen {KIWI}", "go depth 10",
                 "setoption name MultiPV value 1", "isready",
                 "quit"],
    "engine_wide": [
        "uci", "isready",
        "ucinewgame", "isready",
        # book path, RNG pinned so the answer is not clock noise
        "setoption name Book Variety value 0", "isready",
        f"position fen {BOOKED}", "go movetime 100",
        # book disabled, so the same position reaches search
        "setoption name OwnBook value false", "isready",
        "ucinewgame", "isready",
        f"position fen {BOOKED}", "go depth 10",
        # drawn root
        "position fen " + DRAWN, "go depth 10",
        # mate band
        "position fen " + MATE, "go depth 8",
        # fifty-move leaf
        "position fen " + ENDGAME + " moves e7e8q", "go depth 8",
        # clocked search
        "position fen " + KIWI + " moves e2a6", "go wtime 1000 btime 1000",
        # threaded search, to reach the helper path
        "ucinewgame", "isready", "setoption name Threads value 2", "isready",
        "setoption name Clear Hash", "isready",
        f"position fen {KIWI}", "go depth 12",
        "setoption name Threads value 1", "isready",
        # multipv, to reach the alternate-table path
        "ucinewgame", "isready", "setoption name MultiPV value 2", "isready",
        f"position fen {KIWI}", "go depth 10",
        "setoption name MultiPV value 1", "isready",
        # perft, node budget, infinite+stop
        "position startpos", "go perft 4",
        "ucinewgame", "isready", f"position fen {KIWI}", "go nodes 200000",
        "ucinewgame", "isready", "position startpos",
        "go infinite", "stop", "isready",
        "quit",
    ],
}


def run(name: str) -> dict:
    path = workload(name, CMDS[name])
    out = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve().parent / "coverage.py"), COV, name, str(path)],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


if __name__ == "__main__":
    result = {name: run(name) for name in CMDS}
    summary = {}
    for name, r in result.items():
        tot = sum(f["lines"] for f in r["files"].values())
        hit = sum(f["lines_hit"] for f in r["files"].values())
        fns = sum(f["functions"] for f in r["files"].values())
        fhit = sum(f["functions_called"] for f in r["files"].values())
        summary[name] = {"lines_hit": hit, "lines": tot, "line_pct": round(100 * hit / tot, 1),
                         "functions_called": fhit, "functions": fns,
                         "function_pct": round(100 * fhit / fns, 1)}

    bench_fns = set()
    wide_fns = set()
    for fname, f in result["bench"]["files"].items():
        # a function is "reached" if it appears but is not in the never-called list
        for name in f["functions_never_called"]:
            pass
    # Reconstruct reached sets from the counts per file is not possible; instead run a
    # per-file diff using the never-called lists.

    unreachable_by_bench = {}
    for fname, wf in result["combined"]["files"].items():
        bf = result["bench"]["files"].get(fname)
        if not bf:
            continue
        reached_by_wide = set(wf["functions_never_called"])
        # functions wide never called are irrelevant; what matters is wide-called but
        # bench-never-called: those names are in bf's never-called list AND absent from
        # wf's never-called list.
        bench_missing = [n for n in bf["functions_never_called"] if n not in reached_by_wide]
        unreachable_by_bench[fname] = bench_missing

    print(json.dumps({"summary": summary,
                      "bench_blind_functions": unreachable_by_bench,
                      "blind_function_count": sum(len(v) for v in unreachable_by_bench.values())},
                     indent=2))
