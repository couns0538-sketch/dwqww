#!/usr/bin/env python3
"""check_s16f27.py -- MY OWN check of seat 16's S-F27/S-F29: deterministic self-play from ONE start
converges to few distinct games, while ten DIFFERENT starts give ten distinct games.

The mechanism S-F27 claims is determinism at Threads 1 with fixed limits, with occasional divergence
only from clock drift. So the cleanest test is at a FIXED depth/node limit (no clock at all): if the
engine is deterministic, N self-play games from one start must be BYTE-IDENTICAL, and that is a
stronger statement than "3 of 10".

I play games myself with python-chess driving the engine over UCI, one engine process per game,
Threads 1, Hash 16, OwnBook false, `go depth 8` (fixed, no clock). Start positions: one fixed start
for N games, then N different starts from real-game positions.

usage: check_s16f27.py OUTDIR [N_GAMES]
"""
import json
import os
import random
import subprocess
import sys
import threading
import time

import chess

EXE = "/home/ubuntu/b/pc/forge"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
DEPTH = 8
MAX_PLIES = 40


class Engine:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1, env=ENV)
        self.out = []
        self.lock = threading.Lock()
        threading.Thread(target=self._pump, daemon=True).start()
        self.send("uci")
        self.wait("uciok", 60)
        for name, value in PC20:
            self.send("setoption name %s value %s" % (name, value))
            self.sync()

    def _pump(self):
        try:
            for l in self.p.stdout:
                with self.lock:
                    self.out.append(l.rstrip("\n"))
        except Exception:
            pass

    def send(self, s):
        try:
            self.p.stdin.write(s + "\n")
            self.p.stdin.flush()
        except Exception:
            pass

    def sync(self):
        with self.lock:
            k = len(self.out)
        self.send("isready")
        t0 = time.monotonic()
        while time.monotonic() - t0 < 60:
            with self.lock:
                if any(x.strip() == "readyok" for x in self.out[k:]):
                    return
            time.sleep(0.002)
        return

    def wait(self, prefix, timeout=60.0):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            with self.lock:
                hit = [x for x in self.out if x.startswith(prefix)]
            if hit:
                return hit[-1]
            time.sleep(0.002)
        return None

    def bestmove(self):
        with self.lock:
            mark = len(self.out)
        self.send("go depth %d" % DEPTH)
        t0 = time.monotonic()
        while time.monotonic() - t0 < 120:
            with self.lock:
                hit = [x for x in self.out[mark:] if x.startswith("bestmove")]
            if hit:
                parts = hit[0].split()
                return parts[1] if len(parts) > 1 else None
            time.sleep(0.002)
        return None

    def close(self):
        self.send("quit")
        try:
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def play(start_fen):
    """One self-play game over UCI; returns the move list."""
    e = Engine()
    b = chess.Board(start_fen)
    moves = []
    try:
        e.send("ucinewgame")
        e.sync()
        while len(moves) < MAX_PLIES and not b.is_game_over():
            e.send("position fen %s moves %s" % (start_fen, " ".join(moves)))
            e.sync()
            uci = e.bestmove()
            if not uci or uci == "0000":
                break
            try:
                m = chess.Move.from_uci(uci)
            except ValueError:
                break
            if m not in b.legal_moves:
                break
            b.push(m)
            moves.append(uci)
    finally:
        e.close()
    return moves, b.fen()


def varied_starts(n, seed=3011):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        b = chess.Board()
        for _ in range(rng.randint(8, 30)):
            mv = list(b.legal_moves)
            if not mv:
                break
            b.push(rng.choice(mv))
        if not b.is_game_over() and not b.is_check():
            out.append(b.fen())
    return out


def main():
    outdir = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    os.makedirs(outdir, exist_ok=True)
    START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print("self-play at FIXED depth %d (no clock at all), PC r15 + PC20, Threads 1" % DEPTH)
    report = {"depth": DEPTH, "n": n, "same_start": [], "varied_start": []}
    print("--- %d games from ONE start ---" % n)
    for i in range(n):
        moves, fen = play(START)
        report["same_start"].append({"moves": moves, "final_fen": fen})
        print("  game %d: %d plies, final %s" % (i, len(moves), fen[:50]))
    print("--- %d games from DIFFERENT starts ---" % n)
    for i, s in enumerate(varied_starts(n)):
        moves, fen = play(s)
        report["varied_start"].append({"start": s, "moves": moves, "final_fen": fen})
        print("  game %d: %d plies, final %s" % (i, len(moves), fen[:50]))
    ss = {tuple(r["moves"]) for r in report["same_start"]}
    sf = {r["final_fen"] for r in report["same_start"]}
    vs = {tuple(r["moves"]) for r in report["varied_start"]}
    vf = {r["final_fen"] for r in report["varied_start"]}
    report["summary"] = {
        "same_start_distinct_games": len(ss), "same_start_distinct_finals": len(sf),
        "varied_distinct_games": len(vs), "varied_distinct_finals": len(vf),
        "same_start_byte_identical": len(ss) == 1}
    print()
    print("SAME start  : %d distinct games, %d distinct final positions (of %d)" % (
        len(ss), len(sf), n))
    print("VARIED start: %d distinct games, %d distinct final positions (of %d)" % (
        len(vs), len(vf), n))
    print("byte-identical from one start (the stronger claim):", report["summary"]["same_start_byte_identical"])
    with open(os.path.join(outdir, "check_s16f27.json"), "w") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()
