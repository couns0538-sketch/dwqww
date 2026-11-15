#!/usr/bin/env python3
"""Job 11 step 4 (job 10 part B): the first answer on a clock.

MultiPV 1 and 4; Hash 16, 128 and 512; Threads 1. For 50 positions, a FRESH process each:
setoption lines, isready, ucinewgame, isready, then `go wtime C btime C` for C in
{60, 200, 1000} ms. Report the time from `go` to `bestmove`: median, largest, and how often
it exceeds the clock. The clock starts after `ucinewgame`/`isready`, so hash-clearing cost
is not charged (job 8 measured that at ~35 ms for 512 MB).

Usage: j11_partB.py <positions.json> <out.json>
"""
import json
import queue
import statistics
import subprocess
import sys
import threading
import time

ENGINE = "/tmp/ds/build-release/forge"


def one_run(fen, multipv, hash_mb, clock_ms):
    proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip("\n")) for l in proc.stdout],
                     daemon=True).start()
    for c in ("setoption name Threads value 1", f"setoption name Hash value {hash_mb}",
              "setoption name NNUEArch value false", "setoption name OwnBook value false",
              f"setoption name MultiPV value {multipv}", "isready", "ucinewgame", "isready"):
        proc.stdin.write(c + "\n")
    proc.stdin.flush()
    # wait for the two readyoks
    seen = 0
    deadline = time.monotonic() + 60
    while seen < 2 and time.monotonic() < deadline:
        try:
            line = q.get(timeout=5)
        except queue.Empty:
            break
        if line.startswith("readyok"):
            seen += 1
    proc.stdin.write(f"position fen {fen}\n")
    t0 = time.monotonic()
    proc.stdin.write(f"go wtime {clock_ms} btime {clock_ms}\n")
    proc.stdin.flush()
    best = None
    while True:
        try:
            line = q.get(timeout=max(0.01, 30 - (time.monotonic() - t0)))
        except queue.Empty:
            break
        if line.startswith("bestmove"):
            best = line.split()[1] if len(line.split()) > 1 else None
            break
    elapsed = (time.monotonic() - t0) * 1000.0
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    return best, elapsed


def main():
    positions = json.load(open(sys.argv[1]))[:50]
    out_path = sys.argv[2]
    rows = []
    for multipv in (1, 4):
        for hash_mb in (16, 128, 512):
            for clock in (60, 200, 1000):
                times = []
                over = 0
                in_set = 0
                for p in positions:
                    best, ms = one_run(p["fen"], multipv, hash_mb, clock)
                    times.append(ms)
                    if ms > clock:
                        over += 1
                    if best in p["answers"]:
                        in_set += 1
                rows.append({"multipv": multipv, "hash_mb": hash_mb, "clock_ms": clock,
                             "positions": len(positions),
                             "median_ms": round(statistics.median(times), 2),
                             "max_ms": round(max(times), 2),
                             "later_than_clock": over,
                             "in_answer_set": in_set})
                print(json.dumps(rows[-1]), flush=True)
    json.dump(rows, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main()
