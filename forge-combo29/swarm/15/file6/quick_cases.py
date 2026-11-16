import chess
# Targeted: black king boxed in a corner by its own pieces; white has a pawn that can promote with
# mate, and a queen that would mate too -- we need the PAWN move to be the ONLY mate.
# Strategy: enumerate a small structured family and keep only exact single-pawn-mate positions.
def mates(b):
    out=[]
    for mv in b.legal_moves:
        pt=b.piece_type_at(mv.from_square); cap=b.is_capture(mv)
        b.push(mv); m=b.is_checkmate(); b.pop()
        if m: out.append((mv.uci(), pt==chess.PAWN, cap))
    return out

pawn=[]; cap=[]
# black king on h8, own piece on g8 or h7; white pawn can promote to give mate on g8/h8...
grids=[
 "6k1/6P1/8/8/8/8/8/6K1 w - - 0 1",   # Pg7 -> g8=Q
 "7k/6P1/8/8/8/8/8/6K1 w - - 0 1",
 "6k1/5P2/8/8/8/8/8/6K1 w - - 0 1",
 "7k/5P2/8/8/8/8/8/6K1 w - - 0 1",
 "6k1/7P/8/8/8/8/8/6K1 w - - 0 1",
 "k7/1P6/8/8/8/8/8/7K w - - 0 1",
 "1k6/2P5/8/8/8/8/8/7K w - - 0 1",
]
# also add a white queen far away so mate must come from the pawn
for g in list(grids):
    b=chess.Board(g)
    if not b.is_valid(): continue
    m=mates(b)
    if m: print("base grid %-40s mates=%s" % (g,m))
