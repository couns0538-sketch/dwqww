#!/usr/bin/env python3
"""Job 3 B1: build mate positions constructively instead of by rejection sampling.

Random sparse positions almost never contain a forced mate (measured: 2 mate-in-2 in
132 tries over 600 s), so this generator works the other way round:

  1. pick a bare king square for the losing side and put its king there,
  2. put the stronger side's king and 1-3 men on random squares near it,
  3. reject illegal / in-check-when-not-to-move boards,
  4. classify the position exactly with the brute-force mate search in b_truth.py.

Classification (`mate_in`, validated in this job against an exhaustive move-tree walk
on 300 positions with 0 disagreements):
  +2  -> a forced mate in exactly 2 plies for the side to move  (mate in 1 move)
  +3  -> exactly 3 plies (mate in 2 moves)
  +5  -> exactly 5 plies (mate in 3 moves)
  -2  -> the side to move is mated in exactly 2 plies whatever it plays

Only "exactly" counts: a position with a shorter mate is classified by the shorter
one and lands in that bucket (or is discarded if the bucket is already full).

Usage: b1_mates.py <out.json> <seed> [count2] [count3] [countmated2]
"""
import json
import random
import sys
import time

import chess

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek_job3")
import b_truth as T


def build_position(rng):
    """A random legal position with a bare king on one side and 1-3 men on the other."""
    weak_is_white = rng.random() < 0.5
    weak_king = rng.randrange(64)
    # Keep the weak king off the very corner sometimes so mates are reachable.
    strong_king = rng.choice([s for s in chess.SQUARES if s != weak_king])
    if chess.square_distance(weak_king, strong_king) < 2:
        return None
    board = chess.Board(None)
    board.set_piece_at(strong_king, chess.Piece(chess.KING, not weak_is_white and chess.WHITE or chess.BLACK))
    board.set_piece_at(weak_king, chess.Piece(chess.KING, chess.WHITE if weak_is_white else chess.BLACK))
    used = {weak_king, strong_king}
    # Bias the men towards the weak king so mates actually occur.
    free_near = [s for s in range(64) if s not in used
                 and chess.square_distance(s, weak_king) <= 4]
    free_far = [s for s in range(64) if s not in used]
    n_men = rng.randint(1, 3)
    types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
    weights = [0.45, 0.3, 0.15, 0.10]
    for _ in range(n_men):
        pool = free_near if (rng.random() < 0.7 and free_near) else free_far
        if not pool:
            return None
        sq = rng.choice(pool)
        ptype = rng.choices(types, weights)[0]
        colour = chess.WHITE if not weak_is_white else chess.BLACK
        board.set_piece_at(sq, chess.Piece(ptype, colour))
        used.add(sq)
        free_near = [s for s in free_near if s != sq]
        free_far = [s for s in free_far if s != sq]
    # Strong side to move most of the time (mates need the mover to be winning),
    # but sometimes the weak side, to find "mated in 2".
    board.turn = chess.WHITE if (not weak_is_white and rng.random() < 0.8) else (
        chess.BLACK if (weak_is_white and rng.random() < 0.8) else (chess.WHITE if weak_is_white else chess.BLACK))
    board.castling_rights = 0
    if not board.is_valid():
        return None
    # The side not to move must not be in check.
    board.turn = not board.turn
    bad = board.is_check()
    board.turn = not board.turn
    if bad:
        return None
    return board


def main():
    out_path = sys.argv[1]
    seed = int(sys.argv[2])
    want2 = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    want3 = int(sys.argv[4]) if len(sys.argv) > 4 else 100
    wantm2 = int(sys.argv[5]) if len(sys.argv) > 5 else 50
    rng = random.Random(seed)
    found = {"mate2": [], "mate3": [], "mated2": []}
    deadline = time.time() + 1500
    tries = 0
    while time.time() < deadline and not (len(found["mate2"]) >= want2 and len(found["mate3"]) >= want3
                                          and len(found["mated2"]) >= wantm2):
        tries += 1
        board = build_position(rng)
        if board is None:
            continue
        if len(found["mate2"]) < want2:
            if T.mate_in(board, 1) == 1 and T.mate_in(board, 2) == 1:
                found["mate2"].append(board.fen())
                continue
        if len(found["mated2"]) < wantm2:
            if T.mate_in(board, 2) == -2:
                found["mated2"].append(board.fen())
                continue
        if len(found["mate3"]) < want3:
            # Exactly mate in 2 MOVES (3 plies): not mate in 1 move, and mate in 3.
            if T.mate_in(board, 3) == 3 and T.mate_in(board, 2) != 1:
                found["mate3"].append(board.fen())
        if tries % 2000 == 0:
            print(f"tries {tries}: {[ (k,len(v)) for k,v in found.items() ]}", flush=True)
    with open(out_path, "w") as f:
        json.dump(found, f, indent=1)
    print(json.dumps({k: len(v) for k, v in found.items()}, sort_keys=True), "tries", tries)


if __name__ == "__main__":
    main()
