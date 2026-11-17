"""Select a fixture where repetition detection is PROVABLY load-bearing.

Two solvers run on the same position:

  * `rep`    -- threefold is a terminal draw (FIDE 9.2), as the engine should
  * `norep`  -- threefold is invisible, so the search returns material/score

A position qualifies only when

    rep_score == 0   and   norep_score <= -300

i.e. the weak side's only half-point comes from reaching a repetition.  That
is a criterion a machine can check, unlike "looks like a perpetual".

The selected fixture is then used to ask whether the ENGINE sees the
repetition in-tree: solve the engine with repetition enabled and with it
ablated; if the two agree, repetition contributed nothing there.
"""

import chess

VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
          chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def material(board):
    return sum((VALUES[p.piece_type] if p.color == board.turn else -VALUES[p.piece_type])
               for p in board.piece_map().values())


class Solver:
    def __init__(self, depth, detect_repetition):
        self.depth = depth
        self.detect = detect_repetition
        self.nodes = 0
        self.pv = []

    def solve(self, board, depth, alpha, beta, path):
        self.nodes += 1
        if self.detect and board.is_repetition(2):
            if not self.pv:
                self.pv = list(path)
            return 0
        if board.is_insufficient_material() or board.halfmove_clock >= 150:
            return 0
        if board.is_checkmate():
            return -30000 + (self.depth - depth)
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
        if best_path is not None and not self.pv:
            self.pv = best_path
        return best


def evaluate(fen, depth=7):
    board = chess.Board(fen)
    if not board.is_valid():
        return None
    r = Solver(depth, True)
    n = Solver(depth, False)
    return {
        "fen": fen,
        "material": material(board),
        "rep": r.solve(board.copy(), depth, -40000, 40000, []),
        "norep": n.solve(board.copy(), depth, -40000, 40000, []),
        "pv": " ".join(m.uci() for m in r.pv),
    }


def candidates():
    """Boxed strong king against a lone queen, plus a far-away strong piece.

    The strong king is boxed by its own pieces so the weak queen always has a
    check; the extra strong piece is placed where the queen cannot take it.
    """
    out = []
    boxes = [
        # strong king, and its own pieces that box it in
        ("h8", [("g7", chess.PAWN), ("h7", chess.PAWN), ("f8", chess.ROOK)]),
        ("g8", [("f7", chess.PAWN), ("g7", chess.PAWN), ("h7", chess.PAWN)]),
        ("a8", [("a7", chess.PAWN), ("b7", chess.PAWN), ("b8", chess.ROOK)]),
    ]
    for king_sq, blockers in boxes:
        for wk in ("h1", "a1", "b1", "g1"):
            for wq in ("e4", "d5", "h5", "d4", "e5", "c5"):
                squares = {king_sq: (chess.KING, chess.BLACK),
                           wk: (chess.KING, chess.WHITE),
                           wq: (chess.QUEEN, chess.WHITE)}
                for bsq, bpt in blockers:
                    squares[bsq] = (bpt, chess.BLACK)
                # a strong queen far from the weak queen's reach
                for extra in ("h4", "a5", "g1", "b2", "c7", "e1", "d8"):
                    if extra in squares:
                        continue
                    sq2 = dict(squares)
                    sq2[extra] = (chess.QUEEN, chess.BLACK)
                    b = chess.Board(None)
                    b.turn = chess.WHITE
                    ok = True
                    for s, (pt, cl) in sq2.items():
                        pc = chess.Piece(pt, cl)
                        if b.piece_at(chess.parse_square(s)) is not None:
                            ok = False
                            break
                        b.set_piece_at(chess.parse_square(s), pc)
                    if not ok:
                        continue
                    b.castling_rights = chess.BB_EMPTY
                    b.ep_square = None
                    b.halfmove_clock = 0
                    b.fullmove_number = 1
                    if b.is_valid() and len(b.piece_map()) == len(sq2):
                        out.append(b.fen())
    return out


if __name__ == "__main__":
    cands = candidates()
    print("candidates: %d" % len(cands))
    hits = []
    for fen in cands:
        res = evaluate(fen, depth=6)
        if not res:
            continue
        if res["rep"] == 0 and res["norep"] <= -300:
            hits.append(res)
            print("HIT  rep=%-6d norep=%-7d mat=%-6d %s\n     pv=%s" % (
                res["rep"], res["norep"], res["material"], fen, res["pv"]))
            if len(hits) >= 5:
                break
    print()
    print("load-bearing fixtures: %d" % len(hits))
