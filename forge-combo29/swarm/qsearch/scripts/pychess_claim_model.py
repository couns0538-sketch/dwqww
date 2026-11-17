"""Third-route check: python-chess movegen + independent claim model.
FIDE 9.3 claim: tested on the SIDE TO MOVE when halfmove_clock >= 100; the claim
is optional, so the node value is max(0, continuation).
This is deliberately a different movegen AND a different board model from both
my C++ model and the coordinator's.
"""
import chess, sys

def material(board):
    v = {chess.PAWN:100, chess.KNIGHT:320, chess.BISHOP:330, chess.ROOK:500, chess.QUEEN:900}
    s = 0
    for pt, val in v.items():
        s += val*(len(board.pieces(pt, chess.WHITE)) - len(board.pieces(pt, chess.BLACK)))
    return s

NEVER = object()

def solve(board, depth, alpha, beta, ctx):
    ctx['nodes'] += 1
    if ctx['nodes'] > ctx['cap']:
        raise RuntimeError("cap")
    moves = list(board.legal_moves)
    if not moves:
        if board.is_check():
            return -30000 + (128 - depth)
        return 0
    claimable = board.halfmove_clock >= 100
    if depth <= 0:
        m = material(board)
        return m if board.turn == chess.WHITE else -m
    best = 0 if claimable else -99999
    for mv in moves:
        board.push(mv)
        try:
            s = -solve(board, depth-1, -beta, -alpha, ctx)
        finally:
            board.pop()
        if s > best:
            best = s
            if ctx.get('want_pv') and ctx.get('pv_depth') == depth:
                ctx['pv'] = ([mv] + ctx.get('child_pv', []))
        if best > alpha: alpha = best
        if alpha >= beta: break
    return best

def run(fen, depth, cap=50_000_000):
    b = chess.Board(fen)
    ctx = {'nodes':0, 'cap':cap, 'want_pv':False}
    try:
        s = solve(b, depth, -99999, 99999, ctx)
    except RuntimeError:
        return "CAPPED", ctx['nodes'], None
    return s, ctx['nodes'], None

if __name__ == "__main__":
    fen = sys.argv[1]; 
    depths = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv)>2 else [2,3,4,5,6]
    for d in depths:
        s,n,_ = run(fen,d)
        print(f"  depth {d:>2}: score {str(s):>8s}  nodes {n}")
