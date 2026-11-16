#!/usr/bin/env python3
"""clockseq.py EXE OUTDIR : clock behaviour across a sequence of moves in ONE process.

Scenario A (a real game): 10 moves from startpos, the clock decreasing by the time the engine used plus the
increment, exactly as a GUI would send it. Checks every move returns a bestmove and none overruns.

Scenario B (identical clock): 10 moves from startpos with the clock HELD at 6000 ms every time, to see whether
the engine's own time management drifts across moves.

Scenario C (movetime interleaved): a clock search, then `go movetime 100`, then a clock search, all in one
process, to see whether the movetime limit leaks into the next clock search.
"""
import os
import re
import statistics
import subprocess
import sys
import time

import chess

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


class Session:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        uci, ok = self.to("uciok", 20)
        if not ok:
            raise Missing("no uciok")
        known = {m.group(1) for l in uci for m in [re.match(r"option name (.*) type ", l)] if m}
        self.send("isready"); self.to("readyok", 20)
        for n, v in PC20.items():
            if n not in known:
                raise Missing(f"option {n} absent")
            self.send(f"setoption name {n} value {v}")
            self.send("isready"); self.to("readyok", 20)

    def send(self, c):
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def to(self, tok, lim=120):
        out = []
        dl = time.monotonic() + lim
        while time.monotonic() < dl:
            l = self.p.stdout.readline()
            if not l:
                return out, False
            l = l.rstrip("\n")
            out.append(l)
            if l.strip().startswith(tok):
                return out, True
        return out, False

    def go(self, cmd):
        t0 = time.monotonic()
        self.send(cmd)
        lines, ok = self.to("bestmove", 60)
        wall = (time.monotonic() - t0) * 1000.0
        if not ok:
            raise Missing(f"no bestmove for '{cmd}'")
        best = None
        eng = None
        depth = None
        for l in lines:
            if l.startswith("bestmove"):
                best = l.split()[1]
            m = re.match(r"^info depth (\d+) .*? time (\d+)", l)
            if m:
                depth = int(m.group(1))
                eng = int(m.group(2))
        if best is None:
            raise Missing("no bestmove token")
        return best, eng, wall, depth

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


POS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
INC = 60
out = [f"exe {EXE}", "PC20 + Threads 1 + Hash 16, one process, moves from startpos", ""]

# Scenario A: a real game, clock decreasing
s = Session()
board = chess.Board()
w, b = 6000, 6000
rows = []
overruns = 0
try:
    for move_no in range(1, 11):
        # a GUI sends the position (with the moves played) before every go
        s.send("position fen " + board.fen())
        s.send("isready"); s.to("readyok", 20)
        if board.turn == chess.WHITE:
            cmd = f"go wtime {w} btime {b} winc {INC} binc {INC}"
        else:
            cmd = f"go wtime {b} btime {w} winc {INC} binc {INC}"
        best, eng, wall, depth = s.go(cmd)
        my_clock = w if board.turn == chess.WHITE else b
        allowed = my_clock + INC
        if wall > allowed:
            overruns += 1
        rows.append(f"  move {move_no:2d} turn {'w' if board.turn else 'b'} clock {my_clock:5d} "
                    f"best {best} depth {depth} engine {eng} wall {wall:.1f} over {overruns and 'X' or 'ok'}")
        mv = chess.Move.from_uci(best)
        if mv not in board.legal_moves:
            raise Missing(f"ILLEGAL bestmove {best} on move {move_no}")
        board.push(mv)
        used = wall
        if board.turn == chess.BLACK:
            w = max(1, int(w - used + INC))
        else:
            b = max(1, int(b - used + INC))
finally:
    s.close()
out.append("### Scenario A: real game, clock decreasing")
out += rows
out.append(f"  overruns: {overruns} of 10")
print("\n".join(out[-13:]) if len(out) > 13 else "\n".join(out), flush=True)

# Scenario B: identical clock every move
s = Session()
board = chess.Board()
rows = []
engines = []
try:
    for move_no in range(1, 11):
        s.send("position fen " + board.fen())
        s.send("isready"); s.to("readyok", 20)
        cmd = f"go wtime 6000 btime 6000 winc {INC} binc {INC}"
        best, eng, wall, depth = s.go(cmd)
        engines.append(eng)
        rows.append(f"  move {move_no:2d} best {best} depth {depth} engine {eng} wall {wall:.1f}")
        mv = chess.Move.from_uci(best)
        if mv not in board.legal_moves:
            raise Missing(f"ILLEGAL bestmove {best} move {move_no}")
        board.push(mv)
finally:
    s.close()
out.append("")
out.append("### Scenario B: identical 6000 ms clock every move")
out += rows
ratio = (max(engines) / max(1, min(engines))) if engines else 0
out.append(f"  engine time: min {min(engines)} max {max(engines)} ratio {ratio:.2f}")
print("\n".join(out[-13:]), flush=True)

# Scenario C: movetime leak
s = Session()
board = chess.Board()
rows = []
try:
    s.send("position startpos"); s.send("isready"); s.to("readyok", 20)
    b1 = s.go("go wtime 6000 btime 6000 winc 60 binc 60")
    b2 = s.go("go movetime 100")
    b3 = s.go("go wtime 6000 btime 6000 winc 60 binc 60")
    rows = [f"  clock search 1: best {b1[0]} engine {b1[1]} wall {b1[2]:.1f}",
            f"  movetime 100  : best {b2[0]} engine {b2[1]} wall {b2[2]:.1f}",
            f"  clock search 2: best {b3[0]} engine {b3[1]} wall {b3[2]:.1f}"]
finally:
    s.close()
out.append("")
out.append("### Scenario C: movetime interleaved with clock searches (same position, one process)")
out += rows
print("\n".join(rows), flush=True)

text = "\n".join(out) + "\n"
with open(os.path.join(OUTDIR, "clockseq.txt"), "w") as fh:
    fh.write(text)
