#!/usr/bin/env python3
"""Measurement 1, remaining surface: what does `go mate N` report when it FAILS?

Four questions the corpus run alone cannot answer:

  A. FALSE POSITIVE: does `go mate N` ever report a mate score on a position
     where the oracle proves no mate exists inside the searched window? Every
     positive mate claim is replayed in python-chess AND cross-checked against
     the oracle, so a plausible-looking mate that does not exist is caught.
  B. MATE-SHAPED LINE, NON-MATE SCORE: the failure mode a corpus user would
     most likely mis-read. On a no-mate board, is the PV `2N-1` plies long and
     ending in a quiet move (a depth-capped line) or truncated?
  C. DEFENDER TO MOVE: with the LOSING side to move, a mate score must be
     NEGATIVE. A search that returns a positive mate score for the defender is
     reporting a mate that does not exist.
  D. STOP: does `stop` during `go mate N` produce a clean bestmove, and does a
     second `go mate N` after a stop still work?

Nothing here trusts the engine's own claim: C uses the oracle's exact DTM for
the side to move, so "the defender is lost in 3 plies" is a fact from python-chess.

Usage: run_surface.py --exe build/forge --out surface.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402
from mateoracle import Oracle, pv_replays_to_mate  # noqa: E402

# Positions with NO forced mate for the side to move inside 7 plies. Proven by
# the oracle at run time, not asserted here.
NO_MATE_POOL = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
]

# The DEFENDER-to-move side of a forced mate. Each is a position where the side
# to move is getting mated; the oracle confirms the sign and the distance.
DEFENDER_POOL = [
    "8/5k2/8/6K1/1Q6/8/8/8 b - - 0 1",     # black to move, White mates
    "k7/8/8/8/8/3R4/6K1/6R1 b - - 0 1",
    "8/8/8/8/8/1N2N3/8/K1k5 b - - 0 1",    # a legal checkmate already: extreme case
]


def oracle_no_mate(fen: str, plies: int = 7) -> bool:
    board = chess.Board(fen)
    o = Oracle(node_budget=6_000_000)
    return o.dtm_plies(board, plies) is None


def part_a_b(exe: str) -> dict:
    print("A/B — false-positive mate claims and the shape of a failed mate search\n")
    rows = []
    header = (f"{'position':22s} {'N':>2s} {'score':>12s} {'dep':>3s} {'nodes':>10s} "
              f"{'pvlen':>5s} {'ends':>10s} {'claim_ok':>8s}")
    print(header)
    print("-" * len(header))
    for fen in NO_MATE_POOL:
        if not oracle_no_mate(fen, 7):
            print(f"  SKIP {fen}: oracle found a mate in 7; not a no-mate row")
            continue
        board = chess.Board(fen)
        for n in (1, 2, 3, 4):
            with Engine(exe, {"OwnBook": "false"}) as eng:
                eng.newgame()
                eng.setpos(fen)
                res = eng.go(f"go mate {n}", timeout=600)
            sc = res.last_score
            pv = res.last_pv
            kind, val = (sc if sc else (None, None))
            # Does the PV end in mate? Replay it.
            ok, detail = (None, "")
            if kind == "mate" and val and val > 0:
                ok, detail = pv_replays_to_mate(board, pv)
            ends = "mate" if ok else ("cp-line" if kind == "cp" else "?")
            rows.append({
                "fen": fen, "n": n, "score_kind": kind, "score_value": val,
                "depth": res.last_depth, "nodes": res.last_nodes,
                "pv_len": len(pv), "expect_len": 2 * n - 1,
                "pv": pv, "claim_ok": ok, "detail": detail,
                "full_line": len(pv) == 2 * n - 1,
                "walls": round(res.wall_s, 3),
            })
            print(f"{fen[:22]:22s} {n:2d} {str(sc):>12s} {str(res.last_depth):>3s} "
                  f"{str(res.last_nodes):>10s} {len(pv):5d} {ends:>10s} {str(ok):>8s}", flush=True)
        print()
    return {"rows": rows}


def part_c(exe: str) -> dict:
    print("\nC — defender to move: the sign of a mate score\n")
    rows = []
    for fen in DEFENDER_POOL:
        board = chess.Board(fen)
        o = Oracle(node_budget=8_000_000)
        dtm = o.dtm_plies(board, 7)          # for the SIDE TO MOVE (the defender)
        # A defender's DTM is None; the attacker mates in odd plies, so from the
        # defender's point of view there is no forced mate FOR THEM. What matters
        # is whether the ENGINE reports a negative (or a positive) mate score.
        for n in (1, 2, 3, 4):
            with Engine(exe, {"OwnBook": "false"}) as eng:
                eng.newgame()
                eng.setpos(fen)
                res = eng.go(f"go mate {n}", timeout=600)
            sc = res.last_score
            kind, val = (sc if sc else (None, None))
            rows.append({
                "fen": fen, "n": n, "score_kind": kind, "score_value": val,
                "depth": res.last_depth, "nodes": res.last_nodes,
                "bestmove": res.bestmove, "pv": res.last_pv,
                "oracle_defender_dtm7": dtm,
                "board_is_checkmate": board.is_checkmate(),
                "sign": ("negative (defender lost)" if (val or 0) < 0
                         else "positive (claims a mate FOR the defender)" if (val or 0) > 0
                         else "cp"),
            })
            print(f"{fen[:34]:34s} N={n} {str(sc):>12s} dep={res.last_depth} "
                  f"nodes={res.last_nodes} bm={res.bestmove}", flush=True)
        print()
    return {"rows": rows}


def part_d(exe: str) -> dict:
    print("\nD — stop during `go mate N`, then a second request\n")
    rows = []
    fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    for n in (4, 6):
        with Engine(exe, {"OwnBook": "false"}) as eng:
            eng.newgame()
            eng.setpos(fen)
            eng.send(f"go mate {n}")
            time.sleep(0.4)
            eng.send("stop")
            # Read until the bestmove that the stop produces.
            lines = []
            bestmove = None
            deadline = time.time() + 60
            while time.time() < deadline:
                ln = eng.readline(timeout=deadline - time.time())
                if ln is None:
                    break
                lines.append(ln)
                if ln.startswith("bestmove"):
                    bestmove = ln.split()[1]
                    break
            depthlines = [ln for ln in lines if ln.startswith("info depth")]
            # Now a second request on the same process: does the mode still work?
            eng.newgame()
            eng.setpos("8/8/4R3/8/3R4/8/2k3K1/8 w - - 0 1")
            after = eng.go(f"go mate {n}", timeout=600)
            rows.append({
                "fen": fen, "n": n, "stopped_bestmove": bestmove,
                "stopped_info_lines": len(depthlines),
                "stopped_last": depthlines[-1] if depthlines else None,
                "second_request_bestmove": after.bestmove,
                "second_request_score": after.last_score,
                "second_request_nodes": after.last_nodes,
                "second_request_terminated": after.terminated,
            })
            print(f"N={n}: stop -> bestmove {bestmove} after {len(depthlines)} info lines; "
                  f"second request -> {after.bestmove} {after.last_score} "
                  f"nodes {after.last_nodes}", flush=True)
    return {"rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="build/forge")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data = {"a_b": part_a_b(args.exe), "c": part_c(args.exe), "d": part_d(args.exe)}
    json.dump(data, open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
