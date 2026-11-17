import chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def white_adv(bd): return sum(V[p.piece_type]*(1 if p.color else -1) for p in bd.piece_map().values())
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
b=chess.Board(FEN); b.push_uci("e6e5"); b.push_uci("a4b6")
print("After White takes the queen, BLACK chooses; white's advantage for each recapture:")
opts=[]
for m in [x for x in b.legal_moves if b.is_capture(x)]:
    c=b.copy(); c.push(m); opts.append((white_adv(c),m.uci()))
for a,mv in sorted(opts): print("   %-6s -> white +%d"%(mv,a))
best=min(opts)
print("\nBLACK's least-bad recapture: %s -> White +%d  (this is the number to quote)"%(best[1],best[0]))
print("F129 said +6; measured +%d -> %s"%(best[0],"AGREES" if best[0]==6 else "DISAGREES"))
print("\nMy earlier swing.py reported +8 by MAXIMISING white's advantage and calling it black's best - my bug, not the report's.")
