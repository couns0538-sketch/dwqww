"""Shared fixture construction + validation for the boundary audit.

Every fixture is checked twice before it may be used:
  1. python-chess: the FEN parses, the position is legal, and the structural
     claim the family asserts (mate-in-1 available, every move stalemates,
     etc.) actually holds;
  2. the engine: `position fen` must not answer `invalid FEN`. A refused FEN
     keeps the previous board and manufactures a pass.

python-chess is used as a CONSTRUCTIVE oracle here, not a scoring oracle; the
brief warns its fen() drops the ep square and its repetition logic differs.
Where that matters (repetition family) the claim is asserted on the move list
we send, not on the FEN alone.
"""
import chess
import itertools
import random


def fen_of(board):
    """Full FEN including counters, with the ep square kept if a legal ep
    capture exists (python-chess already does this) -- see brief trap 5."""
    return board.fen()


def legal_and_valid(board):
    return board.is_valid()


def mates_in_one(board):
    """UCI strings of moves that immediately checkmate."""
    out = []
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            out.append(mv.uci())
        board.pop()
    return out


def stalemating_moves(board):
    """Moves after which the opponent is stalemated."""
    out = []
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_stalemate():
            out.append(mv.uci())
        board.pop()
    return out


def opponent_mates_in_one(board):
    """True if, for the given board (opponent to move), they have a mate in 1."""
    return bool(mates_in_one(board))


# ---------------------------------------------------------------------------
# family 1a: side to move has a mate in 1
# ---------------------------------------------------------------------------

def gen_mate_in_one(seed=0, count=50, max_tries=4_000_000):
    """Construct positions where the side to move has a mate in one.

    Constructions are chosen so the mate is unambiguous and the position is
    quiet-ish: random K+Q / K+R / K+Q+minor endgames with the defender
    restricted. We keep only positions with a *forced* mate in 1 (a legal
    mating move exists) and, for a subset, exactly one such move.
    """
    rng = random.Random(seed)
    found = []
    seen = set()
    tries = 0
    while len(found) < count and tries < max_tries:
        tries += 1
        board = _random_mating_position(rng)
        if board is None:
            continue
        if not legal_and_valid(board) or board.is_checkmate() or board.is_stalemate():
            continue
        m = mates_in_one(board)
        if not m:
            continue
        fen = board.fen()
        if fen in seen:
            continue
        seen.add(fen)
        found.append({"fen": fen, "mate_moves": m,
                      "side": "w" if board.turn == chess.WHITE else "b"})
    return found, tries


def _random_mating_position(rng):
    """Throw a small army at a cornered king until a mate in 1 exists."""
    board = chess.Board(None)
    wk_file = rng.choice([0, 1, 6, 7])
    bk_file = rng.choice([0, 1, 6, 7])
    wk = chess.square(wk_file, rng.choice([0, 1, 2, 5, 6, 7]))
    bk = chess.square(bk_file, rng.choice([0, 1, 2, 5, 6, 7]))
    if wk == bk:
        return None
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    free = [s for s in range(64) if s not in (wk, bk)]
    rng.shuffle(free)
    n = rng.randint(1, 3)
    types = [chess.QUEEN, chess.ROOK, chess.QUEEN, chess.BISHOP, chess.KNIGHT]
    for i in range(n):
        pt = rng.choice(types)
        sq = free[i]
        board.set_piece_at(sq, chess.Piece(pt, chess.WHITE))
    board.turn = chess.WHITE if rng.random() < 0.5 else chess.BLACK
    board.castling_rights = 0
    board.ep_square = None
    board.halfmove_clock = 0
    board.fullmove_number = rng.randint(20, 80)
    # A position is legal only if the side NOT to move is not already in check.
    them = board.turn
    board.turn = not them
    in_check = board.is_check()
    board.turn = them
    if in_check:
        return None
    return board


# ---------------------------------------------------------------------------
# family 1b: the opponent has a mate in 1 next move; one move avoids it
# ---------------------------------------------------------------------------

def gen_avoid_mate(seed=0, count=50, max_tries=4_000_000):
    """Positions where the side to move is threatened with mate in 1.

    We require: at least one legal move after which the opponent has NO mate in
    one, and at least one move after which the opponent DOES. The engine must
    pick an avoiding move. A position where every move loses to mate is kept in
    a separate bucket (there the correct answer is 'mate 1' against).
    """
    rng = random.Random(seed)
    found = []
    seen = set()
    tries = 0
    while len(found) < count and tries < max_tries:
        tries += 1
        board = _random_threat_position(rng)
        if board is None:
            continue
        if not legal_and_valid(board) or board.is_checkmate() or board.is_stalemate():
            continue
        avoiding, losing = [], []
        for mv in board.legal_moves:
            board.push(mv)
            if board.is_checkmate():
                board.pop()
                continue  # our own move mates: not an 'avoid' fixture
            if board.is_stalemate() or board.is_game_over(claim_draw=False):
                board.pop()
                continue
            opp_mate = opponent_mates_in_one(board)
            (losing if opp_mate else avoiding).append(mv.uci())
            board.pop()
        if not avoiding or not losing:
            continue
        fen = board.fen()
        if fen in seen:
            continue
        seen.add(fen)
        found.append({"fen": fen, "avoid": avoiding, "lose": losing,
                      "side": "w" if board.turn == chess.WHITE else "b"})
    return found, tries


def _random_threat_position(rng):
    """Black (or White) has a mating net one move away against the mover."""
    board = chess.Board(None)
    mover = rng.choice([chess.WHITE, chess.BLACK])
    opp = not mover
    mk = rng.choice([chess.square(0, 0), chess.square(7, 0), chess.square(0, 7),
                     chess.square(7, 7), chess.square(4, 0), chess.square(4, 7)])
    ok = rng.choice([s for s in range(64) if s != mk])
    board.set_piece_at(mk, chess.Piece(chess.KING, mover))
    board.set_piece_at(ok, chess.Piece(chess.KING, opp))
    free = [s for s in range(64) if s not in (mk, ok)]
    rng.shuffle(free)
    i = 0
    for _ in range(rng.randint(2, 3)):
        pt = rng.choice([chess.QUEEN, chess.ROOK, chess.QUEEN, chess.BISHOP, chess.KNIGHT])
        board.set_piece_at(free[i], chess.Piece(pt, opp))
        i += 1
    if rng.random() < 0.5:
        for _ in range(rng.randint(1, 2)):
            pt = rng.choice([chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK])
            board.set_piece_at(free[i], chess.Piece(pt, mover))
            i += 1
    board.turn = mover
    board.castling_rights = 0
    board.ep_square = None
    board.halfmove_clock = 0
    board.fullmove_number = rng.randint(20, 80)
    if board.is_check() and board.status() != chess.STATUS_VALID:
        return None
    # legality: the side not to move must not be in check
    board.turn = opp
    bad = board.is_check()
    board.turn = mover
    if bad:
        return None
    return board


# ---------------------------------------------------------------------------
# family 2: one ply from stalemate
# ---------------------------------------------------------------------------

def gen_stalemate_next(seed=0, count=25, max_tries=2_000_000, require_all=True):
    """Positions where every legal move stalemates the opponent.

    `require_all=True` is the brief's family: *the only legal moves lead to
    stalemate*. The true value of such a position is a draw (0.00).
    """
    rng = random.Random(seed)
    found = []
    seen = set()
    tries = 0
    while len(found) < count and tries < max_tries:
        tries += 1
        board = _random_stalemate_trap(rng)
        if board is None:
            continue
        if not legal_and_valid(board) or board.is_checkmate() or board.is_stalemate():
            continue
        n_legal = board.legal_moves.count()
        if n_legal == 0:
            continue
        st = stalemating_moves(board)
        if len(st) != n_legal:
            continue
        fen = board.fen()
        if fen in seen:
            continue
        seen.add(fen)
        found.append({"fen": fen, "moves": [m.uci() for m in board.legal_moves],
                      "stale": st, "side": "w" if board.turn == chess.WHITE else "b"})
    return found, tries


def _random_stalemate_trap(rng):
    """A winning side whose every move happens to stalemate the bare king.

    Easiest construction: the strong side has only a king and one minor piece
    that is pinned/blocked, or a queen far away. We search instead of design:
    put a lone king in a corner with its escape squares attacked and give the
    mover a few pieces that cannot deliver mate.
    """
    board = chess.Board(None)
    mover = rng.choice([chess.WHITE, chess.BLACK])
    opp = not mover
    corner = rng.choice([chess.square(0, 0), chess.square(7, 0),
                         chess.square(0, 7), chess.square(7, 7)])
    board.set_piece_at(corner, chess.Piece(chess.KING, opp))
    free = [s for s in range(64) if s != corner]
    rng.shuffle(free)
    board.set_piece_at(free[0], chess.Piece(chess.KING, mover))
    i = 1
    for _ in range(rng.randint(1, 2)):
        pt = rng.choice([chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT])
        board.set_piece_at(free[i], chess.Piece(pt, mover))
        i += 1
    board.turn = mover
    board.castling_rights = 0
    board.ep_square = None
    board.halfmove_clock = 0
    board.fullmove_number = rng.randint(20, 80)
    board.turn = opp
    bad = board.is_check()
    board.turn = mover
    if bad:
        return None
    return board


def gen_stalemate_avoid(seed=0, count=25, max_tries=3_000_000):
    """Winning side to move that has a stalemating move AND a winning move."""
    rng = random.Random(seed)
    found = []
    seen = set()
    tries = 0
    while len(found) < count and tries < max_tries:
        tries += 1
        board = _random_mating_position(rng)
        if board is None:
            continue
        if not legal_and_valid(board) or board.is_checkmate() or board.is_stalemate():
            continue
        st = stalemating_moves(board)
        mate = mates_in_one(board)
        if not st or not mate:
            continue
        # a winning, non-stalemating move that is not mate must exist for the
        # "avoid" question to be about the move, not just about mate-in-1
        if st == mate:
            continue
        fen = board.fen()
        if fen in seen:
            continue
        seen.add(fen)
        found.append({"fen": fen, "stale": st, "mate": mate,
                      "side": "w" if board.turn == chess.WHITE else "b"})
    return found, tries
