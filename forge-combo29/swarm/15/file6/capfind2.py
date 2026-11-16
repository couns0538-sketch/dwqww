import chess
def mates(b):
    out=[]
    for mv in b.legal_moves:
        pt=b.piece_type_at(mv.from_square); cap=b.is_capture(mv)
        b.push(mv); m=b.is_checkmate(); b.pop()
        if m: out.append((mv.uci(), pt==chess.PAWN, cap))
    return out
# vary which black piece sits on a8 for white Qh1 to capture
cands=[
 "r5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1",
 "n5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1",
 "b5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1",
 "q5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1",
 "p5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1",
 "1r4k1/5ppp/8/8/8/8/8/6KQ w - - 100 1",
 "2r3k1/5ppp/8/8/8/8/8/6KQ w - - 100 1",
 "r4rk1/5ppp/8/8/8/8/8/6KQ w - - 100 1",
]
for c in cands:
    try: b=chess.Board(c)
    except: print("%-42s parse fail"%c); continue
    if not b.is_valid(): print("%-42s INVALID"%c); continue
    pr=b.copy(); pr.turn=chess.BLACK
    if pr.is_check(): print("%-42s black in check"%c); continue
    m=mates(b)
    tag=""
    if len(m)==1 and m[0][2] and not m[0][1]: tag="  <== CAPTURE-ONLY MATE"
    print("%-42s mates=%s%s"%(c,m,tag))
