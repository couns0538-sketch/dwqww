import chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def adv(bd): return sum(V[p.piece_type]*(1 if p.color==chess.WHITE else -1) for p in bd.piece_map().values())
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
b=chess.Board(FEN)
c=b.copy(); c.push_uci("b6b4")
print("after b6b4: white advantage %+d (root %+d)"%(adv(c),adv(b)))
print("white's capture Qd2xb4 available?", chess.Move.from_uci("d2b4") in c.legal_moves)
if chess.Move.from_uci("d2b4") in c.legal_moves:
    d=c.copy(); d.push_uci("d2b4")
    print("  after Qd2xb4: white advantage %+d  (queen taken!)"%adv(d))
    # black recapture?
    for m in [x for x in d.legal_moves if d.is_capture(x)]:
        e=d.copy(); e.push(m)
        print("  black recapture %s -> white %+d"%(m.uci(),adv(e)))
