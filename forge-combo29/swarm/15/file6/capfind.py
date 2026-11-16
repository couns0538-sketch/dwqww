import chess
def mates(b):
    out=[]
    for mv in b.legal_moves:
        pt=b.piece_type_at(mv.from_square); cap=b.is_capture(mv)
        b.push(mv); m=b.is_checkmate(); b.pop()
        if m: out.append((mv.uci(), pt==chess.PAWN, cap))
    return out
# A CAPTURE mate: black king boxed, white rook/queen captures a blocker and mates.
cands=[
 # white Q takes on h7 with mate, black king g8 boxed by own pawns
 "6k1/5ppp/8/8/8/8/8/R5QK w - - 100 1",
 "6k1/5pQp/8/8/8/8/8/6K1 w - - 100 1",
 "r5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1",
 "6k1/5ppp/8/8/8/8/8/4R2K w - - 100 1",
 "2r3k1/5ppp/8/8/8/8/8/6RK w - - 100 1",
 "6k1/5p1p/8/7Q/8/8/8/6K1 w - - 100 1",
 "5rk1/5ppp/8/8/8/8/8/6RK w - - 100 1",
]
for c in cands:
    try: b=chess.Board(c)
    except: continue
    if not b.is_valid(): print("%-44s INVALID"%c); continue
    pr=b.copy(); pr.turn=chess.BLACK
    if pr.is_check(): print("%-44s black in check"%c); continue
    m=mates(b)
    tag=""
    if len(m)==1 and m[0][2] and not m[0][1]: tag="  <== CAPTURE-ONLY (non-pawn) MATE"
    print("%-44s mates=%s%s" % (c,m,tag))
