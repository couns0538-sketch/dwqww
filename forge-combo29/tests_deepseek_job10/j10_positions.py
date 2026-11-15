#!/usr/bin/env python3
"""Job 10: 300 forced mates in exactly 2 moves and 300 in exactly 3, with a UNIQUE key move.

Key move = a move that keeps the shortest mate. The position is kept only if exactly ONE
legal move does that, so "played the key move" is unambiguous.

Classification uses the brute-force mate search validated in jobs 3/4 (b_truth.py):
  mate_in(board, n) returns signed plies-to-mate, +n = the side to move mates in n plies.
  mate in 2 MOVES = +3 plies; mate in 3 MOVES = +5 plies.

Positions are built outward, as in jobs 3/4: a bare king for the loser plus a few men.

Usage: j10_positions.py <out.json> <seed>
"""
import json
import time
import random
import sys

import chess

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek_job3")
import b_truth as T


def build_position(rng):
    weak_is_white = rng.random() < 0.5
    weak_king = rng.randrange(64)
    strong_king = rng.choice([s for s in chess.SQUARES if s != weak_king])
    if chess.square_distance(weak_king, strong_king) < 2:
        return None
    board = chess.Board(None)
    board.set_piece_at(strong_king, chess.Piece(chess.KING,
                                                chess.BLACK if weak_is_white else chess.WHITE))
    board.set_piece_at(weak_king, chess.Piece(chess.KING,
                                             chess.WHITE if weak_is_white else chess.BLACK))
    used = {weak_king, strong_king}
    free_near = [s for s in range(64) if s not in used
                 and chess.square_distance(s, weak_king) <= 4]
    free_far = [s for s in range(64) if s not in used]
    types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
    weights = [0.45, 0.30, 0.15, 0.10]
    colour = chess.BLACK if weak_is_white else chess.WHITE
    for _ in range(rng.randint(1, 3)):
        pool = free_near if (rng.random() < 0.7 and free_near) else free_far
        if not pool:
            return None
        sq = rng.choice(pool)
        board.set_piece_at(sq, chess.Piece(rng.choices(types, weights)[0], colour))
        used.add(sq)
        free_near = [s for s in free_near if s != sq]
        free_far = [s for s in free_far if s != sq]
    board.turn = colour
    board.castling_rights = 0
    board.ep_square = None
    board.halfmove_clock = 0
    if not board.is_valid():
        return None
    board.turn = not board.turn
    bad = board.is_check()
    board.turn = not board.turn
    if bad:
        return None
    return board


def key_moves(board, plies):
    """All moves that keep a mate in exactly `plies` plies (the shortest)."""
    out = []
    for m in board.legal_moves:
        board.push(m)
        if plies == 1:
            ok = board.is_checkmate()
        elif board.is_checkmate():
            ok = False          # a shorter mate: not the key move for this class
        else:
            ok = T.mate_in(board, plies - 1) == -(plies - 1)
        board.pop()
        if ok:
            out.append(m.uci())
    return out


def main():
    out_path, seed = sys.argv[1], int(sys.argv[2])
    rng = random.Random(seed)
    targets = {"mate2": 300, "mate3": 300}
    plies = {"mate2": 3, "mate3": 5}
    found = {"mate2": [], "mate3": []}
    dropped_nonunique = 0
    dropped_other = 0
    tries = 0
    t0 = time.time()
    while (len(found["mate2"]) < targets["mate2"] or len(found["mate3"]) < targets["mate3"]):
        tries += 1
        if tries > 600000:
            break
        board = build_position(rng)
        if board is None:
            continue
        # Try mate2 first only while it needs positions, then mate3, independently:
        # a candidate is classified once and never starves the other bucket.
        order = [c for c in ("mate2", "mate3") if len(found[c]) < targets[c]]
        for cls in order:
            p = plies[cls]
            v = T.mate_in(board, p)
            if v != p:
                continue
            if p == 5 and T.mate_in(board, 3) == 3:
                dropped_other += 1
                break          # it is a mate in 2 moves, not 3: wrong bucket
            keys = key_moves(board, p)
            if len(keys) != 1:
                dropped_nonunique += 1
                break
            found[cls].append({"fen": board.fen(), "key": keys[0], "plies": p,
                               "men": len(board.piece_map())})
            break
        if tries % 2000 == 0:
            print(f"  tries {tries} ({time.time()-t0:.0f}s): mate2 {len(found['mate2'])} "
                  f"mate3 {len(found['mate3'])}", flush=True)
    json.dump(found, open(out_path, "w"), indent=1)
    print(json.dumps({"mate2": len(found["mate2"]), "mate3": len(found["mate3"]),
                      "tries": tries, "dropped_nonunique": dropped_nonunique,
                      "dropped_shorter_mate": dropped_other}))


if __name__ == "__main__":
    main()
