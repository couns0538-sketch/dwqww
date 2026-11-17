"""Select a fixture whose drawing mechanism is provably a repetition.

Requirement, checked mechanically rather than by eye:

  * the side to move is materially lost (static material <= -400), and
  * the solved score is exactly 0, and
  * the principal variation contains the same position three times
    (python-chess `is_repetition(2)` on the third visit).

Only the third condition distinguishes "saved by repetition" from "saved by
a tactic such as winning the queen back".  The engine is not consulted here;
this selects the fixture that the engine test then consumes.
"""

import chess

VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
          chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def material(board):
    return sum((VALUES[p.piece_type] if p.color == board.turn else -VALUES[p.piece_type])
               for p in board.piece_map().values())


def occurrences(board):
    n = 1
    while board.is_repetition(n + 1):
        n += 1
    return n


class Solver:
    def __init__(self, max_depth):
        self.max_depth = max_depth
        self.pv = []

    def solve(self, board, depth, alpha, beta, path):
        if board.is_repetition(2) or board.is_insufficient_material() or board.halfmove_clock >= 100:
            return 0
        if board.is_checkmate():
            return -30000 + (self.max_depth - depth)
        if board.is_stalemate():
            return 0
        if depth <= 0:
            return material(board)
        best, best_path = -40000, None
        for move in board.legal_moves:
            board.push(move)
            score = -self.solve(board, depth - 1, -beta, -alpha, path + [move])
            board.pop()
            if score > best:
                best, best_path = score, path + [move]
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        if best_path is not None:
            self.pv = best_path
        return best


def pv_repeats(fen, pv):
    """True when the PV itself contains a third occurrence of some position."""
    board = chess.Board(fen)
    for move in pv:
        board.push(move)
        if board.is_repetition(2):
            return True
    return False


def scan(fens, depth=6):
    hits, rows = [], []
    for fen in fens:
        board = chess.Board(fen)
        if not board.is_valid():
            continue
        mat = material(board)
        solver = Solver(depth)
        score = solver.solve(board, depth, -40000, 40000, [])
        rep = pv_repeats(fen, solver.pv)
        rows.append((fen, score, mat, rep, " ".join(m.uci() for m in solver.pv)))
        if score == 0 and mat <= -400 and rep:
            hits.append(rows[-1])
    return rows, hits


def build_candidates():
    out = []
    # Black boxed on g8 by its own f7/g7/h7 pawns; white has a lone queen,
    # black has a queen plus a rook.  Vary the white king and queen squares.
    black = {"g8": chess.Piece(chess.KING, chess.BLACK),
             "a8": chess.Piece(chess.QUEEN, chess.BLACK),
             "b8": chess.Piece(chess.ROOK, chess.BLACK),
             "f7": chess.Piece(chess.PAWN, chess.BLACK),
             "g7": chess.Piece(chess.PAWN, chess.BLACK),
             "h7": chess.Piece(chess.PAWN, chess.BLACK)}
    for ksq in ("a1", "b1", "c1", "h1"):
        for qsq in ("d5", "e5", "e4", "d4", "h5", "b5", "e6", "a5"):
            if qsq in black or qsq == ksq:
                continue
            board = chess.Board(None)
            board.turn = chess.WHITE
            for sq, piece in black.items():
                board.set_piece_at(chess.parse_square(sq), piece)
            board.set_piece_at(chess.parse_square(ksq), chess.Piece(chess.KING, chess.WHITE))
            board.set_piece_at(chess.parse_square(qsq), chess.Piece(chess.QUEEN, chess.WHITE))
            board.castling_rights = chess.BB_EMPTY
            board.ep_square = None
            board.halfmove_clock = 0
            board.fullmove_number = 1
            if board.is_valid():
                out.append(board.fen())
    return out


if __name__ == "__main__":
    cands = build_candidates()
    print("candidates:", len(cands))
    rows, hits = scan(cands, depth=6)
    for fen, score, mat, rep, pv in rows:
        if score == 0 and mat <= -400:
            print("%-46s score=%-6d mat=%-6d pv_repeats=%-5s pv=%s" % (fen, score, mat, rep, pv))
    print()
    print("VERIFIED in-tree-repetition fixtures: %d" % len(hits))
    for fen, score, mat, rep, pv in hits[:5]:
        print("  %s  (mat %d, pv %s)" % (fen, mat, pv))
