#!/usr/bin/env python3
"""Job 10: 300 mate-in-2-moves and 300 mate-in-3-moves positions with a UNIQUE key move.

The brute-force classifier alone is far too slow here (55 ms per candidate, and most
candidates fail), so the ENGINE is used as a filter and brute force as the judge:

  1. build a random sparse position (as in jobs 3/4);
  2. filter: the engine at `MultiPV 8, go depth 8` must report a mate for line 1, and the
     engine's mate distance tells us which class it may belong to;
  3. judge, for every survivor, with brute force (`b_truth.mate_in`): the position is kept
     only if it is a mate in exactly 3 plies (2 moves) or exactly 5 plies (3 moves) AND
     exactly one legal move keeps that shortest mate.

The engine never decides the class or the key move; it only saves brute-force calls. Every
kept position is therefore brute-force verified.

Usage: j10_fast.py <out.json> <seed>
"""
import json
import random
import sys
import time

import chess

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek_job3")
import b_truth as T
sys.path.insert(0, "/tmp/ds")
from j10engine import Engine


def build_position(rng):
    weak_is_white = rng.random() < 0.5
    weak_king = rng.randrange(64)
    strong_king = rng.choice([s for s in chess.SQUARES if s != weak_king])
    if chess.square_distance(weak_king, strong_king) < 2:
        return None
    board = chess.Board(None)
    colour = chess.BLACK if weak_is_white else chess.WHITE
    board.set_piece_at(strong_king, chess.Piece(chess.KING, colour))
    board.set_piece_at(weak_king, chess.Piece(chess.KING, not colour))
    used = {weak_king, strong_king}
    free_near = [s for s in range(64) if s not in used
                 and chess.square_distance(s, weak_king) <= 4]
    free_far = [s for s in range(64) if s not in used]
    types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
    weights = [0.45, 0.30, 0.15, 0.10]
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
    return None if bad else board


def key_moves(board, plies):
    out = []
    for m in board.legal_moves:
        board.push(m)
        if plies == 1:
            ok = board.is_checkmate()
        elif board.is_checkmate():
            ok = False
        else:
            ok = T.mate_in(board, plies - 1) == -(plies - 1)
        board.pop()
        if ok:
            out.append(m.uci())
    return out


def main():
    out_path, seed = sys.argv[1], int(sys.argv[2])
    rng = random.Random(seed)
    eng = Engine(threads=1, hash_mb=16, multipv=8)
    found = {"mate2": [], "mate3": []}
    want = {"mate2": 300, "mate3": 300}
    dropped_nonunique = 0
    dropped_class = 0
    engineered = 0
    t0 = time.time()
    while len(found["mate2"]) < want["mate2"] or len(found["mate3"]) < want["mate3"]:
        board = build_position(rng)
        if board is None:
            continue
        fen = board.fen()
        eng.send("ucinewgame")
        eng.send(f"position fen {fen}")
        eng.send("go depth 6")
        # collect line-1 mate scores per depth
        best_mate = None
        while True:
            line = eng.get(0.5)
            if line is None:
                break
            if line.startswith("bestmove"):
                break
            if " multipv 1 " in line and " score mate " in line:
                try:
                    best_mate = abs(int(line.split(" score mate ")[1].split()[0]))
                except (IndexError, ValueError):
                    pass
        if best_mate is None:
            continue
        # The engine's mate distance is in MOVES; 2 -> 3 plies, 3 -> 5 plies.
        cls = {2: "mate2", 3: "mate3"}.get(best_mate)
        if cls is None or len(found[cls]) >= want[cls]:
            continue
        engineered += 1
        plies = 3 if cls == "mate2" else 5
        if T.mate_in(board, plies) != plies:
            dropped_class += 1
            continue
        keys = key_moves(board, plies)
        if len(keys) != 1:
            dropped_nonunique += 1
            continue
        found[cls].append({"fen": fen, "key": keys[0], "plies": plies,
                           "men": len(board.piece_map())})
        n2, n3 = len(found["mate2"]), len(found["mate3"])
        if (n2 + n3) % 25 == 0:
            print(f"  mate2 {n2} mate3 {n3}  ({time.time()-t0:.0f}s)", flush=True)
    eng.close()
    json.dump(found, open(out_path, "w"), indent=1)
    print(json.dumps({"mate2": len(found["mate2"]), "mate3": len(found["mate3"]),
                      "engine_mate_positions_judged": engineered,
                      "dropped_nonunique": dropped_nonunique,
                      "dropped_wrong_class": dropped_class,
                      "seconds": round(time.time() - t0, 1)}))


if __name__ == "__main__":
    main()
