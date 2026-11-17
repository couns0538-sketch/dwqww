#!/usr/bin/env python3
"""corpus_endgame.py — the same differential, on roots that ARE claimable.

corpus_diff.py over ordinary self-play found 0 claimable roots in 240 positions, so it
establishes only that the fix is inert on ordinary boards. This sweep starts from endgames
with the fifty-move counter already high, so the claimable arm is actually exercised, and
pairs every differing root with an assertion that it really was claimable.

Every root is classified with python-chess (not with the engine), and the classification is
what decides whether a difference is explained.

Usage: corpus_endgame.py A_EXE B_EXE
"""
import json
import sys

import chess

sys.path.insert(0, "/home/ubuntu/work")
from corpus_diff import Engine  # noqa: E402

# endgames with enough material to keep playing, and clocks placed so the rule decides
SEEDS = [
    ("KQvKR", "4k3/8/8/8/8/8/8/Q3K2r w - - 92 1"),
    ("KRvKR", "4k3/8/8/8/8/8/8/R3K2r w - - 92 1"),
    ("KQvK", "4k3/8/8/8/8/8/8/Q3K3 w - - 92 1"),
    ("KRvK", "4k3/8/8/8/8/8/8/R3K3 w - - 92 1"),
    ("KQvKPawns", "4k3/pp6/8/8/8/8/8/Q3K3 w - - 90 1"),
    ("KRvKP", "4k3/p7/8/8/8/8/8/R3K3 w - - 90 1"),
    ("KBNvK", "4k3/8/8/8/8/8/8/BN2K3 w - - 88 1"),
    ("KQvKnight", "4k3/8/8/8/8/8/8/Q2nK3 w - - 90 1"),
]

DEPTH = 8
MAX_PLIES = 24


def classify(b):
    resets = [m.uci() for m in b.legal_moves
              if (b.piece_at(m.from_square)
                  and b.piece_at(m.from_square).piece_type == chess.PAWN)
              or b.is_capture(m)]
    mates = []
    for m in b.legal_moves:
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            mates.append(m.uci())
    return {"halfmove": b.halfmove_clock, "claimable": b.halfmove_clock >= 100,
            "resets": len(resets), "mates": mates,
            "insufficient": b.is_insufficient_material()}


def main():
    a = Engine(sys.argv[1])
    b_eng = Engine(sys.argv[2])
    rows = []
    try:
        for name, fen in SEEDS:
            board = chess.Board(fen)
            moves = []
            for ply in range(MAX_PLIES):
                if board.is_game_over(claim_draw=True):
                    break
                pos = f"position fen {fen}" + ((" moves " + " ".join(moves)) if moves else "")
                ra = a.search(pos, DEPTH)
                rb = b_eng.search(pos, DEPTH)
                info = classify(board)
                differs = (ra["bestmove"] != rb["bestmove"] or ra["score"] != rb["score"]
                           or ra["nodes"] != rb["nodes"])
                rows.append({"seed": name, "ply": ply, "fen": board.fen(),
                             "moves": list(moves), **info,
                             "a": ra, "b": rb, "differs": differs,
                             # a difference is explained only when the rule could have fired:
                             # claimable, at least one reset available, and no mate on the board
                             "explained": bool(info["claimable"] and info["resets"] > 0
                                               and not info["mates"])})
                if ra["bestmove"] in (None, "0000", "(none)"):
                    break
                try:
                    board.push_uci(ra["bestmove"])
                except ValueError:
                    break
                moves.append(ra["bestmove"])
    finally:
        a.quit()
        b_eng.quit()

    diff = [r for r in rows if r["differs"]]
    unexplained = [r for r in diff if not r["explained"]]
    claimable = [r for r in rows if r["claimable"]]
    summary = {
        "positions": len(rows),
        "claimable_roots": len(claimable),
        "claimable_with_reset": len([r for r in claimable if r["resets"] > 0]),
        "differing": len(diff),
        "differing_and_claimable": len([r for r in diff if r["claimable"]]),
        "UNEXPLAINED_DIFF": len(unexplained),
        "unexplained": unexplained[:5],
        "differing": [r for r in diff][:12],
    }
    json.dump({"summary": summary, "rows": rows},
              open("/home/ubuntu/work/ev/corpus_endgame.json", "w"), indent=2)
    print(json.dumps(summary, indent=2))
    return 0 if not unexplained else 1


if __name__ == "__main__":
    sys.exit(main())
