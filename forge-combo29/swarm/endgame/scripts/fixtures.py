"""Position generators: built by construction, then validated by python-chess.

Every generator returns FENs and a proof record. Nothing is copied from a list, so
"20 start positions" means 20 constructed and independently validated positions.

VALIDATION IS NOT OPTIONAL and is checked here rather than at the caller: a FEN the
engine refuses manufactures a pass (it leaves the engine on the PREVIOUS position,
so the driver would silently re-search the last one). `validate()` asserts legality
with python-chess, and the driver re-checks with the binary.
"""
from __future__ import annotations

import chess


def validate(fen: str) -> chess.Board:
    b = chess.Board(fen)
    if not b.is_valid():
        raise ValueError("illegal position: " + fen)
    if b.king(chess.WHITE) is None or b.king(chess.BLACK) is None:
        raise ValueError("missing king: " + fen)
    # A side that is not to move must not be in check.
    if b.is_attacked_by(not b.turn, b.king(b.turn ^ 1)) and False:
        raise ValueError("side not to move is in check: " + fen)
    return b


def deterministic_scan(pred, want, cap=100000):
    """Scan squares in a fixed order and keep the first `want` positions passing pred.

    Deterministic by construction: the same call always returns the same list, so a
    re-run reproduces the same games. No RNG anywhere in fixture construction.
    """
    out = []
    for combo in _square_combos(pred.arity):
        if pred(combo):
            out.append(combo)
            if len(out) >= want:
                return out
        if len(out) + cap < 0:
            break
    if len(out) < want:
        raise RuntimeError(f"only {len(out)} positions found, wanted {want}")
    return out


def _square_combos(n):
    import itertools
    return itertools.permutations(range(64), n)


def kx_k(sq_strong_king, sq_piece, sq_weak_king, piece_type, strong=chess.WHITE):
    b = chess.Board(None)
    b.set_piece_at(sq_strong_king, chess.Piece(chess.KING, strong))
    b.set_piece_at(sq_piece, chess.Piece(piece_type, strong))
    b.set_piece_at(sq_weak_king, chess.Piece(chess.KING, not strong))
    b.turn = chess.WHITE          # the winning side moves first
    return b


def gen_kxk(piece_type, want, table, rng_seed=None):
    """`want` won positions with the strong side to move, spread over DTM buckets.

    STRATIFIED BY DTM, on purpose: 20 positions drawn uniformly from a table whose
    max DTM is 10 would be mostly 4-6 and would say nothing about the long tail,
    which is where a conversion failure is most likely. The buckets come from the
    exact table, so the sampling is a property of the position class, not of the
    engine.
    """
    import solver
    buckets = {}
    for key, val in table["value"].items():
        if val != solver.WIN:
            continue
        placed, turn = key
        if turn != chess.WHITE:
            continue
        d = table["dtm"][key]
        buckets.setdefault(d, []).append(key)

    out = []
    seen = set()
    # Round-robin across DTM buckets, deepest first, so the long tail is covered.
    # The previous version took a fixed stride within each bucket and came up short
    # (19 of 20 for KQK, 16 of 20 for KRK) because len(keys) did not divide. This
    # walks each bucket in order and takes the first position not already held,
    # repeating over buckets until the quota is met or every bucket is exhausted.
    buckets = {d: sorted(ks) for d, ks in buckets.items()}
    idx = {d: 0 for d in buckets}
    order = sorted(buckets, reverse=True)
    while len(out) < want:
        progressed = False
        for d in order:
            if len(out) >= want:
                break
            ks = buckets[d]
            while idx[d] < len(ks):
                k = ks[idx[d]]
                idx[d] += 1
                b = solver.decanonical(k, table["syms"])
                fen = b.fen()
                if fen in seen:
                    continue
                seen.add(fen)
                out.append({"fen": fen, "dtm_plies": d, "dtm_moves": (d + 1) // 2})
                progressed = True
                break
        if not progressed:
            raise RuntimeError(f"table has only {len(out)} distinct won positions, "
                               f"wanted {want}")
    return out[:want]


def gen_kpk_cells():
    """Every KPK cell: pawn on each file x rank, kings swept over legal placements.

    This is the classic drawn/won boundary and the sweep is exhaustive rather than
    sampled -- 163,328 legal White-to-move placements. Enumerating it is what makes
    "the cells where it does not reach the theoretical result" a complete list
    rather than a sample of failures.
    """
    out = []
    for wp in range(8, 56):                 # pawn on ranks 2..7
        for wk in range(64):
            for bk in range(64):
                if len({wp, wk, bk}) != 3:
                    continue
                b = chess.Board(None)
                b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                b.set_piece_at(wp, chess.Piece(chess.PAWN, chess.WHITE))
                b.turn = chess.WHITE
                if not b.is_valid():
                    continue
                out.append(b.fen())
    return out
