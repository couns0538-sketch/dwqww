#!/usr/bin/env python3
"""Job 4 part D: the identity proof, rebuilt as a hash plus a length assertion.

Plays N games engine-vs-itself at `go nodes 20000`, one process per game, from the
UHO openings, then
  * asserts no game is shorter than MIN_PLIES (a silent "both sides empty" pass is
    impossible),
  * prints ONE sha256 over all move lists of each side, and
  * compares the two sides: equal hashes mean identical play.

Two invocations with different engines are compared by their hash lines.  The
power line is the same comparison with `Hash` changed on one side.
"""

import hashlib
import json
import queue
import subprocess
import sys
import threading
import time
from multiprocessing import Pool

import chess

GO = "go nodes 20000"
MIN_PLIES = 20
MAX_PLIES = 300
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

    def until(tok, limit=120.0):
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


def play_game(path, start_fen):
    p, send, until = make_engine(path)
    board = chess.Board(start_fen)
    moves = []
    try:
        while len(moves) < MAX_PLIES:
            if board.is_game_over(claim_draw=True) or board.can_claim_threefold_repetition():
                break
            send("position fen " + start_fen + (" moves " + " ".join(moves) if moves else ""))
            send(GO)
            lines = until("bestmove", 180)
            best = None
            for ln in lines:
                if ln.startswith("bestmove"):
                    best = ln.split()[1]
            if not best or best == "0000":
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
    i, fen, engine = args
    return i, play_game(engine, fen)


def main():
    engine = sys.argv[1]
    epd = sys.argv[2]
    games = int(sys.argv[3])
    out = sys.argv[4]
    workers = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    hash_mb = int(sys.argv[6]) if len(sys.argv) > 6 else 16
    global HASH_MB
    HASH_MB = hash_mb

    openings = []
    with open(epd, errors="ignore") as f:
        for line in f:
            head = line.split(";")[0].split()
            if len(head) < 4:
                continue
            openings.append(" ".join(head[:4]) + " 0 1")
            if len(openings) >= games:
                break
    n = min(games, len(openings))
    results = [None] * n
    t0 = time.time()
    done = 0
    with Pool(workers) as pool:
        for i, ga in pool.imap_unordered(play_pair,
                                         [(i, openings[i], engine) for i in range(n)],
                                         chunksize=1):
            results[i] = ga
            done += 1
            if done % 50 == 0:
                print(f"{done}/{n} games, {time.time()-t0:.0f}s", flush=True)
    lengths = [len(g) for g in results]
    short = [(i, L) for i, L in enumerate(lengths) if L < MIN_PLIES]
    h = hashlib.sha256()
    for g in results:
        h.update((" ".join(g) + "\n").encode())
    digest = h.hexdigest()
    json.dump({"engine": engine, "hash_mb": hash_mb, "games": n, "go": GO,
               "lengths": lengths, "sha256": digest, "games_below_min": short},
              open(out, "w"))
    print(f"engine {engine} hash {hash_mb}: games {n}, shortest {min(lengths)} plies, "
          f"below {MIN_PLIES}: {len(short)}, sha256 {digest}")
    if short:
        print("LENGTH ASSERTION FAILED:", short[:5])
        sys.exit(1)


if __name__ == "__main__":
    main()
