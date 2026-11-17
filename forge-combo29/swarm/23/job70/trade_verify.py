#!/usr/bin/env python3
"""Is b6b4 a queen TRADE rather than a queen LOSS? Verify each leg legally, no greedy assumption."""
import chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def adv(bd): return sum(V[p.piece_type]*(1 if p.color==chess.WHITE else -1) for p in bd.piece_map().values())
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
b=chess.Board(FEN)
for mv in ("e6e5","b6b4"):
    c=b.copy(); c.push_uci(mv)
    print("\n=== base/PC move %s (white to move, white %+d) ==="%(mv,adv(c)))
    # what can White capture?
    for m in [x for x in c.legal_moves if c.is_capture(x)]:
        vic=c.piece_at(m.to_square)
        d=c.copy(); d.push(m)
        print("  white %-6s takes %s(%d) -> white %+d"%(m.uci(),vic.symbol(),V[vic.piece_type],adv(d)))
        # black's recaptures of that square
        for r in [x for x in d.legal_moves if x.to_square==m.to_square]:
            e=d.copy(); e.push(r); victim_black=e.piece_at(m.to_square)
            print("      black %-6s recaptures on %s -> white %+d  (black piece now on %s is a %s)"
                  %(r.uci(),chess.square_name(m.to_square),adv(e),chess.square_name(m.to_square),
                    e.piece_at(m.to_square).symbol().upper() if e.piece_at(m.to_square) else "-"))
