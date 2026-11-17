#!/usr/bin/env python3
"""three_counts.py : the STOP note says a castling-disturbing cycle gives 1 occurrence, the
table's column says 3, and I measure 2. All three cannot be right. This enumerates WHICH
positions occur and how often, so the discrepancy has a cause rather than a vote."""
import chess

CASES={
 "M7":("rn1qkb1r/p2p1p2/1p2p3/2pP2pp/Q1N3P1/P1P1BP2/1P2P1K1/R4BNR w kq - 1 15",
       "c4e5 h8g8 e5c4 g8h8 c4e5 h8g8 e5c4 g8h8"),
 "C1":("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
       "a1b1 a8b8 b1a1 b8a8 a1b1 a8b8 b1a1 b8a8"),
}
for name,(fen,mv) in CASES.items():
    b=chess.Board(fen)
    print("=== %s ==="%name)
    print("root fen:",fen)
    def show(bd,tag,root):
        same_place = bd.board_fen()==root[0]
        print("   %-10s castles=%-5s side=%s  same-placement-as-root=%s  FULL match=%s"%(
            tag, bd.castling_rights if bd.castling_rights else "-",
            "w" if bd.turn else "b", same_place,
            same_place and bd.turn==root[1] and bd.castling_rights==root[2]))
    root=(b.board_fen(),b.turn,b.castling_rights)
    show(b,"ply 0 (root)",root)
    n=1
    for i,m in enumerate(mv.split(),1):
        b.push(chess.Move.from_uci(m))
        show(b,"ply %d %s"%(i,m),root)
        if (b.board_fen(),b.turn,b.castling_rights)==root: n+=1
    print("   -> occurrences of the ROOT under placement+side+castling: %d"%n)
    print("   -> the table's column says 3; the STOP note says 1; measured %d"%n)
    print()
