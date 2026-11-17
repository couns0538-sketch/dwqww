import chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def adv(bd): return sum(V[p.piece_type]*(1 if p.color==chess.WHITE else -1) for p in bd.piece_map().values())
def line(fen,mv,depth=3):
    b=chess.Board(fen); b.push_uci(mv)
    print("  after %s: white %+d"%(mv,adv(b)))
    # follow captures for a few plies to see what the exchange settles at
    for _ in range(depth):
        caps=[m for m in b.legal_moves if b.is_capture(m)]
        if not caps: break
        # side to move takes the most valuable victim available
        best=max(caps,key=lambda m: V[b.piece_at(m.to_square).piece_type])
        vic=b.piece_at(best.to_square)
        b.push(best)
        print("     %s %s takes %s(%d) -> white %+d"%("white" if b.turn==chess.BLACK else "black",
              best.uci(),vic.symbol(),V[vic.piece_type],adv(b)))
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
print("BOARD 1 (23-F60): the two moves and their forced capture sequence")
for mv in ("e6e5","b6b4"): line(FEN,mv)
print("\nBOARD 2 (23-F130/F60): the two moves")
FEN2="5k2/1p4p1/2p2p1p/p2p4/P2PqP2/1QP3P1/1P3P2/5K2 b - - 16 35"
for mv in ("c6c5","e4b1","e4e8"): line(FEN2,mv)
