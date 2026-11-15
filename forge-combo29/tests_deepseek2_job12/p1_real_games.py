#!/usr/bin/env python3
"""Job 12 P1, second half: the counter distribution on 200 positions taken from
real games of this engine after move 60.

1. Play 20 games of the UNPATCHED exe against itself at 20,000 nodes per move,
   one engine process per game, replaying the moves (a search is cut when more
   input is already waiting, so each move is answered before the next is sent).
2. From each game take 10 positions after move 60 (ply 120), skipping terminal
   ones, so the sample is 200 positions.
3. Ask the TRACED engine (option on) to search each one and read its counter
   histogram from `info string R50TRACE`.
"""

import json
import queue
import subprocess
import sys
import threading
import time

import chess

UNPATCHED = sys.argv[1]
TRACED = sys.argv[2]
OUT = sys.argv[3]
GAMES = int(sys.argv[4]) if len(sys.argv) > 4 else 20
PER_GAME = 10
NODES = 20000


def engine(path):
    p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip()) for l in p.stdout] + [q.put(None)],
                     daemon=True).start()

    def send(s):
        try:
            p.stdin.write(s + "\n")
            p.stdin.flush()
        except Exception:
            pass

    def until(tok, lim=120.0):
        t0 = time.time()
        got = []
        while time.time() - t0 < lim:
            try:
                ln = q.get(timeout=max(0.01, lim - (time.time() - t0)))
            except queue.Empty:
                break
            if ln is None:
                break
            got.append(ln)
            if ln.startswith(tok):
                return got
        return got

    send("uci")
    until("uciok", 20)
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    send("isready")
    until("readyok", 20)
    return p, send, until


def play_game(path, max_plies=400):
    p, send, until = engine(path)
    board = chess.Board()
    moves, collected = [], []
    try:
        while len(moves) < max_plies:
            if board.is_game_over(claim_draw=True) or board.can_claim_threefold_repetition():
                break
            if board.ply() >= 120 and len(collected) < PER_GAME:
                collected.append(board.fen())
            send("position startpos" + (" moves " + " ".join(moves) if moves else ""))
            send(f"go nodes {NODES}")
            got = until("bestmove", 180)
            best = None
            for ln in got:
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
            p.wait(timeout=20)
        except Exception:
            p.kill()
    return moves, collected, board


def main():
    all_positions = []
    summary = []
    for g in range(GAMES):
        moves, got, final = play_game(UNPATCHED)
        summary.append({"game": g, "plies": len(moves), "collected": len(got),
                        "result": ("mate" if final.is_checkmate() else
                                   "draw" if final.is_game_over(claim_draw=True) else "cut")})
        all_positions.extend(got)
        print(f"game {g+1}/{GAMES}: {len(moves)} plies, {len(got)} positions after move 60, "
              f"ends {summary[-1]['result']}", flush=True)
    print(f"total positions collected: {len(all_positions)}")

    # counter histogram: the traced engine reports it per search, so aggregate
    p, send, until = engine(TRACED)
    send("setoption name Rule50Scale value 300")
    send("isready")
    until("readyok", 20)
    tot = {"c0_9": 0, "c10_19": 0, "c20_39": 0, "c40_69": 0, "c70plus": 0}
    calls = 0
    for i, fen in enumerate(all_positions):
        send("position fen " + fen)
        send("go depth 9")
        got = until("bestmove", 120)
        for ln in got:
            if "R50TRACE" in ln:
                t = ln.split()
                for k in tot:
                    if k in t:
                        tot[k] += int(t[t.index(k) + 1])
                if "calls" in t:
                    calls += int(t[t.index("calls") + 1])
        if (i + 1) % 40 == 0:
            print(f"  traced {i+1}/{len(all_positions)}", flush=True)
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    res = {"games": summary, "positions": len(all_positions), "fens": all_positions, "eval_calls": calls,
           "histogram": tot}
    json.dump(res, open(OUT, "w"), indent=1)
    print("eval calls:", calls, "histogram:", tot)
    if calls:
        print({k: f"{100.0*v/calls:.2f}%" for k, v in tot.items()})


if __name__ == "__main__":
    main()
