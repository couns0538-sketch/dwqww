#!/usr/bin/env python3
"""diagonal.py EXE OUT.json — the SMALLEST SAFE Hash x MultiPV combinations.

Seat 02's S-F7 (confirmed by seat 12 as S-C3) shows large Hash + MultiPV > 1 collapses because the
extra-PV loop clears the whole table once per extra line, so the cost scales with Hash x (MultiPV-1).
The 2x2 established the extremes; this walks the diagonal a user would actually set, so the answer is
"what can I put in my GUI" rather than "the combination is bad".

Cells: MultiPV 2, 3, 4 x Hash 16, 32, 64, plus MultiPV 1 at the same Hash values as the control.
Two regimes per cell:
  depth6  `go depth 6`  -> wall ms; if a cell cannot finish depth 6 quickly it is unusable for analysis
  clock5s `go wtime 5000 btime 5000` -> depth reached and wall ms; the game-play number

Every run: fresh process, Threads 1 (no Threads option sent), OwnBook false, startpos, read to
`bestmove` before anything else. 2 runs per cell (the effect is two orders of magnitude, so 2 is
enough to see a boundary and the coordinator asked for depth and achieved time per cell).
"""
import json
import queue
import re
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class Eng:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.q = queue.Queue()
        self.lines = []
        threading.Thread(target=self._rd, daemon=True).start()
        self.send("uci")
        self.wait(lambda l: l == "uciok")

    def _rd(self):
        for ln in self.p.stdout:
            self.q.put(ln.rstrip("\n"))
        self.q.put(None)

    def send(self, s):
        try:
            self.p.stdin.write(s + "\n")
            self.p.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            pass

    def wait(self, pred, bound=600.0):
        end = time.monotonic() + bound
        while time.monotonic() < end:
            try:
                ln = self.q.get(timeout=0.2)
            except queue.Empty:
                if self.p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            self.lines.append(ln)
            if pred(ln):
                return ln
        return "TIMEOUT"

    def close(self):
        self.send("quit")
        try:
            self.p.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            self.p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.wait()


def one(exe, hash_mb, multipv, go, bound=900.0):
    e = Eng(exe)
    for name, value in (("Hash", hash_mb), ("MultiPV", multipv), ("OwnBook", "false")):
        e.send(f"setoption name {name} value {value}")
        e.send("isready")
        e.wait(lambda l: l == "readyok", 60)
    e.send(f"position fen {START}")
    e.send("isready")
    e.wait(lambda l: l == "readyok")
    i = len(e.lines)
    t0 = time.monotonic()
    e.send(go)
    bm = e.wait(lambda l: l.startswith("bestmove"), bound)
    wall = time.monotonic() - t0
    seg = e.lines[i:]
    e.close()
    depth = 0
    for l in seg:
        m = re.search(r"^info depth (\d+)", l)
        if m:
            depth = max(depth, int(m.group(1)))
    return {"wall_s": round(wall, 3), "depth": depth,
            "answered": bm not in (None, "TIMEOUT")}


def main():
    exe, outfile = sys.argv[1], sys.argv[2]
    reps = 2
    out = {"exe": exe, "threads": 1, "reps": reps, "cells": []}
    print(f"exe {exe}  Threads 1  startpos  {reps} runs per cell\n")

    hashes = (16, 32, 64)
    mpvs = (1, 2, 3, 4)

    print("=== A: `go depth 6` wall time (ms) — is the cell usable for analysis?")
    print(f"{'MultiPV':>8} | " + " | ".join(f"Hash {h:>4}" for h in hashes))
    print("-" * 62)
    d6 = {}
    for mpv in mpvs:
        row = []
        for h in hashes:
            runs = [one(exe, h, mpv, "go depth 6") for _ in range(reps)]
            med = statistics.median(r["wall_s"] for r in runs) * 1000
            d6[(h, mpv)] = med
            row.append(f"{med:>8.0f}")
            out["cells"].append({"part": "depth6", "hash": h, "multipv": mpv,
                                 "median_ms": round(med, 1),
                                 "runs_ms": [round(r["wall_s"] * 1000, 1) for r in runs],
                                 "depths": [r["depth"] for r in runs]})
        print(f"{mpv:>8} | " + " | ".join(row))

    print("\n=== B: `go wtime 5000 btime 5000` — depth reached (and ms used)")
    print(f"{'MultiPV':>8} | " + " | ".join(f"Hash {h:>4}" for h in hashes))
    print("-" * 62)
    for mpv in mpvs:
        row = []
        for h in hashes:
            runs = [one(exe, h, mpv, "go wtime 5000 btime 5000") for _ in range(reps)]
            depths = [r["depth"] for r in runs]
            ms = [round(r["wall_s"] * 1000) for r in runs]
            row.append(f"{min(depths):>2}d {max(ms):>6}ms")
            out["cells"].append({"part": "clock5s", "hash": h, "multipv": mpv,
                                 "depths": depths, "runs_ms": ms})
        print(f"{mpv:>8} | " + " | ".join(row))

    Path(outfile).write_text(json.dumps(out, indent=1) + "\n")

    # ---- the boundary: largest MultiPV that stays under 200 ms at depth 6 for each Hash
    print("\n=== smallest safe combinations (depth-6 wall under 200 ms)")
    for h in hashes:
        safe = [m for m in mpvs if d6[(h, m)] < 200]
        best = max(safe) if safe else 0
        print(f"  Hash {h:>4} MB: safe MultiPV <= {best}"
              + (f"  (MultiPV {best} takes {d6[(h,best)]:.0f} ms)" if best else ""))
    print(f"\nraw -> {outfile}")


if __name__ == "__main__":
    main()
