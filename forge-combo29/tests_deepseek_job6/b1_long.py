#!/usr/bin/env python3
"""Job 6 part B1: long games under the ASan+UBSan build.

Ten games each of 300, 1,000 and 3,000 plies, given as `position startpos moves ...`,
then `go depth 8`. Expected: a legal bestmove, exit code 0, nothing on stderr.

Games are random legal moves from a seed; a game that python-chess calls over (mate or
stalemate) is replaced by the next seed.

Usage: b1_long.py <engine> <outdir> <seed>
"""
import json
import os
import random
import subprocess
import sys
import time

import chess


def make_game(plies, rng):
    board = chess.Board()
    moves = []
    for _ in range(plies):
        legal = list(board.legal_moves)
        if not legal:
            return None
        # python-chess will not stop us for 50 moves or repetition; only mate/stalemate
        # make `legal` empty.
        m = rng.choice(legal)
        board.push(m)
        moves.append(m.uci())
        if board.is_checkmate() or board.is_stalemate():
            return None
    return moves


def main():
    engine, outdir, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(seed)
    results = []
    for plies in (300, 1000, 3000):
        got = 0
        attempts = 0
        while got < 10 and attempts < 200:
            attempts += 1
            moves = make_game(plies, rng)
            if moves is None:
                continue
            got += 1
            script = ("setoption name Threads value 1\n"
                      "setoption name Hash value 16\n"
                      "setoption name NNUEArch value false\n"
                      f"position startpos moves {' '.join(moves)}\n"
                      "go depth 8\n")
            t0 = time.time()
            proc = subprocess.run([engine], input=script, capture_output=True, text=True,
                                  timeout=900)
            wall = time.time() - t0
            best = [l for l in proc.stdout.splitlines() if l.startswith("bestmove")]
            bestmove = best[-1].split()[1] if best else None
            # Legality: replay and check the move is legal in the final position.
            board = chess.Board()
            for u in moves:
                board.push(chess.Move.from_uci(u))
            legal = False
            if bestmove and bestmatch_ok(bestmove):
                try:
                    legal = chess.Move.from_uci(bestmove) in board.legal_moves
                except ValueError:
                    legal = False
            results.append({"plies": plies, "attempt": attempts, "wall_s": round(wall, 1),
                            "exit_code": proc.returncode, "bestmove": bestmove,
                            "legal": legal, "stderr_bytes": len(proc.stderr),
                            "stderr_head": proc.stderr[:300]})
            print(json.dumps({"plies": plies, "exit": proc.returncode, "legal": legal,
                              "stderr": len(proc.stderr)}), flush=True)
    with open(os.path.join(outdir, "B1-long-games.json"), "w") as f:
        json.dump(results, f, indent=1)


def bestmatch_ok(text):
    return len(text) >= 4


if __name__ == "__main__":
    main()
