#!/usr/bin/env python3
"""check_s28f1.py — seat 20, area 10 job 10: my OWN check of seat 28's S-F1.

Claim: "`go movetime M` stops at M-10 ms: the default `Move Overhead 10` is subtracted from the movetime limit
(src/search.cpp:2192, src/uci.cpp:152), so `go movetime 10` searches 1 ms and `go movetime 50` stops at 40.5 ms."

I do not use their harness. I send `go movetime M` and wait for `bestmove`, timing with a monotonic clock, then
re-test with `setoption name Move Overhead value 0`.

Predictions (in PREDICTION.txt, committed before this ran) - this file only measures.
usage: check_s28f1.py <exe> <outdir>
"""
import json
import os
import statistics
import subprocess
import sys
import threading
import time

EXE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"


def one(movetime, overhead=None, timeout=30.0):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []
    lock = threading.Lock()

    def rd():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass
    threading.Thread(target=rd, daemon=True).start()
    pre = ["uci", "setoption name OwnBook value false"]
    if overhead is not None:
        pre.append(f"setoption name Move Overhead value {overhead}")
    pre += ["isready", "ucinewgame", "isready", f"position fen {FEN}", "isready"]
    for c in pre:
        p.stdin.write(c + "\n")
        p.stdin.flush()
    time.sleep(0.05)
    t0 = time.monotonic()
    p.stdin.write(f"go movetime {movetime}\n")
    p.stdin.flush()
    bm = None
    while time.monotonic() - t0 < timeout:
        with lock:
            b = [x for x in out if x.startswith("bestmove")]
        if b:
            bm = b[-1]
            break
        time.sleep(0.0005)
    t1 = time.monotonic()
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return {"movetime": movetime, "overhead": overhead, "wall_ms": (t1 - t0) * 1000.0, "bestmove": bm}


rows = []
print(f"exe {EXE}")
print(f"position {FEN}")
print(f"machine nproc {os.cpu_count()}")
print()
print(f"{'movetime':>9s} {'overhead':>9s} {'n':>3s} {'median':>8s} {'p99':>8s} {'max':>8s} {'min':>8s} "
      f"{'median-requested':>17s}")
for mt in (10, 50, 100, 200, 500):
    for oh in (None, 0):
        rs = [one(mt, oh) for _ in range(15)]
        w = sorted(r["wall_ms"] for r in rs)
        med = statistics.median(w)
        p99 = w[min(len(w) - 1, int(0.99 * (len(w) - 1)))]
        print(f"{mt:9d} {str(oh):>9s} {len(w):3d} {med:8.2f} {p99:8.2f} {max(w):8.2f} {min(w):8.2f} "
              f"{med-mt:+17.2f}")
        rows += rs

# the same, with a spread of overheads on movetime 100 (to show the subtraction is linear in the option)
print()
print(f"{'movetime':>9s} {'overhead':>9s} {'median wall':>12s} {'implied stop after':>19s}")
for oh in (0, 5, 10, 25, 50):
    rs = [one(100, oh) for _ in range(11)]
    w = sorted(r["wall_ms"] for r in rs)
    med = statistics.median(w)
    print(f"{100:9d} {oh:9d} {med:12.2f} {med:19.2f}")

with open(os.path.join(OUT, "check_s28f1.json"), "w") as f:
    json.dump(rows, f, indent=1)
print("\nwrote check_s28f1.json")
