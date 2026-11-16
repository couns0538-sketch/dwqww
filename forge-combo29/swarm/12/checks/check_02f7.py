#!/usr/bin/env python3
"""check_multipv_hash.py EXE OUT.json — seat 12's check of seat 02's S-F7 / S-F7b.

Claim: large `Hash` together with `MultiPV > 1` makes searches enormously slow, because the
extra-PV loop clears the whole transposition table once per extra line. On a clock it becomes a
strength loss: `go wtime 5000 btime 5000` with Hash 2048 + MultiPV 8 reaches only depth 1.

Design, per the standard this swarm has settled on:
  - a MATRIX, not a single pair: Hash in {16, 2048} x MultiPV in {1, 8}, so the effect is attributed
    to the COMBINATION rather than to either option alone;
  - each cell repeated N times, fresh process, Threads 1 (no Threads option sent);
  - the control that makes a "slow" claim meaningful: Hash 16 + MultiPV 1 and Hash 2048 + MultiPV 1
    must both be fast, and Hash 16 + MultiPV 8 must be fast. If only the (large Hash, MultiPV>1)
    cell is slow, the claim is confirmed rather than "MultiPV is just slow";
  - wall time measured around the `go`..`bestmove` exchange only, with a monotonic clock;
  - the depth reached on a fixed 5 s clock, which is the strength half.

Every run reads stdout to `bestmove` before anything else (no pipelined `quit`).
"""
import json
import queue
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
POS = f"position fen {START}"


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
    """One fresh process; returns wall seconds from `go` to `bestmove`, and the last depth."""
    e = Eng(exe)
    for name, value in (("Hash", hash_mb), ("MultiPV", multipv), ("OwnBook", "false")):
        e.send(f"setoption name {name} value {value}")
        e.send("isready")
        e.wait(lambda l: l == "readyok", 60)
    e.send(POS)
    e.send("isready")
    e.wait(lambda l: l == "readyok")
    i = len(e.lines)
    t0 = time.monotonic()
    e.send(go)
    bm = e.wait(lambda l: l.startswith("bestmove"), bound)
    wall = time.monotonic() - t0
    seg = e.lines[i:]
    e.close()
    depth, nodes, lines = 0, None, 0
    for l in seg:
        if l.startswith("info depth"):
            lines += 1
            import re
            m = re.search(r"^info depth (\d+)", l)
            if m:
                depth = max(depth, int(m.group(1)))
            n = re.search(r" nodes (\d+)", l)
            if n:
                nodes = int(n.group(1))
    return {"wall_s": round(wall, 3), "depth": depth, "nodes": nodes, "info_lines": lines,
            "answered": bm not in (None, "TIMEOUT"), "bestmove": bm.split()[1] if isinstance(bm, str) and bm.startswith("bestmove") else None}


def main():
    exe, outfile = sys.argv[1], sys.argv[2]
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    out = {"exe": exe, "threads": 1, "position": START, "reps": reps, "cells": []}
    print(f"exe {exe}")
    print(f"Threads 1 (no Threads option sent); {reps} fresh processes per cell")
    print(f"position: startpos\n")

    print("=== part 1: `go depth 6` — is the SLOWNESS there? (seat 02's S-F7)")
    print(f"{'Hash':>6} {'MultiPV':>8} {'median ms':>10} {'all runs ms':>34} {'depth':>6} {'info lines':>11}")
    for hash_mb in (16, 2048):
        for multipv in (1, 8):
            runs = []
            for _ in range(reps):
                r = one(exe, hash_mb, multipv, "go depth 6")
                runs.append(r)
            walls = [r["wall_s"] for r in runs]
            med = statistics.median(walls) * 1000
            cell = {"part": "depth6", "hash": hash_mb, "multipv": multipv,
                    "median_ms": round(med, 1), "runs_ms": [round(w * 1000, 1) for w in walls],
                    "depth": runs[0]["depth"], "info_lines": runs[0]["info_lines"],
                    "answered": all(r["answered"] for r in runs)}
            out["cells"].append(cell)
            print(f"{hash_mb:>6} {multipv:>8} {med:>10.1f} {str(cell['runs_ms']):>34} "
                  f"{cell['depth']:>6} {cell['info_lines']:>11}")

    print("\n=== part 2: `go wtime 5000 btime 5000` — does it cost DEPTH? (seat 02's S-F7b)")
    print(f"{'Hash':>6} {'MultiPV':>8} {'median ms':>10} {'depth per run':>20} {'nodes':>10}")
    for hash_mb in (16, 2048):
        for multipv in (1, 8):
            runs = []
            for _ in range(reps):
                r = one(exe, hash_mb, multipv, "go wtime 5000 btime 5000")
                runs.append(r)
            walls = [r["wall_s"] for r in runs]
            med = statistics.median(walls) * 1000
            cell = {"part": "clock5s", "hash": hash_mb, "multipv": multipv,
                    "median_ms": round(med, 1), "runs_ms": [round(w * 1000, 1) for w in walls],
                    "depths": [r["depth"] for r in runs], "nodes": [r["nodes"] for r in runs],
                    "answered": all(r["answered"] for r in runs)}
            out["cells"].append(cell)
            print(f"{hash_mb:>6} {multipv:>8} {med:>10.1f} {str(cell['depths']):>20} "
                  f"{str(cell['nodes'][0]):>10}")

    Path(outfile).write_text(json.dumps(out, indent=1) + "\n")

    # ---- verdicts
    d6 = {(c["hash"], c["multipv"]): c for c in out["cells"] if c["part"] == "depth6"}
    clk = {(c["hash"], c["multipv"]): c for c in out["cells"] if c["part"] == "clock5s"}
    big = d6[(2048, 8)]["median_ms"]
    others = [d6[k]["median_ms"] for k in ((2048, 1), (16, 8), (16, 1))]
    print(f"\n=== verdict")
    print(f"S-F7 slowness: Hash2048+MultiPV8 = {big:.0f} ms; the other three cells = "
          f"{[round(x) for x in others]} ms")
    print(f"  -> {'CONFIRMED: the COMBINATION is what is slow' if big > 20 * max(others) else 'NOT confirmed'}")
    d_big = clk[(2048, 8)]["depths"]
    d_small = clk[(16, 1)]["depths"]
    print(f"S-F7b clock: Hash2048+MultiPV8 depths {d_big} vs Hash16+MultiPV1 depths {d_small}")
    print(f"  -> {'CONFIRMED: large Hash + MultiPV costs depth on a clock' if max(d_big) < min(d_small) else 'NOT confirmed on this evidence'}")
    print(f"raw -> {outfile}")


if __name__ == "__main__":
    main()
