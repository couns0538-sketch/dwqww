"""Random sample over the engine's insufficient-material space, looking for a mating move.

Rationale: the exhaustive sweep is O(64^4) in Python and does not finish. The standard
theorems say mate is impossible here:
  case (a) at most one minor on the board -> the mating side is K + <=1 minor, and
           K vs K, K+B vs K, K+N vs K are all drawn: no mate exists.
  case (b) all bishops of both sides on ONE square colour -> a king on the other colour
           complex is never attacked by any bishop, and every square has at least one
           neighbour of each parity, so a cornered king always has an escape.
This script does NOT prove those theorems; it samples the space so that a gross error in
the engine's predicate (or in my reading of it) would show up as a found mate.
"""
import random
import chess

D = list(chess.SquareSet(chess.BB_DARK_SQUARES))
L = list(chess.SquareSet(chess.BB_LIGHT_SQUARES))
N = 200000
random.seed(100063)  # SEED = 63*1000+... this seat's seed family


def engine_insuff(b):
    for pt in (chess.PAWN, chess.ROOK, chess.QUEEN):
        if b.pieces(pt, chess.WHITE) or b.pieces(pt, chess.BLACK):
            return False
    n = b.pieces(chess.KNIGHT, chess.WHITE) | b.pieces(chess.KNIGHT, chess.BLACK)
    bs = b.pieces(chess.BISHOP, chess.WHITE) | b.pieces(chess.BISHOP, chess.BLACK)
    if len(n) + len(bs) <= 1:
        return True
    return len(n) == 0 and (
        len(bs & chess.SquareSet(chess.BB_DARK_SQUARES)) == 0
        or len(bs & chess.SquareSet(chess.BB_LIGHT_SQUARES)) == 0)


def mate_moves(b):
    out = []
    for m in b.legal_moves:
        b.push(m)
        if b.is_checkmate():
            out.append(m.uci())
        b.pop()
    return out


valid_sampled = 0
insuff_sampled = 0
mated = []
for _ in range(N):
    pool = random.choice((D, L))
    b = chess.Board(None)
    squares = random.sample(range(64), 2 + random.randint(0, 3))
    b.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
    for s in squares[2:]:
        colour = random.choice((chess.WHITE, chess.BLACK))
        pt = chess.BISHOP if random.random() < 0.6 else chess.KNIGHT
        if pt == chess.BISHOP:
            # force same-colour complex so case (b) is reachable
            s = random.choice(pool)
            if b.piece_at(s) is not None:
                continue
        b.set_piece_at(s, chess.Piece(pt, colour))
    b.turn = random.choice((chess.WHITE, chess.BLACK))
    if not b.is_valid():
        continue
    valid_sampled += 1
    if not engine_insuff(b):
        continue
    insuff_sampled += 1
    mm = mate_moves(b)
    if mm:
        mated.append((b.fen(), mm))
print("samples_attempted", N)
print("samples_valid_boards", valid_sampled)
print("samples_engine_insufficient", insuff_sampled)
print("samples_with_a_mating_move", len(mated))
for f in mated[:5]:
    print("  MATE", f)
