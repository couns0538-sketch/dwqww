#!/usr/bin/env python3
"""R5C M1: the N3 options over UCI (SyzygyPath + IntendedThreefold + HardDeadline=10, Threads 1).

1. SyzygyPath info strings: a missing folder and an empty folder name the path ("info string SyzygyPath: no
   tablebase found in ..."), real tables report their counts, <empty> switches them off; after <empty> `bench 13`
   gives the lock pin (empty path = OFF identity).
2. HardDeadline=10 with the N3 options on: for every position (start, middlegame, tablebase roots, a 6-piece root)
   and every go mode, exactly one bestmove arrives, before the deadline:
     go movetime 50          hard limit 40 ms (movetime - Move Overhead 10)   deadline 50 ms after go
     go wtime 100 btime 100  hard limit 20 ms (min(90*60%, 4*5))             deadline 30 ms after go
     go infinite + stop      (no clock: no watchdog)                         bestmove within --stop-limit ms of stop
   Times are measured by this driver around the pipe (go written -> bestmove read); --slack ms is added for the
   driver and the OS (default 5; CI runners are slower). Bestmoves are checked for legality with python-chess
   when it is installed (the PC venv), else for shape.
usage: r5c_n3_uci.py <engine> [--syzygy DIR] [--reps 5] [--slack 5] [--stop-limit 15] [--log FILE]
exit 0 = every check passed.
"""
import argparse
import os
import random
import re
import subprocess
import sys
import tempfile
import time

try:
    import chess  # optional: legality of every bestmove
except ImportError:
    chess = None

POSITIONS = [
    ("start", "startpos"),
    ("middlegame", "fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 9"),
    ("KQRvK", "fen 8/8/8/8/2k5/8/1Q6/K6R w - - 0 1"),
    ("KBBvKN blessed", "fen 8/B7/2B5/8/3k2K1/1n6/8/8 b - - 0 1"),
    ("6 pieces", "fen 8/5kp1/8/8/2q5/8/1Q6/K6R w - - 0 1"),
]


class Engine:
    def __init__(self, exe, log):
        flags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
                                  creationflags=flags)
        self.log = log

    def send(self, line):
        self.log.write("> " + line + "\n")
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def read(self):
        line = self.p.stdout.readline()
        if not line:
            raise SystemExit("FAIL engine exited")
        line = line.rstrip("\r\n")
        self.log.write(line + "\n")
        return line

    def until(self, pred):
        seen = []
        while True:
            line = self.read()
            seen.append(line)
            if pred(line):
                return line, seen

    def sync(self):
        self.send("isready")
        return self.until(lambda l: l == "readyok")[1][:-1]


failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what, flush=True)
    if not ok:
        failures.append(what)


def legal(position, move):
    if chess is None:
        return re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", move) is not None
    board = chess.Board() if position == "startpos" else chess.Board(position[4:])
    return chess.Move.from_uci(move) in board.legal_moves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--syzygy", default="")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--slack", type=float, default=5.0)
    ap.add_argument("--stop-limit", type=float, default=15.0)
    ap.add_argument("--log", default="")
    a = ap.parse_args()
    log = open(a.log, "w") if a.log else open(os.devnull, "w")
    e = Engine(a.engine, log)
    e.send("uci")
    e.until(lambda l: l == "uciok")
    for opt in ("Threads value 1", "Hash value 16", "OwnBook value false"):
        e.send("setoption name " + opt)
    e.sync()

    # 1. info strings
    missing = os.path.join(tempfile.gettempdir(), "r5c_no_such_tb_folder_7c1f")
    e.send(f"setoption name SyzygyPath value {missing}")
    out = e.sync()
    check(any(l.startswith("info string SyzygyPath: no tablebase found in") and missing in l for l in out),
          f"missing folder is named: {out}")
    with tempfile.TemporaryDirectory() as empty:
        e.send(f"setoption name SyzygyPath value {empty}")
        out = e.sync()
        check(any(l.startswith("info string SyzygyPath: no tablebase found in") for l in out), f"empty folder is named: {out}")
    e.send("setoption name SyzygyPath value <empty>")
    out = e.sync()
    check(out == ["info string Syzygy tablebases off"], f"<empty> switches the tables off: {out}")
    e.send("bench 13")
    line, _ = e.until(lambda l: "bench depth 13 nodes" in l)
    nodes = int(re.search(r"nodes (\d+)", line).group(1))
    check(nodes == 862329, f"empty path: bench 13 = {nodes} (pin 862329)")
    if a.syzygy:
        e.send(f"setoption name SyzygyPath value {a.syzygy}")
        out = e.sync()
        check(any(re.search(r"info string Syzygy: \d+ WDL and \d+ DTZ tables, up to 5 pieces", l) for l in out)
              and not any(l.startswith("info string SyzygyPath:") for l in out), f"real tables load: {out}")

    # 2. HardDeadline=10 with the N3 options
    e.send("setoption name IntendedThreefold value true")
    e.send("setoption name HardDeadline value 10")
    e.sync()
    rng = random.Random(5)
    worst = {}
    for name, pos in POSITIONS:
        if "fen 8/" in pos and not a.syzygy and name != "6 pieces":
            continue
        for rep in range(a.reps):
            for mode, go, deadline in (("movetime 50", "go movetime 50", 50.0),
                                       ("wtime 100", "go wtime 100 btime 100 winc 0 binc 0", 30.0),
                                       ("infinite+stop", "go infinite", None)):
                e.send("ucinewgame")
                e.send("position " + pos)
                e.sync()
                t0 = time.perf_counter()
                e.send(go)
                if deadline is None:
                    time.sleep(rng.uniform(0.02, 0.08))
                    t0 = time.perf_counter()
                    e.send("stop")
                line, seen = e.until(lambda l: l.startswith("bestmove"))
                ms = (time.perf_counter() - t0) * 1000
                after = e.sync()
                move = line.split()[1]
                limit = (deadline if deadline is not None else a.stop_limit) + a.slack
                key = f"{name} / {mode}"
                worst[key] = max(worst.get(key, 0.0), ms)
                ok = ms <= limit and legal(pos, move) and not any(l.startswith("bestmove") for l in after)
                if not ok:
                    check(False, f"{key} rep {rep}: bestmove {move} after {ms:.1f} ms (limit {limit:.0f}), "
                                 f"extra bestmove {any(l.startswith('bestmove') for l in after)}")
    for key, ms in worst.items():
        mode = key.split(" / ")[1]
        limit = {"movetime 50": 50.0, "wtime 100": 30.0}.get(mode, a.stop_limit) + a.slack
        check(ms <= limit, f"{key}: slowest bestmove {ms:.1f} ms (limit {limit:.0f} ms incl. slack {a.slack:.0f})")
    e.send("quit")
    e.p.wait(timeout=30)
    print(f"{len(failures)} failures" + ("" if failures else "\nPASS"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
