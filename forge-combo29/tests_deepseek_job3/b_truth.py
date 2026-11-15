#!/usr/bin/env python3
"""Job 3 part B: ground truth by brute force with python-chess.

Everything here is computed from the full game tree, not from an engine.

Mate distances
  A position is "mate in exactly N for the side to move" when the side to move has a
  move leading to a forced mate in N plies and has no shorter forced mate, i.e. the
  game-theoretic value is a win in exactly N plies. Computed with a plain negamax
  over the game tree with these rules kept:
    * a position with no legal moves is mate (0 plies to mate, losing side to move)
      or stalemate (draw),
    * the fifty-move counter and threefold repetition are NOT modelled here; the
      generator only keeps positions whose full tree to the needed depth contains no
      capture-free / pawn-free long line that would hit the fifty-move rule, and B4
      tests the fifty-move rule separately,
    * insufficient material is a draw.
  "Mated in exactly N" means the side to move loses in exactly N plies with best play.

The search returns a signed "plies to mate" value: positive = the side to move mates
in that many plies, negative = the side to move is mated, None = draw/unknown.

Usage: b_truth.py <command> [args]
  mates <count2> <count3> <countmated2> <out.json> <seed>
  material <count> <out.json> <seed>
  stalemate <count> <out.json> <seed>
  special <minutes> <out.json> <seed>
"""
import json
import random
import sys
import time

import chess

INF = 10 ** 9


def material_key(board):
    """(has_pawns_or_major_or_minor) helper: insufficient material as python-chess sees it."""
    return board.is_insufficient_material()


def mate_in(board, depth):
    """Signed plies-to-mate with `board` to move, searched to `depth` plies.

    Returns +n (side to move mates in n plies), -n (side to move is mated in n),
    0 for a proven draw inside the window, or None if undecided at this depth.

    A position that is already checkmate means the side to move has ALREADY been
    mated - it has no move, and the mate was delivered by the previous ply. At the
    root that is reported as -1 (mated in one ply); inside the tree the caller
    converts it directly (it sees is_checkmate() after pushing its move), so this
    value is only used for the root and for clarity.

    Standard mate search: the side to move prefers the SMALLEST positive value, the
    opponent prefers the LARGEST negative value; a draw (0) beats being mated and is
    worse than mating.
    """
    if board.is_checkmate():
        return -1                     # the side to move is already mated
    if board.is_stalemate() or board.is_insufficient_material():
        return 0                      # terminal draw
    if depth == 0:
        return None                   # undecided at this depth
    values = []
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            board.pop()
            values.append(1)          # this move mates immediately
            continue
        sub = mate_in(board, depth - 1)
        board.pop()
        if sub is None:
            values.append(None)
            continue
        if sub == 0:
            values.append(0)
        elif sub > 0:
            values.append(-(sub + 1))   # opponent mates us in sub+1 plies
        else:
            values.append((-sub) + 1)   # opponent is mated: we mate in that many plies
    return choose_value(values)


def choose_value(values):
    """The side to move's best value among child values (already negated for them).

    `None` means "undecided at this depth" and it DOMINATES the negative verdicts: a
    side that still has an unexamined move cannot be called mated. (An earlier version
    of this function skipped the Nones, which made every position with one unexplored
    escape look like a forced loss and produced false mates - caught by cross-checking
    against an exhaustive move-tree walk.)
    """
    if not values:
        return 0
    # A win is claimed only when it is really there; take the quickest.
    wins = [v for v in values if v is not None and v > 0]
    if wins:
        return min(wins)
    # No win: if any escape is still undecided, this node is undecided too.
    if any(v is None for v in values):
        return None
    # All moves are decided: a draw beats being mated.
    if any(v == 0 for v in values):
        return 0
    # Only losses: take the longest.
    return max(values)


def mate_in_exact(board, n):
    """True iff the side to move has a forced mate in exactly n plies (no shorter)."""
    if n < 1:
        return False
    # Must have a mate in n...
    v = mate_in(board, n)
    if v != n:
        return False
    # ...and none shorter.
    if n > 1:
        shorter = mate_in(board, n - 2)
        if shorter is not None and shorter > 0:
            return False
    return True


def mated_in_exact(board, n):
    """True iff the side to move is mated in exactly n plies whatever it plays."""
    if n < 2:
        return False
    v = mate_in(board, n)
    if v != -n:
        return False
    if n > 2:
        shorter = mate_in(board, n - 2)
        if shorter is not None and shorter < 0:
            return False
    return True


def random_position(rng, min_pieces, max_pieces):
    """A random legal, non-terminal position with the given piece-count range."""
    for _ in range(20000):
        target = rng.randint(min_pieces, max_pieces)
        board = chess.Board(None)
        squares = rng.sample(range(64), target)
        wk, bk = squares[0], squares[1]
        if chess.square_distance(wk, bk) < 2:
            continue
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        pool = ([chess.Piece(t, chess.WHITE) for t in
                 [chess.PAWN] * 8 + [chess.KNIGHT] * 2 + [chess.BISHOP] * 2 + [chess.ROOK] * 2 + [chess.QUEEN]]
                + [chess.Piece(t, chess.BLACK) for t in
                   [chess.PAWN] * 8 + [chess.KNIGHT] * 2 + [chess.BISHOP] * 2 + [chess.ROOK] * 2 + [chess.QUEEN]])
        rng.shuffle(pool)
        ok = True
        for sq, piece in zip(squares[2:], pool):
            if piece.piece_type == chess.PAWN and chess.square_rank(sq) in (0, 7):
                ok = False
                break
            board.set_piece_at(sq, piece)
        if not ok:
            continue
        board.turn = rng.choice([chess.WHITE, chess.BLACK])
        board.castling_rights = 0
        board.turn = not board.turn
        if board.is_check():
            continue
        board.turn = not board.turn
        if not board.is_valid() or board.is_game_over():
            continue
        return board
    return None


def cmd_mates(count2, count3, countmated2, out_path, seed):
    rng = random.Random(seed)
    found = {"mate2": [], "mate3": [], "mated2": []}
    deadline = time.time() + 600
    tries = 0
    while (len(found["mate2"]) < count2 or len(found["mate3"]) < count3
           or len(found["mated2"]) < countmated2) and time.time() < deadline:
        tries += 1
        board = random_position(rng, 3, 7)
        if board is None:
            continue
        fen = board.fen()
        if len(found["mate2"]) < count2 and mate_in_exact(board, 3):
            found["mate2"].append(fen)
            continue
        if len(found["mated2"]) < countmated2 and mated_in_exact(board, 2):
            found["mated2"].append(fen)
            continue
        if len(found["mate3"]) < count3 and mate_in_exact(board, 5):
            found["mate3"].append(fen)
    with open(out_path, "w") as f:
        json.dump(found, f, indent=1)
    print(json.dumps({k: len(v) for k, v in found.items()}, sort_keys=True), "tries", tries)


def cmd_material(count, out_path, seed):
    """K+B vs K and K+N vs K, both colours, various squares; all are dead draws.

    Note: these positions are `is_game_over()` by definition (insufficient material),
    so unlike the other generators this one does NOT filter on !is_game_over() - B2
    asks for exactly these dead-drawn positions. It still requires a valid board, the
    kings not adjacent, and the side not to move not in check.
    """
    rng = random.Random(seed)
    fens = []
    piece_types = [chess.BISHOP, chess.KNIGHT]
    while len(fens) < count:
        wk, bk = rng.sample(range(64), 2)
        if chess.square_distance(wk, bk) < 2:
            continue
        strong = rng.choice([chess.WHITE, chess.BLACK])
        piece_type = rng.choice(piece_types)
        free = [s for s in range(64) if s not in (wk, bk)]
        psq = rng.choice(free)
        board = chess.Board(None)
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        board.set_piece_at(psq, chess.Piece(piece_type, strong))
        board.turn = rng.choice([chess.WHITE, chess.BLACK])
        board.castling_rights = 0
        # The side NOT to move must not be in check (else the position is illegal).
        board.turn = not board.turn
        if board.is_check():
            continue
        board.turn = not board.turn
        if not board.is_valid():
            continue
        if not board.is_insufficient_material():
            continue
        fens.append(board.fen())
    with open(out_path, "w") as f:
        json.dump(fens, f, indent=1)
    print(json.dumps({"written": len(fens)}))


def cmd_stalemate(count, out_path, seed):
    """K+Q v K with the queen side to move and at least one move that stalemates."""
    rng = random.Random(seed)
    out = []
    attempts = 0
    while len(out) < count and attempts < 400000:
        attempts += 1
        wk, bk, qsq = rng.sample(range(64), 3)
        if chess.square_distance(wk, bk) < 2:
            continue
        board = chess.Board(None)
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        board.set_piece_at(qsq, chess.Piece(chess.QUEEN, chess.WHITE))
        board.turn = chess.WHITE          # queen side to move
        board.castling_rights = 0
        if not board.is_valid() or board.is_game_over():
            continue
        # The black king must not already be in check, and moving must be black's problem.
        if board.is_check():
            continue
        stale_moves = []
        for move in board.legal_moves:
            board.push(move)
            if board.is_stalemate():
                stale_moves.append(move.uci())
            board.pop()
        if not stale_moves:
            continue
        out.append({"fen": board.fen(), "stalemating_moves": stale_moves})
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"written": len(out), "attempts": attempts}))


def cmd_special(minutes, out_path, seed):
    """Mate-in-one positions where the ONLY mating move is en passant / castling / promotion."""
    rng = random.Random(seed)
    deadline = time.time() + minutes * 60
    found = {"en_passant": [], "castling": [], "promotion": []}
    attempts = 0
    while time.time() < deadline:
        attempts += 1
        board = random_position(rng, 3, 12)
        if board is None:
            continue
        mating = []
        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate():
                mating.append(move)
            board.pop()
        if len(mating) != 1:
            continue
        move = mating[0]
        kind = None
        if board.is_en_passant(move):
            kind = "en_passant"
        elif board.is_castling(move):
            kind = "castling"
        elif move.promotion is not None:
            kind = "promotion"
        if kind is None:
            continue
        if len(found[kind]) >= 20:
            continue
        found[kind].append({"fen": board.fen(), "mating_move": move.uci(),
                            "promotion_piece": chess.piece_name(move.promotion) if move.promotion else None})
        if all(len(found[k]) >= 20 for k in found):
            break
    with open(out_path, "w") as f:
        json.dump({k: {"count": len(v), "positions": v} for k, v in found.items()}, f, indent=1)
    print(json.dumps({k: len(v) for k, v in found.items()}, sort_keys=True), "attempts", attempts)


def main():
    command = sys.argv[1]
    if command == "mates":
        cmd_mates(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], int(sys.argv[6]))
    elif command == "material":
        cmd_material(int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
    elif command == "stalemate":
        cmd_stalemate(int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
    elif command == "special":
        cmd_special(float(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
    else:
        raise SystemExit(f"unknown command {command}")


if __name__ == "__main__":
    main()
