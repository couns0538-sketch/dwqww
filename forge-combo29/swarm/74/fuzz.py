"""Fuzz: random legal positions, engine `go perft 3` vs python-chess perft 3.

Positions come from random legal playouts (python-chess), which is what makes
them legal by construction. Each one is still run through the same three gates
as every other comparison: python-chess validation, a scan of the position reply
for the engine's invalid-FEN diagnostic, and a perft-1 / perft-2 board-identity
check before the depth-3 number is scored.

Seeded, so any mismatch is reproducible: the report prints the seed and the
playout's move list alongside the FEN.

Usage: python3 fuzz.py <engine-binary> [--count N] [--seed S] [--json out.json]
"""

from __future__ import annotations

import json
import random
import sys
import time

import chess

from uci_perft import Engine, EngineError, FenRejected, py_perft, validate_fen

DEFAULT_COUNT = 2000
DEFAULT_SEED = 74_000
DEPTH = 3
MAX_PLIES = 80


def _playout(rng: random.Random, board: chess.Board) -> tuple[str, list[str]]:
    moves: list[str] = []
    for _ in range(rng.randint(4, MAX_PLIES)):
        legal = list(board.legal_moves)
        if not legal:
            break
        move = rng.choice(legal)
        board.push(move)
        moves.append(move.uci())
        if board.is_game_over(claim_draw=False):
            break
    fen = board.fen()
    # Belt and braces: the playout cannot produce an illegal FEN, but assert it.
    if not board.is_valid():
        raise AssertionError(f"playout produced an invalid FEN: {fen} {sorted(board.status())}")
    return fen, moves


def random_position(rng: random.Random) -> tuple[str, list[str]]:
    """A position from a random legal playout; legal by construction."""
    return _playout(rng, chess.Board())


def sparse_endgame(rng: random.Random) -> chess.Board:
    """A legal sparse endgame, so playouts actually reach promotions and ep.

    Uniform random play from the start position almost never promotes (measured:
    19 of 2000 positions had a promotion available). Seeding the playout from
    thin material raises the promotion and en-passant rate without changing what
    is tested: positions are still reached by random legal play, so they are
    legal by construction rather than hand-built.
    """
    while True:
        board = chess.Board.empty()
        board.set_piece_at(
            chess.square(rng.randrange(8), rng.randrange(8)),
            chess.Piece(chess.KING, chess.WHITE),
        )
        board.set_piece_at(
            chess.square(rng.randrange(8), rng.randrange(8)),
            chess.Piece(chess.KING, chess.BLACK),
        )
        if board.king(chess.WHITE) == board.king(chess.BLACK):
            continue
        for _ in range(rng.randint(2, 6)):
            color = rng.choice([chess.WHITE, chess.BLACK])
            kind = rng.choice(
                [chess.PAWN, chess.PAWN, chess.PAWN, chess.KNIGHT,
                 chess.BISHOP, chess.ROOK, chess.QUEEN]
            )
            sq = chess.square(rng.randrange(8), rng.randrange(8))
            # No pawns on the back ranks, and nothing spawns on an occupied square.
            if kind == chess.PAWN and chess.square_rank(sq) in (0, 7):
                continue
            if board.piece_at(sq) is not None:
                continue
            board.set_piece_at(sq, chess.Piece(kind, color))
        board.turn = rng.choice([chess.WHITE, chess.BLACK])
        board.castling_rights = chess.BB_EMPTY
        board.ep_square = None
        board.halfmove_clock = 0
        board.fullmove_number = 1
        if board.is_valid():
            return board


def castling_position(rng: random.Random) -> tuple[str, list[str]]:
    """A legal position with castling rights still live on both wings.

    Random play almost always loses the rights by the time it settles, so this
    builds a bare-back-rank position and randomises the attacking material
    around it, then validates. The point is to exercise castling legality --
    through attacked squares, out of check, and with the rook attacked -- at
    the counts, not just in the hand-built fixtures.
    """
    attempts = 0
    while True:
        attempts += 1
        if attempts > 4000:
            raise RuntimeError("castling_position could not build a legal position")
        board = chess.Board.empty()
        board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
        board.set_piece_at(chess.H1, chess.Piece(chess.ROOK, chess.WHITE))
        board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
        board.set_piece_at(chess.A8, chess.Piece(chess.ROOK, chess.BLACK))
        board.set_piece_at(chess.H8, chess.Piece(chess.ROOK, chess.BLACK))
        board.castling_rights = (
            chess.BB_A1 | chess.BB_H1 | chess.BB_A8 | chess.BB_H8
        )
        for _ in range(rng.randint(1, 5)):
            kind = rng.choice(
                [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
            )
            sq = chess.square(rng.randrange(8), rng.randrange(8))
            if board.piece_at(sq) is not None:
                continue
            board.set_piece_at(sq, chess.Piece(kind, rng.choice([chess.WHITE, chess.BLACK])))
        board.turn = rng.choice([chess.WHITE, chess.BLACK])
        board.ep_square = None
        board.halfmove_clock = 0
        if not board.is_valid():
            continue
        if not (board.has_castling_rights(chess.WHITE) or board.has_castling_rights(chess.BLACK)):
            continue
        # Return directly: a playout from here would usually spend the rights,
        # which is exactly what this mode exists to keep alive.
        return board.fen(), []


def biased_position(rng: random.Random) -> tuple[str, list[str]]:
    """A playout from a sparse endgame: same legality, far more promotions/ep."""
    return _playout(rng, sparse_endgame(rng))


EP_PIECE_KINDS = [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, None]
EP_VICTIM_RANKS = [3, 4]  # black/white home ranks for the capturing pawn


def ep_decorated_position(rng: random.Random) -> tuple[str, list[str]]:
    """A biased playout that is guaranteed to arrive next to an ep opportunity.

    Random play is a poor way to reach en passant: it needs a double push with an
    enemy pawn already standing on the landing square's flank. This builds one
    directly, still as a legal position (python-chess validated) and still a
    random playout from there, so the rest of the position stays random.
    """
    attempts = 0
    while True:
        board = sparse_endgame(rng)
        color = rng.choice([chess.WHITE, chess.BLACK])
        step = 2 if color == chess.WHITE else -2
        capturer_rank = 1 if color == chess.WHITE else 6
        flank_rank = capturer_rank + step
        file_in = rng.randrange(0, 8)
        flank_file = file_in + rng.choice([-1, 1])
        if not (0 <= flank_file <= 7):
            continue
        push_from = chess.square(file_in, capturer_rank)
        push_to = chess.square(file_in, capturer_rank + step)
        flank_sq = chess.square(flank_file, flank_rank)
        # The landing square must be EMPTY: a double push cannot capture. The
        # flank pawns stand beside it, and they are what the ep capture takes.
        if board.piece_at(flank_sq) is not None or board.piece_at(push_from) is not None:
            continue
        if board.piece_at(push_to) is not None:
            continue
        board.set_piece_at(flank_sq, chess.Piece(chess.PAWN, not color))
        board.set_piece_at(push_from, chess.Piece(chess.PAWN, color))
        board.turn = color
        board.castling_rights = chess.BB_EMPTY
        board.ep_square = None
        board.halfmove_clock = 0
        if not board.is_valid():
            continue
        # The pusher may be pinned, so the double push itself must be legal;
        # pushing it blindly can leave the mover in check and corrupt the FEN.
        push = chess.Move(push_from, push_to)
        if push not in board.legal_moves:
            continue
        board.push(push)
        # Return the position with the ep right LIVE: playing more random plies
        # here would usually spend it, which is the flaw that made the earlier
        # version reach ep in zero positions.
        if board.ep_square is not None and any(
            board.is_en_passant(m) for m in board.legal_moves
        ):
            return board.fen(), [push.uci()]
        if attempts > 4000:
            raise RuntimeError("ep_decorated_position could not build an ep position")
        attempts += 1


# --- Targeted edges -------------------------------------------------------
#
# The brief named three edges as this seat's marginal value. Uniform random play
# reaches them too rarely to prove anything (measured: promotion available in 19
# of 2000), so each edge gets a generator that keeps sampling until the edge is
# genuinely live, and a predicate that proves it from python-chess's own
# semantics rather than from the construction's intent.


def _ep_capture_moves(board: chess.Board) -> list[chess.Move]:
    return [m for m in board.legal_moves if board.is_en_passant(m)]


def edge_ep_discovers_check(board: chess.Board) -> bool:
    """An en-passant capture is legal and delivers check by discovery.

    The capture must give check while NOT being a direct check by the capturing
    pawn -- i.e. it opens a line. Verified by pushing the move and asking whose
    turn it is to be in check, then confirming the pawn itself does not attack
    the king from its new square.
    """
    for move in _ep_capture_moves(board):
        board.push(move)
        gives_check = board.is_check()
        if gives_check:
            king_sq = board.king(board.turn)
            pawn_attacks = chess.BB_PAWN_ATTACKS[not board.turn][move.to_square]
            direct = bool(pawn_attacks & chess.BB_SQUARES[king_sq])
        board.pop()
        if gives_check and not direct:
            return True
    return False


def edge_ep_exposes_king(board: chess.Board) -> bool:
    """An en-passant capture is pseudo-legally available but illegal.

    This is the classic edge: the capture is geometrically possible, yet it is
    absent from legal_moves because it would expose the king. Detected by
    checking that the capturing pawn stands beside the ep square and the capture
    is missing from legal_moves.
    """
    if board.ep_square is None:
        return False
    ep_file = chess.square_file(board.ep_square)
    ep_rank = chess.square_rank(board.ep_square)
    from_rank = ep_rank - 1 if board.turn == chess.WHITE else ep_rank + 1
    for file_delta in (-1, 1):
        f = ep_file + file_delta
        if not 0 <= f <= 7:
            continue
        from_sq = chess.square(f, from_rank)
        piece = board.piece_at(from_sq)
        if piece is None or piece.piece_type != chess.PAWN or piece.color != board.turn:
            continue
        candidate = chess.Move(from_sq, board.ep_square)
        if candidate in board.legal_moves:
            continue  # it is legal, so nothing is being suppressed
        # Confirm the pseudo-legal move exists and is only barred by king safety.
        if candidate not in board.generate_pseudo_legal_moves():
            continue
        board.push(candidate)
        # push() does not enforce legality; if our king is attacked afterwards,
        # this is exactly the suppressing-legality case.
        exposed = board.is_attacked_by(not piece.color, board.king(not board.turn))
        board.pop()
        if exposed:
            return True
    return False


def edge_castle_rights_lost_by_rook_capture(board: chess.Board) -> bool:
    """A side has one castling right, the other lost because its rook is gone."""
    for color in (chess.WHITE, chess.BLACK):
        rights = board.castling_rights
        home_rank = 0 if color == chess.WHITE else 7
        king_sq = chess.square(4, home_rank)
        king = board.piece_at(king_sq)
        if king is None or king.piece_type != chess.KING or king.color != color:
            continue
        has_k = bool(rights & chess.BB_SQUARES[chess.square(7, home_rank)])
        has_q = bool(rights & chess.BB_SQUARES[chess.square(0, home_rank)])
        rook_k = board.piece_at(chess.square(7, home_rank))
        rook_q = board.piece_at(chess.square(0, home_rank))
        kingside_rook_there = (
            rook_k is not None and rook_k.piece_type == chess.ROOK and rook_k.color == color
        )
        queenside_rook_there = (
            rook_q is not None and rook_q.piece_type == chess.ROOK and rook_q.color == color
        )
        # One right present with its rook still there, the other absent with no
        # rook: the asymmetry a rook capture produces.
        if has_k and kingside_rook_there and not has_q and not queenside_rook_there:
            return True
        if has_q and queenside_rook_there and not has_k and not kingside_rook_there:
            return True
    return False


def edge_underpromotion_knight_check(board: chess.Board) -> bool:
    """A legal underpromotion to KNIGHT that gives check, and no queen version does."""
    knight_checks = []
    queen_checks = []
    for move in board.legal_moves:
        if not move.promotion:
            continue
        board.push(move)
        gives_check = board.is_check()
        board.pop()
        if not gives_check:
            continue
        if move.promotion == chess.KNIGHT:
            knight_checks.append(move)
        elif move.promotion == chess.QUEEN:
            queen_checks.append(move)
    return bool(knight_checks) and not queen_checks


TARGETS = {
    "ep-check": edge_ep_discovers_check,
    "ep-expose": edge_ep_exposes_king,
    "rook-rights": edge_castle_rights_lost_by_rook_capture,
    "knight-check": edge_underpromotion_knight_check,
}


def build_ep_exposes_king(rng: random.Random) -> chess.Board:
    """Construct the classic ep-exposes-king position directly.

    Both the capturing pawn and the captured pawn stand on one rank, with the
    mover's own king and an enemy rook further along it. The ep capture removes
    both pawns from that rank at once, opening the rook's line onto the king, so
    the capture is pseudo-legal but must not appear in legal moves. Random
    sampling almost never stumbles on this shape, so it is built:

        rank:  rook ... victim(capturer) king
    """
    color = rng.choice([chess.WHITE, chess.BLACK])
    # Rank the two pawns share after the double push.
    action_rank = 4 if color == chess.WHITE else 3
    push_from_rank = 6 if color == chess.WHITE else 1

    victim_file = rng.randrange(2, 6)      # pawn that will be captured ep
    capturer_file = victim_file + 1        # mover's pawn, stands beside it
    rook_file = rng.randrange(0, victim_file)
    king_candidates = [f for f in range(capturer_file + 1, 8)]
    if not king_candidates:
        return None
    king_file = rng.choice(king_candidates)

    board = chess.Board.empty()
    board.set_piece_at(
        chess.square(king_file, action_rank), chess.Piece(chess.KING, color)
    )
    board.set_piece_at(
        chess.square(capturer_file, action_rank), chess.Piece(chess.PAWN, color)
    )
    # Enemy rook on the same rank, beyond the pawns, lining up on our king.
    board.set_piece_at(
        chess.square(rook_file, action_rank), chess.Piece(chess.ROOK, not color)
    )
    # The victim must exist ONLY on its origin square: it reaches the action
    # rank by the double push, which is what creates the ep right. Placing it on
    # the landing square as well blocks its own push.
    push_from = chess.square(victim_file, push_from_rank)
    board.set_piece_at(push_from, chess.Piece(chess.PAWN, not color))
    # Opposing king somewhere harmless: off the action rank, not adjacent.
    while True:
        other_rank = rng.choice([0, 1, 6, 7])
        other_file = rng.randrange(8)
        if other_rank == action_rank:
            continue
        other_sq = chess.square(other_file, other_rank)
        if board.piece_at(other_sq) is not None:
            continue
        if chess.square_distance(other_sq, chess.square(king_file, action_rank)) <= 1:
            continue
        board.set_piece_at(other_sq, chess.Piece(chess.KING, not color))
        break
    board.turn = not color
    board.castling_rights = chess.BB_EMPTY
    board.ep_square = None
    board.halfmove_clock = 0
    if not board.is_valid():
        return None
    push = chess.Move(push_from, chess.square(victim_file, action_rank))
    if push not in board.legal_moves:
        return None
    board.push(push)
    return board


def build_ep_discovers_check(rng: random.Random) -> chess.Board:
    """Construct an ep capture that opens a file for a rook to give check.

    The mover's pawn stands on the file of an enemy king with its own rook behind
    it; the captured pawn stands beside it on the neighbouring file. Taking ep
    moves the capturing pawn off that file and removes the victim, so the rook's
    file is clear and the capture delivers check by discovery, not by the pawn.
    """
    color = rng.choice([chess.WHITE, chess.BLACK])
    action_rank = 4 if color == chess.WHITE else 3
    push_from_rank = 6 if color == chess.WHITE else 1
    back_rank = 0 if color == chess.WHITE else 7
    king_rank = 7 if color == chess.WHITE else 0

    file_in = rng.randrange(1, 7)          # file of the mover's pawn and its rook
    victim_file = file_in + rng.choice([-1, 1])

    board = chess.Board.empty()
    board.set_piece_at(chess.square(file_in, action_rank), chess.Piece(chess.PAWN, color))
    board.set_piece_at(chess.square(file_in, back_rank), chess.Piece(chess.ROOK, color))
    board.set_piece_at(chess.square(file_in, king_rank), chess.Piece(chess.KING, not color))
    # Victim only on its origin; the double push brings it to the action rank.
    push_from = chess.square(victim_file, push_from_rank)
    board.set_piece_at(push_from, chess.Piece(chess.PAWN, not color))
    while True:
        sq = chess.square(rng.randrange(8), rng.choice([0, 1, 6, 7]))
        if board.piece_at(sq) is not None:
            continue
        if chess.square_distance(sq, chess.square(file_in, king_rank)) <= 1:
            continue
        board.set_piece_at(sq, chess.Piece(chess.KING, color))
        break
    board.turn = not color
    board.castling_rights = chess.BB_EMPTY
    board.ep_square = None
    board.halfmove_clock = 0
    if not board.is_valid():
        return None
    push = chess.Move(push_from, chess.square(victim_file, action_rank))
    if push not in board.legal_moves:
        return None
    board.push(push)
    return board


def fen_with_ep(board: chess.Board) -> str:
    """Serialize including the ep square even when no legal ep capture exists.

    python-chess's board.fen() omits the en-passant square when the capture
    would be illegal, which is precisely the ep-exposes-king case. Measured:
    Board("8/8/8/8/k2pP2R/8/8/4K3 b - e3 0 1").fen() returns "... b - -", so a
    position built to test that edge silently loses it on the way to the engine.
    This writer emits the square unconditionally.
    """
    rows = []
    for rank in range(7, -1, -1):
        empty = 0
        row = ""
        for file in range(8):
            piece = board.piece_at(chess.square(file, rank))
            if piece is None:
                empty += 1
                continue
            if empty:
                row += str(empty)
                empty = 0
            row += piece.symbol()
        if empty:
            row += str(empty)
        rows.append(row)
    placement = "/".join(rows)
    ep = "-" if board.ep_square is None else chess.square_name(board.ep_square)
    castling = ""
    if board.castling_rights & chess.BB_H1:
        castling += "K"
    if board.castling_rights & chess.BB_A1:
        castling += "Q"
    if board.castling_rights & chess.BB_H8:
        castling += "k"
    if board.castling_rights & chess.BB_A8:
        castling += "q"
    if not castling:
        castling = "-"
    return (
        f"{placement} {'w' if board.turn == chess.WHITE else 'b'} "
        f"{castling} {ep} {board.halfmove_clock} {board.fullmove_number}"
    )


def targeted_position(rng: random.Random, target: str) -> tuple[str, list[str]]:
    """Sample until `target`'s predicate holds; return that position.

    A mix of random playouts and sparse endgames is sampled, because the three
    edges live in different material regimes: ep needs pawns, underpromotion
    check needs a nearly bare board, rook-rights asymmetry needs both rooks and
    a capture to have happened.
    """
    predicate = TARGETS[target]
    attempts = 0
    while True:
        attempts += 1
        if attempts > 200_000:
            raise RuntimeError(f"targeted_position({target}) found nothing in {attempts} tries")
        if target == "knight-check":
            board = sparse_endgame(rng)
            # A promotion must be reachable: put a pawn one step from the 8th.
            color = rng.choice([chess.WHITE, chess.BLACK])
            promo_rank = 6 if color == chess.WHITE else 1
            sq = chess.square(rng.randrange(8), promo_rank)
            if board.piece_at(sq) is not None:
                continue
            board.set_piece_at(sq, chess.Piece(chess.PAWN, color))
            board.turn = color
            board.castling_rights = chess.BB_EMPTY
            board.ep_square = None
            if not board.is_valid():
                continue
            fen, moves = board.fen(), []
        elif target == "rook-rights":
            # Rebuild a back rank with both rooks, then remove one and its right.
            board = chess.Board.empty()
            color = rng.choice([chess.WHITE, chess.BLACK])
            rank = 0 if color == chess.WHITE else 7
            board.set_piece_at(chess.square(4, rank), chess.Piece(chess.KING, color))
            keep_kingside = rng.random() < 0.5
            keep_sq = chess.square(7 if keep_kingside else 0, rank)
            board.set_piece_at(keep_sq, chess.Piece(chess.ROOK, color))
            board.castling_rights = chess.BB_SQUARES[keep_sq]
            # The other king, so the position is legal.
            other_rank = 7 if color == chess.WHITE else 0
            board.set_piece_at(
                chess.square(rng.randrange(8), other_rank),
                chess.Piece(chess.KING, not color),
            )
            for _ in range(rng.randint(0, 3)):
                sq = chess.square(rng.randrange(8), rng.randrange(8))
                if board.piece_at(sq) is not None:
                    continue
                board.set_piece_at(
                    sq, chess.Piece(rng.choice([chess.KNIGHT, chess.BISHOP, chess.QUEEN]), not color)
                )
            board.turn = color
            board.ep_square = None
            board.halfmove_clock = 0
            if not board.is_valid():
                continue
            fen, moves = board.fen(), []
        elif target in ("ep-check", "ep-expose"):
            builder = build_ep_discovers_check if target == "ep-check" else build_ep_exposes_king
            built = builder(rng)
            if built is None:
                continue
            # fen_with_ep, not fen(): the ep square must survive a position whose
            # ep capture is illegal, which is the whole point of ep-expose.
            fen, moves = fen_with_ep(built), []
        else:
            fen, moves = ep_decorated_position(rng) if rng.random() < 0.6 else _playout(
                rng, sparse_endgame(rng)
            )
        try:
            candidate = chess.Board(fen)
        except ValueError:
            continue
        if not candidate.is_valid():
            continue
        if predicate(candidate):
            return fen, moves


def divide_diff(engine_div: dict[str, int], py_div: dict[str, int]) -> dict:
    """Localisable difference between two divides."""
    keys = sorted(set(engine_div) | set(py_div))
    rows = []
    for key in keys:
        e = engine_div.get(key)
        p = py_div.get(key)
        if e != p:
            rows.append({"move": key, "engine": e, "python": p})
    return {
        "engine_only_moves": sorted(set(engine_div) - set(py_div)),
        "python_only_moves": sorted(set(py_div) - set(engine_div)),
        "differing_children": rows,
    }


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "build-swarm74/forge"
    count = DEFAULT_COUNT
    seed = DEFAULT_SEED
    out_json = None
    if "--count" in sys.argv:
        count = int(sys.argv[sys.argv.index("--count") + 1])
    if "--seed" in sys.argv:
        seed = int(sys.argv[sys.argv.index("--seed") + 1])
    if "--json" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json") + 1]

    rng = random.Random(seed)
    engine = Engine(binary)
    self_test = "--self-test" in sys.argv
    mode = "random"
    if "--biased" in sys.argv:
        mode = "biased"
    if "--castle" in sys.argv:
        mode = "castle"
    if "--ep" in sys.argv:
        mode = "ep"
    target = None
    if "--target" in sys.argv:
        target = sys.argv[sys.argv.index("--target") + 1]
        if target not in TARGETS:
            raise SystemExit(f"unknown --target {target!r}; choose from {sorted(TARGETS)}")
        mode = f"target:{target}"

    compared = 0
    mismatches: list[dict] = []
    refused: list[dict] = []
    total_nodes = 0
    features = {
        "ep_capture_available": 0,
        "ep_right_present": 0,
        "ep_capture_suppressed_illegal": 0,
        "promotion_available": 0,
        "castling_available": 0,
        "side_to_move_in_check": 0,
        "pinned_piece_present": 0,
    }
    started = time.time()

    try:
        for i in range(count):
            if mode == "biased":
                fen, moves = biased_position(rng)
            elif mode == "ep":
                fen, moves = ep_decorated_position(rng)
            elif mode == "castle":
                fen, moves = castling_position(rng)
            elif target is not None:
                fen, moves = targeted_position(rng, target)
            else:
                fen, moves = random_position(rng)
            try:
                board = validate_fen(fen)
                legal_now = list(board.legal_moves)
                # Tag which edges this position actually exercises.
                if any(board.is_en_passant(m) for m in legal_now):
                    features["ep_capture_available"] += 1
                if board.ep_square is not None:
                    features["ep_right_present"] += 1
                    # The ep square is set but no legal ep capture exists: the
                    # suppressed-illegal case, which a count of zero would
                    # otherwise be indistinguishable from "no ep right at all".
                    if not any(board.is_en_passant(m) for m in legal_now):
                        features["ep_capture_suppressed_illegal"] += 1
                if any(m.promotion for m in legal_now):
                    features["promotion_available"] += 1
                if any(board.is_castling(m) for m in legal_now):
                    features["castling_available"] += 1
                if board.is_check():
                    features["side_to_move_in_check"] += 1
                # python-chess's pin mask is all-ones when nothing is pinned, so
                # test pieces individually rather than trusting the mask.
                king_sq = board.king(board.turn)
                pinned = [
                    sq
                    for sq in chess.SquareSet(board.occupied_co[board.turn])
                    if sq != king_sq and board.is_pinned(board.turn, sq)
                ]
                if pinned:
                    features["pinned_piece_present"] += 1
                # Prove the targeted edge held for this position. The generator
                # filtered on it, so a failure here means the predicate and the
                # position drifted apart -- a bug in the harness, not the engine.
                if target is not None and not TARGETS[target](board):
                    refused.append(
                        {
                            "index": i,
                            "fen": fen,
                            "moves": moves,
                            "reason": f"target {target} not live in the generated position",
                        }
                    )
                    continue
                engine.set_position(fen)
                identity = engine.perft(1)
                want1 = len(list(board.legal_moves))
                if identity.nodes != want1:
                    raise FenRejected(
                        f"identity: engine perft 1 {identity.nodes} vs python-chess {want1}"
                    )
                want2 = py_perft(board, 2)
                got2 = engine.perft(2).nodes
                if got2 != want2:
                    raise FenRejected(
                        f"identity: engine perft 2 {got2} vs python-chess {want2}"
                    )
                engine_div = engine.perft(DEPTH)
                py_div = {}
                for move in board.legal_moves:
                    board.push(move)
                    py_div[move.uci()] = py_perft(board, DEPTH - 1)
                    board.pop()
            except (FenRejected, EngineError) as exc:
                refused.append({"index": i, "fen": fen, "moves": moves, "reason": str(exc)})
                continue

            compared += 1
            if self_test and i == 0:
                # Plant a known-bad engine count for this one position and
                # require the comparison below to record it as a mismatch.
                engine_div.nodes += 1
                engine_div.children[next(iter(engine_div.children))] += 1
            total_nodes += engine_div.nodes
            py_total = sum(py_div.values())
            if engine_div.nodes != py_total:
                mismatches.append(
                    {
                        "index": i,
                        "fen": fen,
                        "moves": moves,
                        "engine": engine_div.nodes,
                        "python": py_total,
                        "delta": engine_div.nodes - py_total,
                        "divide": divide_diff(engine_div.children, py_div),
                    }
                )
                print(
                    f"MISMATCH #{len(mismatches)} at index {i}: engine {engine_div.nodes} "
                    f"vs python {py_total} (delta {engine_div.nodes - py_total})"
                )
                print(f"  fen: {fen}")
                for row in mismatches[-1]["divide"]["differing_children"][:12]:
                    print(f"    {row['move']}: engine {row['engine']} python {row['python']}")
            if (i + 1) % 200 == 0:
                elapsed = time.time() - started
                print(
                    f"  ... {i + 1}/{count} generated, {compared} compared, "
                    f"{len(mismatches)} mismatches, {elapsed:.1f}s"
                )

    finally:
        engine.close()

    elapsed = time.time() - started
    print(
        f"\npositions generated: {count} | compared: {compared} | "
        f"mismatches: {len(mismatches)} | engine-refused: {len(refused)} | "
        f"nodes summed: {total_nodes} | {elapsed:.1f}s | seed {seed} | "
        f"mode {mode}"
    )
    print("edge coverage in the compared set:")
    for key, value in features.items():
        print(f"  {key:26s} {value:5d} / {compared}")
    if self_test:
        assert mismatches, "planted bad count produced no mismatch; the fuzz cannot fail"
        assert any(m["divide"]["differing_children"] for m in mismatches), (
            "mismatch was recorded without a localisable divide"
        )
        print(
            "SELF-TEST PASSED: a planted off-by-one engine count is reported as a "
            "mismatch with a localisable divide"
        )
        return 0
    if out_json:
        with open(out_json, "w") as handle:
            json.dump(
                {
                    "seed": seed,
                    "depth": DEPTH,
                    "mode": mode,
                    "generated": count,
                    "compared": compared,
                    "mismatch_count": len(mismatches),
                    "refused_count": len(refused),
                    "nodes_summed": total_nodes,
                    "seconds": round(elapsed, 1),
                    "features": features,
                    "mismatches": mismatches,
                    "refused": refused,
                },
                handle,
                indent=2,
            )
    return 1 if (mismatches or refused) else 0


if __name__ == "__main__":
    sys.exit(main())
