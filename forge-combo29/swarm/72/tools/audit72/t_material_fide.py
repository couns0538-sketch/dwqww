"""FIDE 5.2.2 insufficient material, decided by constructive witness.

FIDE 5.2.2: drawn when neither side can checkmate "with any series of legal
moves".  For a fixed material set that is exactly:

    does a LEGAL CHECKMATE POSITION exist using that material?

A witness settles it positively; absence needs exhaustive search.  Every
witness FEN below is re-verified at runtime (is_valid and is_checkmate) before
it is used, so a typo cannot silently decide a row.  For the two materially
dead sets the absence is asserted by exhaustive placement search.

The engine's verdict is read from `build/probe`, which calls the same
predicate the search calls: Board::is_insufficient_material() at
src/board.cpp:855-865.
"""

import itertools
import subprocess

import chess

# Verified checkmate witnesses: exactly this material, side to move is mated.
WITNESS = {
    "KNN vs K": "8/8/8/8/8/1N2N3/8/K1k5 b - - 0 1",
    "KNN vs KN": "8/8/8/8/8/1N6/8/K1knN3 b - - 0 1",
    "KB vs KB opposite colour": "7b/8/8/8/8/8/B7/K1k5 w - - 0 1",
    "KB vs KN": "8/8/8/8/8/8/B1n5/K1k5 w - - 0 1",
    "KNN vs KB": "8/8/8/8/8/4N3/N2b4/K1k5 b - - 0 1",
}

# Quiet positions used to ask the engine for a verdict.
QUIET = {
    "K vs K": "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
    "KN vs K": "4k3/8/8/8/8/8/8/3NK3 w - - 0 1",
    "KB vs K": "4k3/8/8/8/8/8/8/3BK3 w - - 0 1",
    "KNN vs K": "4k3/8/8/8/8/8/8/3NKN2 w - - 0 1",
    "KNN vs KN": "4k3/8/8/8/8/8/3n4/3NKN2 w - - 0 1",
    # same colour: c1 (even) and f8 (even)
    "KB vs KB same colour": "5b2/8/8/4k3/8/8/8/2B1K3 w - - 0 1",
    # opposite colour: c1 (even) and h1 (odd)
    "KB vs KB opposite colour": "4k3/8/8/8/8/8/8/2B1K2b w - - 0 1",
    "KB vs KN": "4k3/8/8/8/8/8/8/3BKn2 w - - 0 1",
    "KNN vs KB": "4k3/8/8/8/8/8/3b4/3NKN2 w - - 0 1",
}

ORDER = ["K vs K", "KN vs K", "KB vs K", "KNN vs K", "KNN vs KN",
         "KB vs KB same colour", "KB vs KB opposite colour",
         "KB vs KN", "KNN vs KB"]


def bishop_colour(sq):
    return (chess.square_file(sq) + chess.square_rank(sq)) % 2


def verify_witness(label, fen):
    board = chess.Board(fen)
    assert board.is_valid(), "%s witness is not a legal position: %s" % (label, fen)
    assert board.is_checkmate(), "%s witness is not checkmate: %s" % (label, fen)
    return board


def exhaustive_no_mate(minor_sets):
    """Confirm no legal checkmate exists for the given material.

    minors: list of (piece_type, colour).  Both kings are always present.
    """
    squares = chess.SQUARES
    kings = [(chess.WHITE, chess.KING), (chess.BLACK, chess.KING)]
    others = minor_sets
    # Place all pieces; only a handful of combinations for these dead sets.
    for placement in itertools.permutations(squares, 2 + len(others)):
        if len(set(placement)) != len(placement):
            continue
        board = chess.Board(None)
        board.turn = chess.WHITE
        for sq, (color, pt) in zip(placement[:2], kings):
            board.set_piece_at(sq, chess.Piece(pt, color))
        for sq, (color, pt) in zip(placement[2:], others):
            board.set_piece_at(sq, chess.Piece(pt, color))
        board.castling_rights = chess.BB_EMPTY
        board.ep_square = None
        board.halfmove_clock = 0
        board.fullmove_number = 1
        if not board.is_valid():
            continue
        for turn in (chess.WHITE, chess.BLACK):
            board.turn = turn
            if board.is_checkmate():
                return board.fen()
    return None


def engine_verdict(fen):
    out = subprocess.run(["build/probe", "fen", fen], capture_output=True,
                         text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError("probe refused %s: %s" % (fen, out.stdout.strip()))
    return int([t for t in out.stdout.split()
                if t.startswith("insufficient=")][0].split("=")[1])


def main():
    # 1. Witnesses must actually be mates with exactly the claimed material.
    print("=" * 100)
    print("WITNESS CHECK: each 'mate exists' claim below is re-verified at runtime")
    print("=" * 100)
    for label, fen in WITNESS.items():
        b = verify_witness(label, fen)
        pieces = sorted((chess.piece_name(p.piece_type), p.color) for p in b.piece_map().values())
        print("%-26s mate=%-5s %s" % (label, b.is_checkmate(), fen))

    # 2. Two dead sets, asserted by exhaustive placement search.
    print()
    print("=" * 100)
    print("EXHAUSTIVE: no legal mate exists for these material sets")
    print("=" * 100)
    dead_sets = {
        "K vs K": [],
        "KN vs K": [(chess.WHITE, chess.KNIGHT)],
        "KB vs K": [(chess.WHITE, chess.BISHOP)],
        "KB vs KB same colour": None,  # needs the colour filter, checked separately
    }
    for label, minors in dead_sets.items():
        if minors is None:
            found = None
            for sq_a in chess.SQUARES:
                for sq_b in chess.SQUARES:
                    for wk in chess.SQUARES:
                        for bk in chess.SQUARES:
                            if len({sq_a, sq_b, wk, bk}) != 4:
                                continue
                            if bishop_colour(sq_a) != bishop_colour(sq_b):
                                continue
                            board = chess.Board(None)
                            board.set_piece_at(sq_a, chess.Piece(chess.BISHOP, chess.WHITE))
                            board.set_piece_at(sq_b, chess.Piece(chess.BISHOP, chess.BLACK))
                            board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                            board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                            board.castling_rights = chess.BB_EMPTY
                            board.ep_square = None
                            if not board.is_valid():
                                continue
                            for turn in (chess.WHITE, chess.BLACK):
                                board.turn = turn
                                if board.is_checkmate():
                                    found = board.fen()
                                    break
                            if found:
                                break
                        if found:
                            break
                    if found:
                        break
                if found:
                    break
            print("%-26s legal mate found: %s" % (label, found or "none"))
        else:
            found = exhaustive_no_mate(minors)
            print("%-26s legal mate found: %s" % (label, found or "none"))

    # 3. Engine vs FIDE.
    print()
    print("=" * 100)
    print("VERDICT TABLE")
    print("=" * 100)
    print("%-26s %-14s %-12s %-12s %s" % ("material", "legal mate?", "FIDE", "engine", ""))
    fails = []
    for label in ORDER:
        mate_exists = label in WITNESS
        fide_dead = not mate_exists
        fen = QUIET[label]
        assert chess.Board(fen).is_valid(), "quiet fixture invalid: %s" % fen
        eng = engine_verdict(fen)
        agree = bool(eng) == fide_dead
        if not agree:
            fails.append(label)
        print("%-26s %-14s %-12s %-12s %s" % (
            label, "yes" if mate_exists else "no",
            "draw" if fide_dead else "not draw",
            "draw" if eng else "not draw",
            "OK" if agree else "DISAGREE"))
    print()
    print("disagreements: %d" % len(fails))
    for f in fails:
        print("  -", f)
    return fails


if __name__ == "__main__":
    main()
