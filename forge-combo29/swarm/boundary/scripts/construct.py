"""Exhaustive enumerators for the boundary families.

Written after two false starts, both recorded here because they are the
mistake this audit is about:

  1. A one-liner probe that counted "stalemating moves" with
     `(b.push(m), b.is_stalemate(), b.pop())` inside a comprehension. The tuple
     is always truthy, so EVERY move counted as stalemating and the probe
     reported 26/26 for a position that is really 4/26. That is a checker that
     never fires on a clean run -- brief rule 3.
  2. A random sampler that failed to reach "every legal move stalemates" in
     2,000,000 tries. The condition is *structural*, so it must be enumerated.

`all_moves_stalemate` is the single source of truth; both generators call it,
and it is exercised by a planted-fault self-test in `selftest.py`.
"""
import chess
import itertools


def all_moves_stalemate(board):
    """(#stalemating moves, #legal moves). Equal (and > 0) means the brief's
    condition: *the only legal moves lead to stalemate*."""
    n = board.legal_moves.count()
    if n == 0:
        return 0, 0
    st = 0
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_stalemate():
            st += 1
        board.pop()
    return st, n


def mates_in_one(board):
    out = []
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            out.append(mv.uci())
        board.pop()
    return out


def opp_has_mate_in_one(board):
    """Board has opponent to move; do they have a mate in 1?"""
    return bool(mates_in_one(board))


def side_not_to_move_in_check(board):
    """Legality: the side that just moved must not be left in check."""
    t = board.turn
    board.turn = not t
    bad = board.is_check()
    board.turn = t
    return bad


def base(king_sq, pieces, mover, hm=0, fm=30):
    """Build a board with no castling and no ep."""
    b = chess.Board(None)
    b.set_piece_at(king_sq, chess.Piece(chess.KING, mover))
    for sq, pt, col in pieces:
        b.set_piece_at(sq, chess.Piece(pt, col))
    b.turn = mover
    b.castling_rights = 0
    b.ep_square = None
    b.halfmove_clock = hm
    b.fullmove_number = fm
    return b


# ---------------------------------------------------------------------------
# Family 2a: EVERY legal move stalemates (value 0.00, no winner exists)
# ---------------------------------------------------------------------------

def opp_frozen(board, mover):
    """True iff the side NOT to move has zero legal moves and is not in check.

    This is the precondition for 'every legal mover move stalemates': with the
    opponent already immobilised, any mover move that neither checks nor
    releases the box leaves the opponent stalemated when it becomes its turn.
    (A frozen king while the *other* side is to move is a legal, quiet
    position -- stalemate only exists for the side to move.)
    """
    t = board.turn
    board.turn = not mover
    frozen = (board.legal_moves.count() == 0) and not board.is_check()
    board.turn = t
    return frozen


def enum_every_move_stalemates(piece_types=(chess.QUEEN, chess.ROOK,
                                            chess.BISHOP, chess.KNIGHT),
                               limit=200):
    """Exhaustive over: opponent bare king frozen on any square, mover K + one
    piece, every mover move stalemates.

    The engine's correct answer here is a draw: no sequence wins, and the
    position is a dead draw the moment the mover makes any move.
    """
    out = []
    seen = set()
    sqs = list(range(64))
    for mover in (chess.WHITE, chess.BLACK):
        opp = not mover
        for pt in piece_types:
            for ok in sqs:
                for mk in sqs:
                    if mk == ok or chess.square_distance(mk, ok) <= 1:
                        continue
                    for mp in sqs:
                        if mp in (mk, ok):
                            continue
                        b = base(mk, [(mp, pt, mover), (ok, chess.KING, opp)], mover)
                        if not b.is_valid():
                            continue
                        if side_not_to_move_in_check(b):
                            continue
                        if not opp_frozen(b, mover):
                            continue
                        if mates_in_one(b):
                            continue  # that is the mate family, not this one
                        st, tot = all_moves_stalemate(b)
                        if tot == 0 or st != tot:
                            continue
                        fen = b.fen()
                        if fen in seen:
                            continue
                        seen.add(fen)
                        out.append({"fen": fen,
                                    "moves": [m.uci() for m in b.legal_moves],
                                    "mover": "w" if mover == chess.WHITE else "b",
                                    "material": "K" + chess.piece_symbol(pt).upper() + "vK"})
                        if len(out) >= limit:
                            return out
    return out


def enum_every_move_stalemates_kp(limit=200):
    """King-and-pawn locks: a pawn chain that cannot move, so every king move
    stalemates. This is the family with genuinely NO mate anywhere, which is
    what makes it the right control for 'does the engine prefer stalemate when
    losing' -- here there is nothing to prefer.

    Enumerated for White to move, then colour-mirrored so both colours appear.
    """
    out = []
    seen = set()
    for f1, f2 in itertools.combinations(range(8), 2):
        for r in range(2, 6):
            w1, b1 = chess.square(f1, r), chess.square(f1, r + 1)
            w2, b2 = chess.square(f2, r), chess.square(f2, r + 1)
            for mk in range(64):
                for ok in range(64):
                    if mk == ok or chess.square_distance(mk, ok) <= 1:
                        continue
                    if {mk, ok} & {w1, b1, w2, b2}:
                        continue
                    b = chess.Board(None)
                    b.set_piece_at(mk, chess.Piece(chess.KING, chess.WHITE))
                    b.set_piece_at(ok, chess.Piece(chess.KING, chess.BLACK))
                    for s in (w1, w2):
                        b.set_piece_at(s, chess.Piece(chess.PAWN, chess.WHITE))
                    for s in (b1, b2):
                        b.set_piece_at(s, chess.Piece(chess.PAWN, chess.BLACK))
                    b.turn = chess.WHITE
                    b.castling_rights = 0
                    b.ep_square = None
                    b.halfmove_clock = 0
                    b.fullmove_number = 30
                    if not b.is_valid() or side_not_to_move_in_check(b):
                        continue
                    if b.is_checkmate() or b.is_stalemate():
                        continue
                    st, tot = all_moves_stalemate(b)
                    if tot == 0 or st != tot:
                        continue
                    for variant in (b, b.mirror()):
                        fen = variant.fen()
                        if fen in seen:
                            continue
                        seen.add(fen)
                        out.append({"fen": fen,
                                    "moves": [m.uci() for m in variant.legal_moves],
                                    "mover": "w" if variant.turn else "b",
                                    "material": "KPvKP"})
                        if len(out) >= limit:
                            return out
    return out


# ---------------------------------------------------------------------------
# Family 2b: winning side has BOTH a stalemating move and a winning move
# ---------------------------------------------------------------------------

def enum_stalemate_available(piece_types=(chess.QUEEN, chess.ROOK), limit=100):
    """Mover is clearly winning (K+Q or K+R vs bare king, opponent boxed) and
    has at least one move that stalemates and at least one that mates.

    The engine must NOT take the stalemating move, and its score must be a
    mate score, not 0.00.
    """
    out = []
    seen = set()
    for pt in piece_types:
        for ok in range(64):
            for mk in range(64):
                if mk == ok or chess.square_distance(mk, ok) <= 1:
                    continue
                for mp in range(64):
                    if mp in (mk, ok):
                        continue
                    b = base(mk, [(mp, pt, chess.WHITE), (ok, chess.KING, chess.BLACK)],
                             chess.WHITE)
                    if not b.is_valid() or side_not_to_move_in_check(b):
                        continue
                    if b.is_checkmate() or b.is_stalemate():
                        continue
                    mates = mates_in_one(b)
                    if not mates:
                        continue
                    stale = []
                    for m in b.legal_moves:
                        b.push(m)
                        if b.is_stalemate():
                            stale.append(m.uci())
                        b.pop()
                    if not stale:
                        continue
                    fen = b.fen()
                    if fen in seen:
                        continue
                    seen.add(fen)
                    out.append({"fen": fen, "mates": mates, "stale": stale,
                                "material": "K" + chess.piece_symbol(pt).upper() + "vK"})
                    if len(out) >= limit:
                        return out
    return out
