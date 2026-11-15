#!/usr/bin/env python3
"""Job 11 step 2: positions with a SET of right answers (no uniqueness filter).

A right answer is any move that keeps the shortest forced mate. The SET is recorded for
each position, so a stopped search can be judged as "in the set" rather than "is the one
key move".

Adds mate-in-2 first (cheap) and mate-in-3 only while it stays cheap, stopping at 200
positions or at the time limit, whichever comes first - as the job says.

Also records, per position, the depth at which `go depth N` (one thread, one line) first
prints the mate.

Usage: j11_positions.py <out.json> <seed> <seconds>
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
    near = [s for s in range(64) if s not in used and chess.square_distance(s, weak_king) <= 4]
    far = [s for s in range(64) if s not in used]
    types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
    weights = [0.45, 0.30, 0.15, 0.10]
    for _ in range(rng.randint(1, 3)):
        pool = near if (rng.random() < 0.7 and near) else far
        if not pool:
            return None
        sq = rng.choice(pool)
        board.set_piece_at(sq, chess.Piece(rng.choices(types, weights)[0], colour))
        used.add(sq)
        near = [s for s in near if s != sq]
        far = [s for s in far if s != sq]
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


def answer_set(board, plies):
    """Every move that keeps a mate in exactly `plies` plies."""
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


def first_mate_depth(eng, fen):
    eng.send("ucinewgame")
    eng.send(f"position fen {fen}")
    eng.send("go depth 12")
    while True:
        line = eng.get(20)
        if line is None:
            return None
        if line.startswith("bestmove"):
            return None
        if " score mate " in line and " depth " in line:
            try:
                return int(line.split(" depth ")[1].split()[0])
            except (IndexError, ValueError):
                return None


def main():
    out_path, seed, seconds = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    rng = random.Random(seed)
    eng = Engine(threads=1, hash_mb=16, multipv=1)
    found = []
    t0 = time.time()
    yield_probe_start = time.time()
    probe_n = 0
    probe_candidates = 0
    while len(found) < 200 and time.time() - t0 < seconds:
        board = build_position(rng)
        if board is None:
            continue
        probe_candidates += 1
        # mate in 2 moves (3 plies) first, then mate in 3 (5 plies) if still cheap
        cls = None
        plies = None
        if T.mate_in(board, 3) == 3:
            cls, plies = "mate2", 3
        elif (time.time() - yield_probe_start) < seconds * 0.6 and T.mate_in(board, 5) == 5:
            cls, plies = "mate3", 5
        if cls is None:
            continue
        answers = answer_set(board, plies)
        if not answers:
            continue
        fen = board.fen()
        depth = first_mate_depth(eng, fen)
        found.append({"fen": fen, "answers": answers, "class": cls, "plies": plies,
                      "mate_depth": depth, "men": len(board.piece_map())})
        if len(found) % 25 == 0:
            print(f"  {len(found)} positions ({time.time()-t0:.0f}s): "
                  f"mate2 {sum(1 for f in found if f['class']=='mate2')} "
                  f"mate3 {sum(1 for f in found if f['class']=='mate3')}", flush=True)
    eng.close()
    json.dump(found, open(out_path, "w"), indent=1)
    print(json.dumps({"positions": len(found),
                      "mate2": sum(1 for f in found if f["class"] == "mate2"),
                      "mate3": sum(1 for f in found if f["class"] == "mate3"),
                      "candidates_considered": probe_candidates,
                      "seconds": round(time.time() - t0, 1),
                      "yield_per_100_candidates": round(100.0 * len(found) / max(probe_candidates, 1), 2)}))


if __name__ == "__main__":
    main()
