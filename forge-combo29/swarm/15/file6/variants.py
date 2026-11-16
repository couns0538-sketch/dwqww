import chess
def mates(b):
    out=[]
    for mv in b.legal_moves:
        pt=b.piece_type_at(mv.from_square); cap=b.is_capture(mv)
        b.push(mv); m=b.is_checkmate(); b.pop()
        if m: out.append((mv.uci(), pt==chess.PAWN, cap))
    return out
# The known working case, then systematic variants that keep the geometry but change material/side.
known = "8/P7/k7/P7/2K5/8/7Q/8 w - - 100 1"
print("=== known case ===")
b=chess.Board(known); print(known, "->", mates(b))
print()
print("=== variants of the same geometry ===")
cands = [
 # move the white queen, keep P a7 and black K a6, white K c4
 "8/P7/k7/P7/2K5/8/7Q/8 w - - 100 1",
 "8/P7/k7/P7/2K5/8/8/6Q1 w - - 100 1",
 "8/P7/k7/P7/2K5/8/8/Q7 w - - 100 1",
 "8/P7/k7/P7/2K5/8/1Q6/8 w - - 100 1",
 "8/P7/k7/P7/2K5/8/8/1Q6 w - - 100 1",
 "8/P7/k7/P7/2K5/8/8/4Q3 w - - 100 1",
 # black to move variants are useless; keep white to move
 # different ranks: white K further away
 "8/P7/k7/P7/8/8/2K5/7Q w - - 100 1",
 "8/P7/k7/P7/8/2K5/8/7Q w - - 100 1",
 "8/P7/k7/P7/8/8/8/2K4Q w - - 100 1",
 # a black pawn blocking, so the mate must be the a8 promotion
 "8/P7/k7/P7/2K5/8/8/7Q w - - 100 1",
 "8/P7/kp6/P7/2K5/8/8/7Q w - - 100 1",
]
for c in cands:
    try: b=chess.Board(c)
    except Exception as e: print("%-42s parse fail" % c); continue
    if not b.is_valid(): print("%-42s INVALID" % c); continue
    pr=b.copy(); pr.turn=chess.BLACK
    if pr.is_check(): print("%-42s illegal (black in check)"%c); continue
    m=mates(b)
    tag=""
    if len(m)==1 and m[0][1]: tag="  <== PAWN-ONLY MATE"
    elif all(x[1] or x[2] for x in m) and m: tag="  <== all mates are pawn/capture"
    print("%-42s mates=%s%s" % (c,m,tag))
