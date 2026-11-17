import chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def mat(bd): return sum(V[p.piece_type]*(1 if p.color else -1) for p in bd.piece_map().values())
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
b=chess.Board(FEN)
print("root material (black-white): %+d"%mat(b))
b.push_uci("e6e5")            # base bail move
print("after e6e5 (black played): %+d"%mat(b))
b.push_uci("a4b6")            # white takes queen
print("after a4b6 (white wins Q): %+d  <-- swing so far %+d"%(mat(b),mat(b)-0))
# black's best recapture
best=None
for m in [x for x in b.legal_moves if b.is_capture(x)]:
    c=b.copy(); c.push(m); d=mat(c)
    if best is None or d>best[0]: best=(d,m.uci())
print("black recaptures %s -> material %+d"%(best[1],best[0]))
print()
print("NET SWING for Black vs the root: %+d pawns"%(best[0]-0))
print("FINAL says '6 pawns'. F61 says 'roughly a minor piece' (~3). Measured: %d."%abs(best[0]))
