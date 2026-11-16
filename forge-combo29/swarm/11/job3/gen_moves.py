#!/usr/bin/env python3
"""gen_moves.py SEED N OUT — a legal UCI move list of N plies that never ENDS the game.

Why the simple "random legal move" version fails: a random game dies by mate, stalemate or
insufficient material long before 1,000 plies (my first attempts reached 456 and 212 plies
after 200k-300k backtracks). So this generator plays a *shuffling* game: at each ply it tries
the legal moves in a deliberately ordered list that keeps material on the board.

Order of preference at each ply (first move that does not end the game wins):
  1. a quiet (non-capture) move by a rook, then by a king, to a square the opponent does not
     attack — this is the move class that can be repeated forever;
  2. any other non-capture;
  3. a capture (last resort: it changes material and shortens the game).
"Ends" = python-chess `is_game_over(claim_draw=False)`, i.e. mate, stalemate,
insufficient material, or the seventy-five-move rule. Repetition is allowed on purpose: a
threefold is a claim, not an automatic end.
"""
import random, sys, chess

seed, n, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rng = random.Random(seed)
board = chess.Board()
moves = []
backtracks = 0
MAX_BACKTRACKS = 100000


def preference(m):
    """Sort key: lower is tried first."""
    piece = board.piece_at(m.from_square)
    ptype = piece.piece_type if piece else chess.PAWN
    capture = board.is_capture(m)
    # attacked-by-opponent test: after the move, the mover is the side that just moved
    tmp = board.copy()
    tmp.push(m)
    mover = not tmp.turn
    attacked = tmp.is_attacked_by(mover, m.to_square)
    key = 0
    if capture:
        key += 100
    if ptype in (chess.ROOK,):
        key += 0
    elif ptype == chess.KING:
        key += 1
    elif ptype == chess.QUEEN:
        key += 2
    elif ptype == chess.KNIGHT:
        key += 3
    elif ptype == chess.BISHOP:
        key += 4
    else:  # pawn
        key += 10
    if attacked:
        key += 50
    return key


while len(moves) < n and backtracks < MAX_BACKTRACKS:
    legal = list(board.legal_moves)
    rng.shuffle(legal)
    legal.sort(key=preference)
    picked = None
    for m in legal:
        board.push(m)
        if board.is_game_over(claim_draw=False):
            board.pop()
            continue
        picked = m
        break
    if picked is None:
        if not moves:
            sys.exit("no legal non-ending first move")
        board.pop()
        moves.pop()
        backtracks += 1
        continue
    moves.append(picked.uci())

if len(moves) < n:
    sys.exit(f"only reached {len(moves)} plies after {backtracks} backtracks")

with open(out, "w") as f:
    f.write("\n".join(moves) + "\n")
print(f"wrote {len(moves)} plies, backtracks {backtracks}")
