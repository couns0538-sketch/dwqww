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

    compared = 0
    mismatches: list[dict] = []
    refused: list[dict] = []
    total_nodes = 0
    features = {
        "ep_capture_available": 0,
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
            else:
                fen, moves = random_position(rng)
            try:
                board = validate_fen(fen)
                legal_now = list(board.legal_moves)
                # Tag which edges this position actually exercises.
                if any(board.is_en_passant(m) for m in legal_now):
                    features["ep_capture_available"] += 1
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
