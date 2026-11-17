import chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def adv(bd): return sum(V[p.piece_type]*(1 if p.color==chess.WHITE else -1) for p in bd.piece_map().values())
FEN2="5k2/1p4p1/2p2p1p/p2p4/P2PqP2/1QP3P1/1P3P2/5K2 b - - 16 35"
b=chess.Board(FEN2)
print("root white-advantage (static material): %+d"%adv(b))
for mv in ("c6c5","e4b1"):
    c=b.copy(); c.push_uci(mv)
    print(" after %-6s white-advantage %+d"%(mv,adv(c)))
print("\nFINAL/F130 claim: 'both moves allow the same +1'. Check: does the better side win +1?")
