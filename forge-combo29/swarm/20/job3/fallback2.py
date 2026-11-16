#!/usr/bin/env python3
"""fallback2.py — seat 20, job3: characterise the UNSEARCHED-MOVE fallback and test whether it can be
reached in GAME PLAY (a GUI's own commands), which is what would matter.

What the base code does (search.cpp, read at 6b98f217):
  - `if (result.best_move.is_none()) result.best_move = root_candidates.front();`  (end of Worker::search)
  - `if (limits.nodes_specified && limits.nodes == 0) { result.best_move = root_candidates.front(); return; }`
  - `result.best_move = root_candidates.front();` when the time is already gone at dispatch.
root_candidates.front() is the FIRST move of the engine's legal-move list (a2a3-family for white).

Criterion (stated before the run): a reply is UNSEARCHED when the process printed NO `info depth` line before
its `bestmove`. Verified here:
  1. go nodes 1 / go nodes 0 / go depth 0 on three positions (already known from clockcut).
  2. A real GUI's stop: go infinite, then stop after 0-20 ms, 20 tries each.
  3. A real GUI's quit during a search (that one is legal: quit ends the process).
  4. THE ONE THAT WOULD MATTER: a normal clock game, sending go only after each bestmove, checking that no
     bestmove is unsearched and that each bestmove is legal for the current board.
"""
import subprocess
import sys
import threading
import time

import chess

EXE = sys.argv[1]
FENS = [
    ("startpos", chess.STARTING_FEN),
    ("italian", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"),
    ("midgame", "r2q1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 1"),
    ("KvK", "8/8/8/8/8/8/8/K6k w - - 0 1"),
]


class Eng:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.lines = []
        self.lock = threading.Lock()
        threading.Thread(target=self._rd, daemon=True).start()

    def _rd(self):
        try:
            for l in self.p.stdout:
                with self.lock:
                    self.lines.append(l.rstrip("\n"))
        except Exception:
            pass

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def mark(self):
        with self.lock:
            return len(self.lines)

    def since(self, k):
        with self.lock:
            return self.lines[k:]

    def wait_best(self, k, timeout=30):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            for l in self.since(k):
                if l.startswith("bestmove"):
                    return l
            time.sleep(0.002)
        return None

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def reset(e):
    e.send("uci"); e.send("setoption name OwnBook value false"); e.send("isready")
    e.send("ucinewgame"); e.send("isready")
    time.sleep(0.05)


print(f"== fallback2 on {EXE}")
e = Eng(EXE)
reset(e)

print("\n-- 1. explicit tiny budgets (positions x go forms), 5 tries each")
print(f"{'position':9s} {'go':16s} {'unsearched':>10s} {'moves':20s}")
for name, fen in FENS:
    for go in ("go nodes 1", "go nodes 0", "go depth 0", "go depth 1"):
        uns = 0
        moves = []
        for _ in range(5):
            e.send(f"position fen {fen}")
            e.send("isready")
            k = e.mark()
            e.send(go)
            bm = e.wait_best(k, 20)
            depth = sum(1 for x in e.since(k) if x.startswith("info depth"))
            if bm:
                mv = bm.split()[1]
                moves.append(mv)
                if depth == 0:
                    uns += 1
            e.send("stop")
            time.sleep(0.01)
        print(f"{name:9s} {go:16s} {uns:10d} {','.join(sorted(set(moves))):20s}")

print("\n-- 2. a GUI's stop: go infinite, stop after d ms (20 tries each)")
print(f"{'position':9s} {'delay':>6s} {'unsearched':>10s} {'moves':20s}")
for name, fen in FENS[:3]:
    for d in (0, 1, 2, 5, 10, 20, 50, 200):
        uns = 0
        moves = []
        for _ in range(20):
            e.send(f"position fen {fen}")
            e.send("isready")
            k = e.mark()
            e.send("go infinite")
            if d:
                time.sleep(d / 1000.0)
            e.send("stop")
            bm = e.wait_best(k, 20)
            depth = sum(1 for x in e.since(k) if x.startswith("info depth"))
            if bm:
                moves.append(bm.split()[1])
                if depth == 0:
                    uns += 1
            time.sleep(0.01)
        print(f"{name:9s} {d:6d} {uns:10d} {','.join(sorted(set(moves))):20s}")

print("\n-- 3. a normal clock game from startpos, one go per bestmove, 40 plies (white gets wtime 1000)")
b = chess.Board()
uns = 0
illegal = 0
ndepths = []
t0 = time.monotonic()
while not b.is_game_over() and b.ply() < 20:
    e.send(f"position fen {b.fen()}")
    e.send("isready")
    k = e.mark()
    e.send("go wtime 1000 btime 1000 winc 0 binc 0")
    bm = e.wait_best(k, 20)
    depth = sum(1 for x in e.since(k) if x.startswith("info depth"))
    ndepths.append(depth)
    if not bm:
        print(f"  ply {b.ply()}: NO BESTMOVE")
        break
    mv = bm.split()[1]
    if depth == 0:
        uns += 1
    try:
        m = chess.Move.from_uci(mv)
    except ValueError:
        m = None
    if m is None or m not in b.legal_moves:
        illegal += 1
        print(f"  ply {b.ply()}: ILLEGAL bestmove {mv} for {b.fen()}")
        break
    b.push(m)
print(f"  plies played {b.ply()}, unsearched {uns}, illegal {illegal}, "
      f"info-depth counts {ndepths}, wall {time.monotonic()-t0:.1f}s")
e.close()
