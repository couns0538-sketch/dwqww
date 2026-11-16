#!/usr/bin/env python3
"""check_s16f28.py -- MY OWN check of seat 16's S-F28: with an IDENTICAL clock every move the engine's
own search time varies widely across moves (they measured 166-416 ms, a 2.51x ratio, over 10 moves at
a 6000 ms clock), while never overrunning.

My harness: ONE engine process for a move sequence, Threads 1, Hash 16, OwnBook false, PC20, both
clocks present (30-C49), with the clock DEBITED by the measured wall time after each move so the
sequence is realistic. I record the engine's own reported `time` field from its last info line (its
own accounting) AND my monotonic wall measurement, so the two can be compared.

usage: check_s16f28.py OUTDIR [N_MOVES] [CLOCK_MS]
"""
import json
import os
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
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1, env=ENV)
        self.out = []
        self.lock = threading.Lock()
        threading.Thread(target=self._pump, daemon=True).start()
        self.send("uci")
        self.wait("uciok")
        for n, v in PC20:
            self.send("setoption name %s value %s" % (n, v))
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

    def wait(self, prefix, timeout=60.0):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            with self.lock:
                hit = [x for x in self.out if x.startswith(prefix)]
            if hit:
                return hit[-1]
            time.sleep(0.002)
        return None

    def search(self, pos_cmd, go):
        self.send("position " + pos_cmd)
        self.sync()
        with self.lock:
            mark = len(self.out)
        t0 = time.monotonic()
        self.send(go)
        bm = None
        while time.monotonic() - t0 < 300:
            with self.lock:
                blk = self.out[mark:]
            hit = [x for x in blk if x.startswith("bestmove")]
            if hit:
                parts = hit[0].split()
                bm = parts[1] if len(parts) > 1 else None
                break
            time.sleep(0.002)
        wall = (time.monotonic() - t0) * 1000
        with self.lock:
            blk = self.out[mark:]
        etime = enodes = None
        for l in blk:
            if l.startswith("info depth") and " pv" in l:
                t = l.split()
                if "time" in t:
                    etime = int(t[t.index("time") + 1])
                if "nodes" in t:
                    enodes = int(t[t.index("nodes") + 1])
        return bm, etime, enodes, wall

    def close(self):
        self.send("quit")
        try:
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def main():
    outdir = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    clock = int(sys.argv[3]) if len(sys.argv) > 3 else 6000
    os.makedirs(outdir, exist_ok=True)
    b = chess.Board(START)
    e = Eng()
    rows = []
    print("ONE process, move sequence, Threads 1, Hash 16, PC20, clock %d ms (both clocks), debited" % clock)
    print("%-5s %-8s %-9s %-9s %-9s %-9s %s" % (
        "ply", "bestmove", "eng_ms", "wall_ms", "nodes", "clock_left", "overrun?"))
    remaining = float(clock)
    try:
        e.send("ucinewgame")
        e.sync()
        for ply in range(n):
            if b.is_game_over():
                break
            pos = "fen " + b.fen()
            go = "go wtime %d btime %d" % (int(remaining), int(remaining))
            bm, etime, enodes, wall = e.search(pos, go)
            over = wall > remaining
            rows.append({"ply": ply, "bestmove": bm, "eng_ms": etime, "wall_ms": round(wall, 1),
                         "nodes": enodes, "clock_left": round(remaining, 1), "overrun": over,
                         "fen": b.fen()})
            print("%-5d %-8s %-9s %-9s %-9s %-9s %s" % (
                ply, bm, etime, round(wall, 1), enodes, round(remaining), "OVERRUN" if over else ""))
            remaining = max(0.0, remaining - wall)
            if not bm or bm == "0000":
                break
            try:
                mv = chess.Move.from_uci(bm)
            except ValueError:
                break
            if mv not in b.legal_moves:
                break
            b.push(mv)
    finally:
        e.close()
    walls = [r["wall_ms"] for r in rows]
    engs = [r["eng_ms"] for r in rows if r["eng_ms"]]
    summary = {
        "moves": len(rows),
        "overruns": sum(1 for r in rows if r["overrun"]),
        "wall_min": min(walls) if walls else None,
        "wall_max": max(walls) if walls else None,
        "wall_ratio": round(max(walls) / min(walls), 2) if walls and min(walls) else None,
        "eng_min": min(engs) if engs else None,
        "eng_max": max(engs) if engs else None,
        "eng_ratio": round(max(engs) / min(engs), 2) if engs and min(engs) else None,
    }
    print()
    print(json.dumps(summary, indent=1))
    with open(os.path.join(outdir, "check_s16f28.json"), "w") as f:
        json.dump({"clock_ms": clock, "start": START, "rows": rows, "summary": summary}, f, indent=1)


if __name__ == "__main__":
    main()
