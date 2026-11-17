#!/usr/bin/env python3
"""Test #1 from the brief: null-move pruning in a zugzwang-adjacent position.

Zugzwang is where null move is classically unsound: the side to move would
rather PASS, so "if I pass and still stand at least as well, my position is
good" is false -- the obligation to move is what ruins them. If the engine
trusts a null-move cutoff inside a position where every legal move loses, it
can return a non-losing score for a lost position, or the wrong mate distance.

What is measured, per fixture:

  * the true mate distance, from the oracle (and cross-checked by brute force);
  * the engine's mate score at each depth, with null move ON and ABLATED;
  * whether the null-move path actually FIRED (counter evidence). A null here
    whose counters are zero would be a null from a corpus that never reached the
    condition -- the kill condition the brief names.

The fixtures are built to be genuinely zugzwang-adjacent: the side to move has
legal moves, every one of them loses, and the position is quiet (no check), which
is exactly where a null-move search evaluates "pass" as a real option.
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, "scripts")
import chess  # noqa: E402
import mateoracle as mo  # noqa: E402
from ucidrv import Engine, check_fen  # noqa: E402


def brute_shortest(fen: str, maxp: int = 9) -> int:
    """Third, independent shortest-mate solver (explicit minimax, no memo)."""
    def ev(bd, k):
        if bd.is_checkmate():
            return True
        if bd.is_stalemate() or bd.is_insufficient_material():
            return False
        reps = list(bd.legal_moves)
        if not reps:
            return False
        for m in reps:
            bd.push(m)
            ok = cm(bd, k - 1)
            bd.pop()
            if not ok:
                return False
        return True

    def cm(bd, k):
        if bd.is_checkmate():
            return True
        if k < 1:
            return False
        for m in bd.legal_moves:
            bd.push(m)
            ok = ev(bd, k - 1)
            bd.pop()
            if ok:
                return True
        return False

    b = chess.Board(fen)
    for k in range(1, maxp + 1, 2):
        if cm(b, k):
            return k
    return 0


def all_moves_lose(board: chess.Board, plies_after: int) -> bool:
    """True when every legal move by the side to move hands the opponent a mate."""
    for m in board.legal_moves:
        board.push(m)
        # the opponent now mates within plies_after
        ok = mo._layered_attacker(board, plies_after)
        board.pop()
        if not ok:
            return False
    return True


# Fixtures where the LOSING side is to move and every move loses -- the
# zugzwang-adjacent shape. Each was chosen so the loser is QUIET (not in check):
# having to move, with no good move, is the condition null move mishandles.
ZUGZWANG_FIXTURES = [
    # Black to move, bare king in the corner, White Q+K. Black must step and mate follows.
    "7k/8/6K1/8/8/8/8/6Q1 b - - 0 1",
    # Black to move, K in corner, White R+K: the classic "must give way" shape.
    "7k/5K2/8/8/8/8/8/6R1 b - - 0 1",
    # Black to move, two rooks, ladder mate pending.
    "7k/8/8/8/8/8/6R1/6R1 b - - 0 1",
    # Black to move, KQ vs K with the king on the edge and no check.
    "k7/8/1K6/8/8/8/8/7Q b - - 0 1",
    # Black to move, only pawn moves left, all lose to mate.
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
]


def get_stats(engine: Engine) -> dict:
    engine.send("probestats")
    line = engine._read_until(lambda l: l.startswith("probestats"))[-1]
    return json.loads(line[len("probestats"):])


def probe(engine: Engine, fen: str, depth: int, arm: str) -> dict:
    engine.newgame()
    check_fen(engine, fen)
    engine.send(f"ablate {arm}")
    engine.isready()
    r = engine.go(f"depth {depth}")
    s = get_stats(engine)
    last = r.last
    return {"bestmove": r.bestmove,
            "score_mate": last.score_mate if last else None,
            "score_cp": last.score_cp if last else None,
            "nodes": r.nodes, "counts": s}


def main() -> int:
    depths = [int(x) for x in (sys.argv[1] if len(sys.argv) > 1 else "4,6,8,10,12").split(",")]
    engine = Engine("build/probe/forge", {"Threads": "1", "Hash": "64", "OwnBook": "false"})
    out = []
    try:
        for fen in ZUGZWANG_FIXTURES:
            board = chess.Board(fen)
            if not board.is_valid():
                out.append({"fen": fen, "error": "invalid"})
                continue
            # Ground truth: the side to move is LOSING, so the oracle reports what
            # the side to move can force (0 here) and we separately ask how fast
            # the OPPONENT mates, by flipping the side to move.
            flipped = chess.Board(fen)
            flipped.turn = not flipped.turn
            flipped.clear_stack()
            opp = mo.solve_negamax(flipped, 9) if flipped.is_valid() else 0
            opp_brute = brute_shortest(flipped.fen()) if flipped.is_valid() else 0
            every_loses = all_moves_lose(board, max(1, opp - 2)) if opp > 0 else False
            row = {
                "fen": fen,
                "side_to_move": "white" if board.turn == chess.WHITE else "black",
                "opponent_mates_in_plies": opp,
                "brute_opponent_mates_in_plies": opp_brute,
                "oracles_agree": opp == opp_brute,
                "every_legal_move_loses": every_loses,
                "in_check": board.is_check(),
                "legal_moves": board.legal_moves.count(),
                "by_depth": {},
            }
            for d in depths:
                on = probe(engine, fen, d, "none")
                off = probe(engine, fen, d, "null_move")
                row["by_depth"][d] = {
                    "null_on": on, "null_off": off,
                    "null_fired": on["counts"].get("null_try", 0),
                    "null_cutoff": on["counts"].get("null_cutoff", 0),
                    "verdict_changed_by_ablation":
                        (on["score_mate"], on["bestmove"]) != (off["score_mate"], off["bestmove"]),
                }
            out.append(row)
            print(f"{fen:38s} opp_mate_in={opp} (brute {opp_brute}) every_move_loses={every_loses}",
                  flush=True)
    finally:
        engine.close()

    with open("evidence/zugzwang.json", "w") as fh:
        json.dump(out, fh, indent=1)

    # Report: did null move fire at all, and did it change any verdict?
    fired = sum(1 for r in out for d in r.get("by_depth", {}).values() if d["null_fired"] > 0)
    changed = [(r["fen"], d, v["null_on"]["bestmove"], v["null_off"]["bestmove"])
               for r in out for d, v in r.get("by_depth", {}).items()
               if v["verdict_changed_by_ablation"]]
    print(json.dumps({
        "fixtures": len(out),
        "fixtures_with_every_move_losing": sum(1 for r in out if r.get("every_legal_move_loses")),
        "cells_where_null_move_fired": fired,
        "cells_where_ablation_changed_the_answer": len(changed),
        "changed": changed,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
