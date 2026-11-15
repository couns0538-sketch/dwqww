#!/usr/bin/env python3
"""Job 3 proof (c) and (d): identical play, and proof that the comparison can fail.

Plays a fixed set of games engine-vs-itself at `go nodes 20000`, one process per
game, replaying the moves and asking the engine for a move at every turn.  A
game stops at a terminal position, at 300 plies, or at a third occurrence (the
same rule a match program uses, so R1 can never act).

Two or more configurations are compared move-by-move; the script reports, per
pair, how many games differ and the first differing move of the first such game.
"""

import json
import queue
import subprocess
import sys
import threading
import time
from multiprocessing import Pool

import chess


HASH_MB = 16


def make_engine(path):
    p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()

    def reader():
        for ln in p.stdout:
            q.put(ln.rstrip())
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(s):
        try:
            p.stdin.write(s + "\n")
            p.stdin.flush()
        except Exception:
            pass

    def until(tok, limit=60.0):
        t0 = time.time()
        got = []
        while time.time() - t0 < limit:
            try:
                ln = q.get(timeout=max(0.01, limit - (time.time() - t0)))
            except queue.Empty:
                break
            if ln is None:
                break
            got.append(ln)
            if ln.startswith(tok):
                return got
        return got

    send("uci")
    until("uciok", 10)
    send("setoption name Threads value 1")
    send(f"setoption name Hash value {HASH_MB}")
    send("setoption name OwnBook value false")
    send("isready")
    until("readyok", 10)
    return p, send, until


def play_game(engine_path, start_fen, max_plies=300):
    p, send, until = make_engine(engine_path)
    board = chess.Board(start_fen)
    moves = []
    try:
        while len(moves) < max_plies:
            if board.is_game_over(claim_draw=True):
                break
            # the match-program rule: a third occurrence ends the game
            if board.can_claim_threefold_repetition():
                break
            send("position fen " + start_fen + (" moves " + " ".join(moves) if moves else ""))
            send("go nodes 20000")
            lines = until("bestmove", 120)
            best = None
            for ln in lines:
                if ln.startswith("bestmove"):
                    best = ln.split()[1]
            if best is None or best == "0000":
                break
            mv = chess.Move.from_uci(best)
            if mv not in board.legal_moves:
                break
            moves.append(best)
            board.push(mv)
    finally:
        send("quit")
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
    return moves


def play_pair(args):
    """Play the same opening with both engines; return (game, moves_a, moves_b)."""
    i, fen, engine_a, engine_b, hash_mb = args
    global HASH_MB
    HASH_MB = hash_mb
    return i, play_game(engine_a, fen), play_game(engine_b, fen)


def main():
    engine_a = sys.argv[1]      # unpatched
    engine_b = sys.argv[2]      # patched
    epd = sys.argv[3]
    games = int(sys.argv[4]) if len(sys.argv) > 4 else 400
    out = sys.argv[5]
    workers = int(sys.argv[6]) if len(sys.argv) > 6 else 4
    global HASH_MB
    if len(sys.argv) > 7:
        HASH_MB = int(sys.argv[7])

    openings = []
    with open(epd, errors="ignore") as f:
        for line in f:
            # EPD: "<board> <side> <castling> <ep> ;" -- take the FEN part only.
            head = line.split(";")[0].split()
            if len(head) < 4:
                continue
            openings.append(" ".join(head[:4]) + " 0 1")
            if len(openings) >= games:
                break
    if len(openings) < games:
        print(f"only {len(openings)} openings in the file, playing that many")
    n = min(games, len(openings))

    results = {"games": n, "a": [None] * n, "b": [None] * n}
    t0 = time.time()
    done = 0
    with Pool(workers) as pool:
        for i, ga, gb in pool.imap_unordered(
                play_pair, [(i, openings[i], engine_a, engine_b, HASH_MB) for i in range(n)],
                chunksize=1):
            results["a"][i] = ga
            results["b"][i] = gb
            done += 1
            if done % 25 == 0:
                print(f"{done}/{n} games, {time.time()-t0:.0f}s", flush=True)
            json.dump(results, open(out, "w"))     # checkpoint every game
    json.dump(results, open(out, "w"))
    diff = 0
    first = None
    for i, (ga, gb) in enumerate(zip(results["a"], results["b"])):
        if ga != gb:
            diff += 1
            if first is None:
                for k, (ma, mb) in enumerate(zip(ga, gb)):
                    if ma != mb:
                        first = {"game": i, "fen": openings[i], "ply": k + 1,
                                 "unpatched": ma, "patched": mb}
                        break
                else:
                    first = {"game": i, "fen": openings[i],
                             "ply": min(len(ga), len(gb)) + 1,
                             "unpatched": ga[len(gb):] or "<ended>",
                             "patched": gb[len(ga):] or "<ended>"}
    print(f"games {n}; games that differ {diff}; first difference {first}")


if __name__ == "__main__":
    main()
