import chess, sys
START="1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"
# exact: can the side to move force mate within `plies` plies?
def win(fen, plies):
    if plies<=0: return False
    b=chess.Board(fen); any_=False
    for mv in b.legal_moves:
        b.push(mv)
        if b.is_checkmate(): b.pop(); return True
        nxt=b.fen(); b.pop()
        if lose(nxt, plies-1): return True
    return False
def lose(fen, plies):
    if plies<=0: return False
    b=chess.Board(fen); moves=list(b.legal_moves)
    if not moves: return b.is_checkmate()
    for mv in moves:
        b.push(mv); mated=b.is_checkmate(); nxt=b.fen(); b.pop()
        if mated: continue
        if not win(nxt, plies-1): return False
    return True
for mv in ("c6d6","c6c7"):
    b=chess.Board(START); b.push_uci(mv)
    # after our move it is BLACK to move; black has a forced mate if win(after, plies)
    res={}
    for plies in (3,5,7,9):
        res[plies]=win(b.fen(), plies)
    print(mv, "black forced mate within (3,5,7,9) plies:", res)
