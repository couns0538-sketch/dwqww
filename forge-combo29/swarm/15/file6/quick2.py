import chess, itertools, random
def mates(b):
    out=[]
    for mv in b.legal_moves:
        pt=b.piece_type_at(mv.from_square); cap=b.is_capture(mv)
        b.push(mv); m=b.is_checkmate(); b.pop()
        if m: out.append((mv.uci(), pt==chess.PAWN, cap))
    return out
# Black king on the 8th rank in a corner, blocked by ONE own piece; white pawn on the 7th promoting.
found_p=[]; found_c=[]
rng=random.Random(7)
squares=[s for s in range(64)]
for trial in range(60000):
    b=chess.Board(None)
    # white pawn on rank 7 (index 6), black king on rank 8 adjacent
    pf=chess.square(rng.randrange(8),6)
    prom_to=chess.square(chess.square_file(pf),7)
    # black king near the promotion square
    kcands=[s for s in chess.SquareSet(chess.BB_KING_ATTACKS[prom_to])
            if chess.square_rank(s)==7]
    if not kcands: continue
    bk=rng.choice(kcands)
    b.set_piece_at(pf, chess.Piece(chess.PAWN, chess.WHITE))
    b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    # white king somewhere legal
    wkc=[s for s in squares if s not in (pf,bk)]
    wk=rng.choice(wkc)
    b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    b.turn=chess.WHITE; b.castling_rights=chess.BB_EMPTY
    if not b.is_valid(): continue
    pr=b.copy(); pr.turn=chess.BLACK
    if pr.is_check(): continue
    m=mates(b)
    if len(m)==1 and m[0][1]:
        if b.fen() not in [x[0] for x in found_p]: found_p.append((b.fen(),m[0][0]))
        if len(found_p)>=3: break
print("PAWN-MOVE-ONLY MATES:")
for f,u in found_p: print("  %-40s %s" % (f,u))
