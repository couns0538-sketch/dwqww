import chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def mat(bd): return sum(V[p.piece_type]*(1 if p.color else -1) for p in bd.piece_map().values())
FEN2="5k2/1p4p1/2p2p1p/p2p4/P2PqP2/1QP3P1/1P3P2/5K2 b - - 16 35"
b=chess.Board(FEN2)
print("B2 turn black. material(black-white) root:", mat(b))
# which black pieces are attacked?
for sq,pc in b.piece_map().items():
    if pc.color==chess.BLACK and pc.piece_type!=chess.KING and b.is_attacked_by(chess.WHITE,sq):
        print("  black",pc.symbol(),"on",chess.square_name(sq),"attacked by white from",
              [chess.square_name(s) for s in b.attackers(chess.WHITE,sq)])
for mv in ("c6c5","e4b1"):
    c=b.copy(); c.push_uci(mv)
    print(" after %s: material %+d" % (mv,mat(c)))
    for sq,pc in c.piece_map().items():
        if pc.color==chess.BLACK and pc.piece_type!=chess.KING and c.is_attacked_by(chess.WHITE,sq):
            print("    still attacked:",pc.symbol(),chess.square_name(sq))
