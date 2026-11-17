import chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
FEN2="5k2/1p4p1/2p2p1p/p2p4/P2PqP2/1QP3P1/1P3P2/5K2 b - - 16 35"
def best_static_capture(bd):
    """one-ply static exchange: best net gain available to side to move, no recapture allowed."""
    best=0; bm=None
    for m in bd.legal_moves:
        if not bd.is_capture(m): continue
        vic=bd.piece_at(m.to_square)
        if vic is None: continue
        c=bd.copy(); mover=c.piece_at(m.from_square); c.push(m)
        # was the capturing piece itself recapturable? report gain as victim value only, per F130's convention
        gain=V[vic.piece_type]
        if gain>best: best,bm=gain,m.uci()
    return best,bm
for label,mv in (("base c6c5","c6c5"),("PC e4e8","e4e8")):
    c=chess.Board(FEN2); c.push_uci(mv)
    g,bf=best_static_capture(c)
    print("%-10s -> side to move (White) best static capture: +%d via %s"%(label,g,bf))
print("\nF130's claim: BOTH allow the opponent +1. Also check the move pair the FINAL cited (e4b1):")
c=chess.Board(FEN2); c.push_uci("e4b1"); g,bf=best_static_capture(c)
print("base c6c5 vs PC e4b1 -> +%d via %s  (FINAL's cited pair)"%(g,bf))
