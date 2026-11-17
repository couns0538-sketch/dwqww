#!/usr/bin/env python3
"""Prove and characterise the mate-distance overclaim found in run_edges.

A `go mate 4` request reported `mate 6` on a position whose exact DTM is 5 moves
(9 plies). Two things must be separated, and they are different defects:

  1. IS THE DISTANCE WRONG? `mate 6` on a mate-in-5 is wrong by one move.
  2. IS THE MOVE STILL WINNING? h7h2 may still force the mate, just reported with
     the wrong distance. If the move is the right move, this is a DISTANCE defect
     only; if the move also fails to force, it is a MOVE defect.

The oracle settles both. It also settles a third question the finding needs:
does the overclaim disappear with a bigger N (`go mate 5` reports mate 5), which
makes it a bound-at-the-edge phenomenon rather than a general one.

Every claim here is checked against python-chess, and the verifier is itself
checked: the "force" test is a full minimax over replies, not a replay of the
engine's own line.

Usage: run_overclaim.py --exe build/forge --out overclaim.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402
from mateoracle import Oracle, pv_replays_to_mate  # noqa: E402

FEN = "8/7Q/8/8/K7/8/8/5k2 w - - 0 1"


def forced_mate_from_move(board: chess.Board, uci: str, plies: int) -> tuple[bool, int | None]:
    """Does this MOVE force mate within `plies`? Oracle answer, not engine replay."""
    mv = chess.Move.from_uci(uci)
    if mv not in board.legal_moves:
        return False, None
    b = board.copy()
    b.push(mv)
    if b.is_checkmate():
        return True, 1
    o = Oracle(node_budget=20_000_000)
    inner = o._loses_in(b, plies - 1)
    if inner is None:
        return False, None
    return True, inner + 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="build/forge")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    board = chess.Board(FEN)
    out = {"fen": FEN, "runs": []}

    o = Oracle(node_budget=30_000_000)
    exact = o.exact_dtm_up_to(board, 6)
    print(f"FEN {FEN}")
    print(f"oracle exact DTM: {exact} plies = {(exact + 1)//2} moves")
    out["oracle_exact_dtm_plies"] = exact
    out["oracle_exact_dtm_moves"] = (exact + 1) // 2

    for n in (1, 2, 3, 4, 5, 6):
        with Engine(args.exe, {"OwnBook": "false"}) as eng:
            eng.newgame()
            eng.setpos(FEN)
            res = eng.go(f"go mate {n}", timeout=600)
        sc = res.last_score or (None, None)
        kind, val = sc
        replay_ok, replay_detail = (None, "")
        if kind == "mate" and val and val > 0:
            replay_ok, replay_detail = pv_replays_to_mate(board, res.last_pv)
        force_ok = force_plies = None
        if res.bestmove and res.bestmove != "0000":
            force_ok, force_plies = forced_mate_from_move(board, res.bestmove, 2 * n + 3)
        overclaims = (kind == "mate" and val is not None and val > n)
        wrong_distance = (kind == "mate" and val is not None
                          and (val + 1) * 1 != exact)
        rec = {
            "n": n, "score_kind": kind, "score_value": val,
            "depth": res.last_depth, "nodes": res.last_nodes,
            "bestmove": res.bestmove, "pv": res.last_pv, "pv_len": len(res.last_pv),
            "pv_replays_to_mate": replay_ok, "pv_detail": replay_detail,
            "move_forces_mate_within_window": force_ok,
            "move_forces_mate_plies": force_plies,
            "overclaims_beyond_n": overclaims,
            "distance_equals_truth": (not wrong_distance) if kind == "mate" else None,
        }
        out["runs"].append(rec)
        print(f"  go mate {n}: {kind}{val} dep={res.last_depth} nodes={res.last_nodes} "
              f"bm={res.bestmove} pvlen={len(res.last_pv)} "
              f"pvreplay={replay_ok} moveforce={force_ok}/{force_plies} "
              f"overclaim={overclaims}", flush=True)

    json.dump(out, open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")

    bad = [r for r in out["runs"] if r["overclaims_beyond_n"]]
    print(f"\nVERDICT: {len(bad)} of {len(out['runs'])} requests overclaim a distance beyond N.")
    for r in bad:
        print(f"  go mate {r['n']} -> mate {r['score_value']} (N={r['n']}) on a "
              f"mate-in-{out['oracle_exact_dtm_moves']}; PV replays to mate: "
              f"{r['pv_replays_to_mate']}; move forces in "
              f"{r['move_forces_mate_plies']} plies: {r['move_forces_mate_within_window']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
