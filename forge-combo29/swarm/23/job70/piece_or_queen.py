import subprocess, chess, sys
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
b=chess.Board(FEN)
def val(board):
    v={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9}
    w=sum(v.get(p.piece_type,0) for p in board.piece_map().values() if p.color==chess.WHITE)
    k=sum(v.get(p.piece_type,0) for p in board.piece_map().values() if p.color==chess.BLACK)
    return k-w  # black minus white, from black's view
print("material before (black - white):", val(b))
# play e6e5, then ask the engine for black's best reply line? we want: what does WHITE win
b2=b.copy(); b2.push_uci("e6e5")
print("material after e6e5:", val(b2))
# what hangs: for each white capture available, net material swing
moves=[m for m in b2.legal_moves if b2.is_capture(m)]
res=[]
for m in moves:
    c=b2.copy(); cap=c.piece_at(m.to_square); c.push(m)
    # after capture, can black recapture?
    best=None
    for rm in [x for x in c.legal_moves if c.is_capture(x)]:
        d=c.copy(); rcap=d.piece_at(rm.to_square); d.push(rm)
        swing=val(d)-val(b)
        if best is None or swing<best[0]: best=(swing,rm.uci(),rcap.symbol() if rcap else None)
    res.append((cap.symbol(), chess.square_name(m.to_square), m.uci(), best))
for r in sorted(res,key=lambda x:x[3][0]):
    print("white captures %s on %s (%s); after black's best recapture %s (%s) material(black-white)=%d -> swing %d"
          %(r[0],r[1],r[2],r[3][1],r[3][2],r[3][0],r[3][0]-val(b)))
