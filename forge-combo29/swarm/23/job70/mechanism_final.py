#!/usr/bin/env python3
"""The mechanism, stated exactly: does each move leave the queen capturable, and what does Black get back?"""
import chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def adv(bd): return sum(V[p.piece_type]*(1 if p.color==chess.WHITE else -1) for p in bd.piece_map().values())
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
b=chess.Board(FEN)
print("ROOT: black queen on b6, attacked by white knight a4:", b.is_attacked_by(chess.WHITE,chess.B6))
print("%-8s %-22s %-26s %s"%("move","queen capturable after?","recapture takes back","net for White"))
for mv in ("e6e5","b6b4"):
    c=b.copy(); c.push_uci(mv)
    # the capture White plays
    cap=None
    for m in c.legal_moves:
        if c.is_capture(m) and c.piece_at(m.to_square).piece_type==chess.QUEEN:
            cap=m; break
    d=c.copy(); d.push(cap)
    recs=[x for x in d.legal_moves if x.to_square==cap.to_square]
    best=None
    for r in recs:
        e=d.copy(); e.push(r); a=adv(e)
        if best is None or a<best[0]: best=(a,r.uci())
    print("%-8s %-22s %-26s +%d"%(mv,"YES ("+cap.uci()+")",best[1]+" (net %+.0f)"%best[0],best[0]))
print()
print("So BOTH moves leave the queen capturable. The difference is what Black's recapture takes:")
print("  e6e5  -> White Nxb6 wins QUEEN(9); black axb6 takes a KNIGHT(3)  => White +6")
print("  b6b4  -> White Qxb4 wins QUEEN(9); black Bxb4 takes the QUEEN(9) => White +0, a TRADE")
print("The cost is the RECAPTURE BALANCE, not whether the queen can be taken.")
