#!/usr/bin/env python3
"""verb_check.py : a DOCUMENT CLAIM THAT IS A DECIDABLE FUNCTION OF A BOARD.
The FINAL said the unsearched move "hangs a piece" (creates a threat) and that the loss was
"roughly a minor piece". Both are checkable against a fixture without an engine: they are
python-chess predicates. This checks the prose claim, not a number - the same class as
"does this number agree with that measurement", applied to a verb instead.

Exits nonzero if any assertion disagrees, or if the KNOWN-ANSWER CONTROL does not come out
the opposite way (a check that cannot distinguish the two shapes is not evidence)."""
import sys, chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
fails=[]
def check(name, got, want):
    ok = got==want
    print("  %-58s got=%-5s want=%-5s %s"%(name,got,want,"OK" if ok else "**FAIL**"))
    if not ok: fails.append(name)

b=chess.Board(FEN)
print("A. FIXTURE 23-F60 (Black to move). Assertions the FINAL's prose makes:")
check("piece on b6 is a QUEEN not a minor piece", b.piece_type_at(chess.B6)==chess.QUEEN, True)
check("queen already attacked at root (White)", b.is_attacked_by(chess.WHITE,chess.B6), True)
c=b.copy(); c.push_uci("e6e5")
check("after e6e5 the queen is STILL on b6", c.piece_at(chess.B6).symbol()=="q", True)
check("after e6e5 the queen is STILL attacked", c.is_attacked_by(chess.WHITE,chess.B6), True)
d=b.copy(); d.push_uci("b6b4")
check("after PC's b6b4 the queen has LEFT b6", d.piece_at(chess.B6) is None, True)
check("=> base IGNORES an existing threat (not a new hang)",
      b.is_attacked_by(chess.WHITE,chess.B6) and c.is_attacked_by(chess.WHITE,chess.B6), True)

print("\nB. KNOWN-ANSWER CONTROL: a board where the move DOES create a new hang.")
# 1.e4 e5 2.Qh5 - black to move, Qh5 attacks e5 and f7; a black move ignoring it must lose material.
ctl=chess.Board("rnbqkbnr/pppp1ppp/8/4p2Q/4P3/8/PPPP1PPP/RNB1KBNR b KQkq - 1 2")
check("control: nothing of Black's is attacked by Qh5 on f7? (piece exists)",
      ctl.piece_at(chess.F7) is not None, True)
# pick a black move that ignores the threat to f7
m=chess.Move.from_uci("a7a6")
e=ctl.copy(); e.push(m)
check("control: after a7a6 the f7 pawn is attacked (threat UNANSWERED)", e.is_attacked_by(chess.WHITE,chess.F7), True)
check("control: f7 was ALSO attacked before a7a6 (so this is also a failure-to-answer, not a new hang)",
      ctl.is_attacked_by(chess.WHITE,chess.F7), True)
# a genuine NEW hang: move a piece TO an attacked square
ctl2=chess.Board("4kr2/8/8/8/8/8/8/4K1N1 w - - 0 1")
assert not ctl2.is_check(), "control fixture must not start in check"
assert chess.Move.from_uci("g1f3") in ctl2.legal_moves, "control move must be legal"
nk=ctl2.piece_at(chess.G1)
check("control2: the KNIGHT on g1 is not attacked before it moves",
      nk.symbol()=="N" and ctl2.is_attacked_by(chess.BLACK,chess.G1), False)
g=ctl2.copy(); g.push_uci("g1f3")
check("control2: after Ng1-f3 the knight's NEW square f3 IS attacked => a GENUINE new hang",
      g.is_attacked_by(chess.BLACK,chess.F3), True)

print("\nVERDICT:", "PASS" if not fails else "FAIL (%d)"%len(fails))
sys.exit(0 if not fails else 1)
