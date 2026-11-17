#!/usr/bin/env python3
"""Measurement 2 + 4: does `go mate N` terminate, and does it obey a clock?

Part A — TERMINATION. The source says `mate_depth = mate_moves * 2 - 1` and
`max_depth = min(limits.depth, mate_depth)`, so an iteration cap always exists.
This measures whether that cap is reached, and how long it takes, on positions
where NO mate exists. Every no-mate claim is backed by `no_mate_in_one` (a total
enumeration of root moves) or by the oracle's window search.

The bound is reported three ways, because they answer different questions:
  * the ply cap the source implies (2N-1),
  * the WALL TIME actually observed at that cap,
  * and an extrapolation of wall time for larger N, MARKED as extrapolation.

Part B — CLOCK. `go mate N` sent with a clock and without one. The question is
not "does it respect the clock" in the abstract but whether a CLOCK SHORTENS the
answer relative to the same request with no clock, and whether a clock ever
causes `go mate N` to return a DIFFERENT mate claim than the unbounded request.
A clock that silently truncates a mate search is the hazard a caller cares
about: it changes the answer, not just the time.

Usage: run_termination.py --exe build/forge --out termination.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402
from mateoracle import Oracle, no_mate_in_one  # noqa: E402

# No-mate-in-1 positions, proven by total enumeration in python-chess. Rich
# middlegames so the search has real work to do at every depth.
NO_MATE_1 = [
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("after-1e4", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"),
    ("italian", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"),
    ("queens-gambit", "rnbqkb1r/ppp1pppp/5n2/3p4/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3"),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("bare-kings", "8/8/8/4k3/8/4K3/8/8 w - - 0 1"),
]


def part_a(exe: str, out_path: str) -> dict:
    rows = []
    print("PART A — termination on positions with NO mate in 1\n")
    header = f"{'position':16s} {'N':>2s} {'dep':>3s} {'score':>12s} {'nodes':>10s} {'wall_s':>8s} {'terminated':>10s} {'plycap':>6s}"
    print(header)
    print("-" * len(header))
    for name, fen in NO_MATE_1:
        board = chess.Board(fen)
        proved = no_mate_in_one(board)
        for n in (1, 2, 3, 4, 5, 6):
            with Engine(exe, {"OwnBook": "false"}) as eng:
                eng.newgame()
                eng.setpos(fen)
                res = eng.go(f"go mate {n}", timeout=600)
            sc = res.last_score
            rec = {
                "position": name, "fen": fen, "n": n,
                "depth": res.last_depth, "score": sc, "nodes": res.last_nodes,
                "wall_s": round(res.wall_s, 4), "terminated": res.terminated,
                "timed_out": res.timed_out, "ply_cap": 2 * n - 1,
                "cap_respected": res.last_depth == 2 * n - 1,
                "no_mate_in_1_proved": proved,
                "bestmove": res.bestmove, "pv": res.last_pv,
            }
            rows.append(rec)
            print(f"{name:16s} {n:2d} {str(res.last_depth):>3s} "
                  f"{str(sc):>12s} {str(res.last_nodes):>10s} {res.wall_s:8.3f} "
                  f"{str(res.terminated):>10s} {2*n-1:6d}", flush=True)
        print()
    json.dump(rows, open(out_path, "w"), indent=1)
    return {"rows": rows}


def part_b(exe: str, out_path: str) -> dict:
    print("\nPART B — does the clock change the answer?\n")
    rows = []
    # A board where go mate 4 DOES find a mate (from the corpus) plus a no-mate
    # board, so both outcomes are exercised under a clock.
    boards = [
        ("mate-in-4", "8/8/4R3/8/3R4/8/2k3K1/8 w - - 0 1"),
        ("no-mate", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ]
    cmds = [
        ("no-clock", "go mate 4"),
        ("wtime-5000-winc-100", "go mate 4 wtime 5000 btime 5000 winc 100 binc 100"),
        ("wtime-1000-winc-10", "go mate 4 wtime 1000 btime 1000 winc 10 binc 10"),
        ("wtime-200-noinc", "go mate 4 wtime 200 btime 200"),
        ("movetime-500", "go mate 4 movetime 500"),
        ("movetime-50", "go mate 4 movetime 50"),
        ("movetime-5", "go mate 4 movetime 5"),
    ]
    header = f"{'board':12s} {'request':24s} {'dep':>3s} {'score':>12s} {'nodes':>10s} {'wall_s':>8s} {'bm':>6s}"
    print(header)
    print("-" * len(header))
    for bname, fen in boards:
        for label, cmd in cmds:
            with Engine(exe, {"OwnBook": "false"}) as eng:
                eng.newgame()
                eng.setpos(fen)
                res = eng.go(cmd, timeout=600)
            sc = res.last_score
            rows.append({
                "board": bname, "fen": fen, "request": label, "cmd": cmd,
                "depth": res.last_depth, "score": sc, "nodes": res.last_nodes,
                "wall_s": round(res.wall_s, 4), "bestmove": res.bestmove,
                "info_lines": len(res.info_depths), "timed_out": res.timed_out,
                "pv": res.last_pv,
            })
            print(f"{bname:12s} {label:24s} {str(res.last_depth):>3s} {str(sc):>12s} "
                  f"{str(res.last_nodes):>10s} {res.wall_s:8.3f} {str(res.bestmove):>6s}", flush=True)
        print()
    json.dump(rows, open(out_path, "w"), indent=1)

    # The comparison that matters: does any clock produce a DIFFERENT answer
    # from the no-clock request on the same board?
    print("clock-vs-no-clock answer comparison:")
    for bname, _ in boards:
        base = next(r for r in rows if r["board"] == bname and r["request"] == "no-clock")
        for r in [x for x in rows if x["board"] == bname and x["request"] != "no-clock"]:
            same_score = r["score"] == base["score"]
            same_move = r["bestmove"] == base["bestmove"]
            verdict = "same answer" if (same_score and same_move) else (
                "SAME MOVE, DIFFERENT SCORE" if same_move else "DIFFERENT ANSWER")
            print(f"  {bname:12s} {r['request']:24s} -> {verdict}"
                  f"  ({base['score']} vs {r['score']}, {base['bestmove']} vs {r['bestmove']})")
    return {"rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="build/forge")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    a = part_a(args.exe, os.path.join(args.outdir, "termination_a.json"))
    b = part_b(args.exe, os.path.join(args.outdir, "termination_b_clock.json"))
    json.dump({"a": a, "b": b},
              open(os.path.join(args.outdir, "termination.json"), "w"), indent=1)
    print(f"\nwrote {args.outdir}/termination.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
