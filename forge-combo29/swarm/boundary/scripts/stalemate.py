"""Construct positions where EVERY legal move stalemates.

Two earlier attempts are kept in the record because they are the failure mode
this audit is about:

  * a probe whose predicate was a tuple, so every move counted as stalemating;
  * exhaustive K+piece vs bare-K enumeration, which found **zero** in ~1M
    boards -- the condition is real but K+Q vs K cannot satisfy it, because a
    strong side that can box a lone king can also mate it.

The construction that works restricts the MOVER as well: the mover's own pawns
are locked against the opponent's, so the mover's only free pieces are its king
and one rook/bishop/knight. Combined with a frozen opponent king, every mover
move can be made to stalemate.

The predicate `every_move_stalemates` is the same one self-tested in
selftest.py, and it is checked against a planted fault (a position known to
have a non-stalemating move) before any clean run is trusted.
"""
import chess
import itertools
import random


def every_move_stalemates(board):
    """(n_stalemating, n_legal). n_legal>0 and equal counts == the condition."""
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


def _legal(board):
    """The side that just moved must not be in check."""
    t = board.turn
    board.turn = not t
    bad = board.is_check()
    board.turn = t
    return not bad


def _locked_pawn_pairs(files, rank):
    """White pawns on `rank`, black pawns directly in front: a mutual block."""
    out = []
    for f in files:
        out.append((chess.square(f, rank), chess.Piece(chess.PAWN, chess.WHITE)))
        out.append((chess.square(f, rank + 1), chess.Piece(chess.PAWN, chess.BLACK)))
    return out


def build(opp_king, mover_king, pawn_files, pawn_rank, pieces, mover=chess.WHITE):
    b = chess.Board(None)
    b.set_piece_at(opp_king, chess.Piece(chess.KING, not mover))
    b.set_piece_at(mover_king, chess.Piece(chess.KING, mover))
    for sq, p in _locked_pawn_pairs(pawn_files, pawn_rank):
        b.set_piece_at(sq, p)
    for sq, pt in pieces:
        if b.piece_at(sq) is not None:
            return None
        b.set_piece_at(sq, chess.Piece(pt, mover))
    b.turn = mover
    b.castling_rights = 0
    b.ep_square = None
    b.halfmove_clock = 0
    b.fullmove_number = 30
    return b


def enum_every_move_stalemates(limit=60, seed=7, tries=3_000_000):
    """Enumerate locked-pawn + one-piece positions where every legal move
    stalemates. Deterministic given `seed`: the search order is fixed and the
    accepted list is stable, so the fixture set is reproducible."""
    rng = random.Random(seed)
    out = []
    seen = set()
    squares = list(range(64))
    piece_kinds = [chess.ROOK, chess.QUEEN, chess.BISHOP, chess.KNIGHT]
    for _ in range(tries):
        if len(out) >= limit:
            break
        mover = chess.WHITE if rng.random() < 0.5 else chess.BLACK
        nfiles = rng.randint(1, 3)
        files = rng.sample(range(8), nfiles)
        rank = rng.randint(1, 5)
        ok = rng.choice(squares)
        mk = rng.choice(squares)
        if mk == ok or chess.square_distance(mk, ok) <= 1:
            continue
        pt = rng.choice(piece_kinds)
        mp = rng.choice(squares)
        b = build(ok, mk, files, rank, [(mp, pt)], mover)
        if b is None or not b.is_valid() or not _legal(b):
            continue
        if b.is_checkmate() or b.is_stalemate():
            continue
        st, tot = every_move_stalemates(b)
        if tot == 0 or st != tot:
            continue
        if mates_in_one(b):
            continue
        fen = b.fen()
        if fen in seen:
            continue
        seen.add(fen)
        out.append({"fen": fen,
                    "moves": [m.uci() for m in b.legal_moves],
                    "mover": "w" if mover == chess.WHITE else "b",
                    "piece": chess.piece_symbol(pt),
                    "pawn_files": files, "pawn_rank": rank})
    return out


def enum_stalemate_available(limit=60, seed=11, tries=4_000_000):
    """The winning side has BOTH a stalemating move and a mating move.

    Correct behaviour: take the mate, score it as a mate. Taking the stalemate
    (or scoring 0.00) is an error, because a win exists.
    """
    rng = random.Random(seed)
    out = []
    seen = set()
    for _ in range(tries):
        if len(out) >= limit:
            break
        mover = chess.WHITE
        ok = rng.choice([chess.A8, chess.H8, chess.A1, chess.H1,
                         chess.A7, chess.H7, chess.A2, chess.H2])
        mk = rng.choice([s for s in range(64) if s != ok])
        if chess.square_distance(mk, ok) <= 1:
            continue
        pt = rng.choice([chess.QUEEN, chess.ROOK])
        mp = rng.choice([s for s in range(64) if s not in (mk, ok)])
        b = chess.Board(None)
        b.set_piece_at(ok, chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(mk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(mp, chess.Piece(pt, chess.WHITE))
        b.turn = mover
        b.castling_rights = 0
        b.ep_square = None
        b.halfmove_clock = 0
        b.fullmove_number = 40
        if not b.is_valid() or not _legal(b):
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
    return out
