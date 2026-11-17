"""Correct solver: TT stores ONLY exact values (full window), so no bound pollution."""
import chess, sys
MATE = 10**5

def solve(fen, max_ply=10):
    tt = {}
    def nega(b, ply):
        if b.is_checkmate(): return -MATE + ply
        if not any(b.legal_moves): return 0
        if b.is_insufficient_material(): return 0
        claimable = b.halfmove_clock >= 100
        if not claimable and b.is_repetition(2): return 0
        if ply >= max_ply: return 0
        key = (b._transposition_key(), b.halfmove_clock, ply)
        if key in tt: return tt[key]
        best = -MATE*2
        for m in b.legal_moves:
            b.push(m); s = -nega(b, ply+1); b.pop()
            if s > best: best = s
        if claimable: best = max(0, best)
        tt[key] = best
        return best
    return nega(chess.Board(fen), 0)

def show(v):
    if v > MATE//2:    return f"mate +{(MATE-v+1)//2}"
    if v < -(MATE//2): return f"mate -{((MATE+v)+1)//2}"
    return "draw 0"
