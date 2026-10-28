"""Like fable_nnue_losing_search.py, but the objective is the ENGINE's own census (fable_census.exe over a pipe):
the number of pseudo-legal noisy moves with see_ge(move, 0) false = what MovePicker defers into bad_captures_.
usage: fable_nnue_losing_search2.py <census.exe> <seed> <seconds> [start_fen]"""
import sys, time, random, subprocess, chess
from chess import PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, WHITE, BLACK

LIMITS = {PAWN: 8, KNIGHT: 2, BISHOP: 2, ROOK: 2, QUEEN: 9, KING: 1}


class Census:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def __call__(self, fen):
        self.p.stdin.write(fen + "\n")
        self.p.stdin.flush()
        out = self.p.stdout.readline().split()
        if not out or out[0] != "ok":
            return None
        return tuple(int(x) for x in out[1:])  # noisy, losing, legal_losing, in_check


def valid(board):
    if board.turn != WHITE or board.is_check() or board.status() != chess.STATUS_VALID:
        return False
    for color in (WHITE, BLACK):
        total = 0
        counts = {}
        for pt, lim in LIMITS.items():
            n = chess.popcount(board.pieces_mask(pt, color))
            if n > lim:
                return False
            counts[pt] = n
            total += n
        promoted = (max(0, counts[KNIGHT] - 2) + max(0, counts[BISHOP] - 2) + max(0, counts[ROOK] - 2) +
                    max(0, counts[QUEEN] - 1))
        if total > 16 or promoted > 8 - counts[PAWN]:
            return False
    return True


def score(board, census):
    if not valid(board):
        return -1, None
    r = census(board.fen())
    if r is None:
        return -1, None
    noisy, losing, legal_losing, in_check = r
    if in_check or noisy > 256 or legal_losing == 0:
        return -1, r
    return losing, r


def mutate(board, rng):
    b = board.copy(stack=False)
    squares = list(chess.SQUARES)
    here = [s for s in squares if b.piece_at(s) is not None]
    r = rng.random()
    if r < 0.30:  # nudge
        sq = rng.choice(here)
        piece = b.piece_at(sq)
        f, k = chess.square_file(sq), chess.square_rank(sq)
        df, dk = rng.choice([(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)])
        if not (0 <= f + df < 8 and 0 <= k + dk < 8):
            return None
        dst = chess.square(f + df, k + dk)
        if b.piece_at(dst) is not None or (piece.piece_type == PAWN and k + dk in (0, 7)):
            return None
        b.remove_piece_at(sq)
        b.set_piece_at(dst, piece)
        return b
    if r < 0.45:  # retype
        cands = [s for s in here if b.piece_type_at(s) != KING]
        if not cands:
            return None
        sq = rng.choice(cands)
        piece = b.piece_at(sq)
        pt = rng.choice([PAWN, KNIGHT, BISHOP, ROOK, QUEEN])
        if pt == piece.piece_type or (pt == PAWN and chess.square_rank(sq) in (0, 7)):
            return None
        b.set_piece_at(sq, chess.Piece(pt, piece.color))
        return b
    if r < 0.55:  # recolour a non-king piece
        cands = [s for s in here if b.piece_type_at(s) != KING]
        if not cands:
            return None
        sq = rng.choice(cands)
        piece = b.piece_at(sq)
        b.set_piece_at(sq, chess.Piece(piece.piece_type, not piece.color))
        return b
    r = rng.random()
    if r < 0.4:  # add
        sq = rng.choice(squares)
        if b.piece_at(sq) is not None:
            return None
        color = rng.choice([WHITE, BLACK])
        pt = rng.choice([PAWN, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, QUEEN])
        if pt == PAWN and chess.square_rank(sq) in (0, 7):
            return None
        b.set_piece_at(sq, chess.Piece(pt, color))
        return b
    cands = [s for s in here if b.piece_type_at(s) != KING]
    if not cands:
        return None
    sq = rng.choice(cands)
    if r < 0.6:  # remove
        b.remove_piece_at(sq)
        return b
    piece = b.piece_at(sq)  # move anywhere
    dst = rng.choice(squares)
    if b.piece_at(dst) is not None or (piece.piece_type == PAWN and chess.square_rank(dst) in (0, 7)):
        return None
    b.remove_piece_at(sq)
    b.set_piece_at(dst, piece)
    return b


def main():
    exe, seed, seconds = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    start_fen = sys.argv[4] if len(sys.argv) > 4 else "1q6/P1pQrbP1/1pKp1Q1b/2pQ1n1Q/N1Np1Q1n/BRpQ1r2/1pRp1Q2/1kB5 w - - 0 1"
    census = Census(exe)
    rng = random.Random(seed)
    board = chess.Board(start_fen)
    board.castling_rights = 0
    board.ep_square = None
    cur, info = score(board, census)
    print(f"start {board.fen()} engine score {cur} {info}", flush=True)
    best, best_board, best_info = cur, board.copy(stack=False), info
    t0 = time.time()
    it = 0
    temp = 2.0
    while time.time() - t0 < seconds:
        it += 1
        cand = mutate(board, rng)
        if cand is None:
            continue
        cand.castling_rights = 0
        cand.ep_square = None
        s, inf = score(cand, census)
        if s < 0:
            continue
        if s >= cur or rng.random() < pow(2.718281828, (s - cur) / temp):
            board, cur, info = cand, s, inf
            if s > best:
                best, best_board, best_info = s, cand.copy(stack=False), inf
                print(f"[{time.time()-t0:6.1f}s it {it}] best {best} engine noisy/losing/legal_losing/in_check {inf} {cand.fen()}", flush=True)
        if it % 2000 == 0:
            temp = max(0.3, temp * 0.9)
        if it % 150000 == 0:
            board, cur, info = best_board.copy(stack=False), best, best_info
            temp = 2.0
    print(f"done it {it} best {best} {best_info} fen {best_board.fen()}", flush=True)


if __name__ == "__main__":
    main()
