#!/usr/bin/env python3
"""plant_19f54.py OUTDIR : the missing plant for 19-F54's "0 of 40".

19-F54 reported that of 40 lone-king positions the engine's move produced a worse RESULT than an available
alternative in **0** cases. Under Rule 1 that zero is not shown, because the harness has never been shown a case
it is REQUIRED to flag.

The sample's one mate-bearing position does not serve as a plant: the engine *played* the mate, so it exercised
the "no defect" path. A plant must be a case where the harness must return DEFECT.

How to plant it without touching the engine: substitute a **fake mover** that returns a deliberately bad move
(a legal non-mating move in a position where another move mates at once), and run the SAME scoring logic over it.
If the harness reports 0 on the fake mover too, the harness cannot detect a defect and 19-F54's zero means
nothing.

This script therefore tests the scoring function twice:
  REAL  : the engine's own move on the mate-bearing board — expect NO defect
  PLANT : a move chosen to be non-mating where a mate exists — MUST report a defect
"""
import os
import sys

import chess

outdir = sys.argv[1]
os.makedirs(outdir, exist_ok=True)

WIN, DRAW, UNKNOWN = 2, 1, 0
H = (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)


def status_after(board, move):
    b = board.copy()
    b.push(move)
    if b.is_checkmate():
        return WIN
    if b.is_insufficient_material() or b.is_game_over():
        return DRAW
    return UNKNOWN


def defect(board, move):
    """The exact test 19-F54 used: a missed WIN, i.e. an alternative mates at once while this move does not."""
    legal = list(board.legal_moves)
    alt_best = max((status_after(board, m) for m in legal), default=UNKNOWN)
    r = status_after(board, move)
    return alt_best == WIN and r != WIN


lines = ["# the plant for 19-F54's zero", ""]

# the one board in the sample with an immediate mate available
FEN = "6K1/8/1r4k1/8/8/2p5/8/8 b - - 13 186"
b = chess.Board(FEN)
mates = [m for m in b.legal_moves if status_after(b, m) == WIN]
nonmates = [m for m in b.legal_moves if status_after(b, m) != WIN]

lines.append("board: `%s`" % FEN)
lines.append("")
lines.append("- legal moves: %d ; of which MATE AT ONCE: %d (%s) ; NON-mating: %d"
             % (b.legal_moves.count(), len(mates), [m.uci() for m in mates], len(nonmates)))
lines.append("")

real = mates[0] if mates else None
planted = nonmates[0] if nonmates else None

lines.append("## REAL path — the engine's own move (`b6b8`, which mates)")
lines.append("")
lines.append("- move %s -> status %s" % (real.uci(), status_after(b, real)))
lines.append("- **defect reported: %s** (expected: False, because it plays the mate)"
             % defect(b, real))
lines.append("")

lines.append("## PLANT — a legal non-mating move, which the harness MUST flag")
lines.append("")
lines.append("- move %s -> status %s" % (planted.uci(), status_after(b, planted)))
lines.append("- **defect reported: %s** (expected: True — this is the plant)" % defect(b, planted))
lines.append("")

ok = (not defect(b, real)) and defect(b, planted)
lines.append("## verdict")
lines.append("")
lines.append("**The scoring harness distinguishes the two: %s.**" % ("YES" if ok else "NO"))
lines.append("")
if ok:
    lines.append("So 19-F54's zero is a measurement that **can** detect a defect: the same code reported True for a "
                 "bad move and False for the right one on the same board. The zero is therefore 'not shown to be "
                 "wrong' in the Rule 1 sense — the harness is proven able to see a defect.")
else:
    lines.append("**The harness CANNOT distinguish them, so 19-F54's zero is NOT SHOWN and must be withdrawn.**")
text = "\n".join(lines)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print(text)
