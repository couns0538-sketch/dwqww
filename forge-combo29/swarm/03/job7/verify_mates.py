#!/usr/bin/env python3
"""verify_mates.py OUTFILE : verify or refute each mate claim used in the job-7 adjudication, with python-chess.

Clean exact formulation. Define:

    winning(board, plies)  -- True iff the side to move can FORCE checkmate in at most `plies` plies.
    losing(board, plies)   -- True iff the side to move is LOST: whatever it plays, the opponent forces mate
                              within `plies` plies.

    winning(b, p) = exists move: (b.push -> if checkmate: True
                                            else losing(b, p-1))
    losing(b, p)  = for all moves: (b.push -> if not checkmate: winning(b, p-1))     [p must be > 0]

`mate N` for the side to move means winning(pos, 2N-1). `mate -N` means losing(pos, 2N-1).

Both are memoised on (fen, plies) so the searches stay finite.
"""
import functools
import sys

import chess

OUT = sys.argv[1]
FENS = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/03/job4/set_bm200.fens") if l.strip()]

CLAIMS = [
    (153, "a4b4", "cp -1284"),
    (153, "a4b5", "cp -1074"),
    (155, "c6d6", "cp -1145"),
    (155, "c6c7", "mate -14"),
    (156, "g5h3", "mate 16"),
    (156, "f2e3", "mate 6"),
    (160, "f1e2", "mate 6"),
    (160, "f1f2", "mate 5"),
]


@functools.lru_cache(maxsize=None)
def winning(fen, plies):
    if plies <= 0:
        return False
    b = chess.Board(fen)
    for mv in b.legal_moves:
        b.push(mv)
        if b.is_checkmate():
            b.pop()
            return True
        nxt = b.fen()
        b.pop()
        if losing(nxt, plies - 1):
            return True
    return False


@functools.lru_cache(maxsize=None)
def losing(fen, plies):
    """side to move is lost: every legal move allows a forced mate within `plies`."""
    if plies <= 0:
        return False
    b = chess.Board(fen)
    moves = list(b.legal_moves)
    if not moves:
        return b.is_checkmate()
    for mv in moves:
        b.push(mv)
        mate_now = b.is_checkmate()
        nxt = b.fen()
        b.pop()
        if mate_now:
            continue                      # this move loses immediately, as required
        if not winning(nxt, plies - 1):
            return False                  # a move that escapes -> not lost
    return True


lines = ["| idx | move | engine claim | python-chess verdict |", "|---|---|---|---|"]
for idx, mv, claim in CLAIMS:
    b = chess.Board(FENS[idx])
    if mv not in [m.uci() for m in b.legal_moves]:
        lines.append(f"| {idx} | {mv} | {claim} | MOVE ILLEGAL at this root — cannot assess |")
        print(lines[-1], flush=True)
        continue
    if claim.startswith("mate"):
        n = int(claim.split()[1])
        plies = 2 * abs(n) - 1
        b.push_uci(mv)
        after = b.fen()
        if n > 0:
            # mover claims to win: the OPPONENT (now to move) must be lost within plies-1
            verdict = f"opponent LOST within {plies-1} plies: {losing(after, plies-1)}"
        else:
            # mover claims to BE mated: the opponent (now to move) must win
            verdict = f"opponent WINS within {plies-1} plies: {winning(after, plies-1)}"
    else:
        verdict = "cp score, not a mate claim — no mate verification applicable"
    lines.append(f"| {idx} | {mv} | {claim} | {verdict} |")
    print(lines[-1], flush=True)

open(OUT, "w").write("\n".join(lines) + "\n")
