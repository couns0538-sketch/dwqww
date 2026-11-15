#!/usr/bin/env python3
"""Job 4 part C step 1 and 3: the short-clock cliff, measured.

50 positions with a mate in one, each checked by python-chess.  For every
(wtime, Threads) pair: a fresh process, `Move Overhead 10`, `OwnBook false`,
`go wtime W btime W`, then record whether the answer was the mating move,
whether any nodes were searched, and the largest time from `go` to `bestmove`.
"""

import json
import queue
import subprocess
import sys
import threading
import time

import chess

ENGINE = sys.argv[1]
POSFILE = sys.argv[2]
OUT = sys.argv[3]
CLOCKS = [1, 5, 9, 10, 11, 12, 13, 15, 20, 30, 50]
THREADS = [1, 8, 64]


def run(fen, clock, threads, wait=3.0):
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()

    def reader():
        for ln in p.stdout:
            q.put(ln.rstrip())
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(s):
        try:
            p.stdin.write(s + "\n")
            p.stdin.flush()
            return True
        except Exception:
            return False

    def collect(until, limit):
        t0 = time.time()
        got = []
        while time.time() - t0 < limit:
            try:
                ln = q.get(timeout=max(0.005, limit - (time.time() - t0)))
            except queue.Empty:
                break
            if ln is None:
                break
            got.append(ln)
            if until and until(ln):
                return got, True
        return got, False

    send("uci")
    collect(lambda l: l.strip() == "uciok", 10)
    send(f"setoption name Threads value {threads}")
    send("setoption name Hash value 16")
    send("setoption name Move Overhead value 10")
    send("setoption name OwnBook value false")
    send("isready")
    collect(lambda l: l.strip() == "readyok", 10)
    send("position fen " + fen)
    t0 = time.time()
    send(f"go wtime {clock} btime {clock}")
    got, answered = collect(lambda l: l.startswith("bestmove"), wait)
    elapsed = (time.time() - t0) * 1000.0
    needed_stop = False
    if not answered:
        send("stop")
        more, answered = collect(lambda l: l.startswith("bestmove"), 2.0)
        got += more
        needed_stop = True
        elapsed = (time.time() - t0) * 1000.0
    best = None
    nodes = None
    for ln in got:
        if ln.startswith("bestmove"):
            best = ln.split()[1]
        if " nodes " in ln:
            try:
                nodes = int(ln.split(" nodes ")[1].split()[0])
            except Exception:
                pass
    send("quit")
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    return {"best": best, "nodes": nodes, "ms": round(elapsed, 1), "stop": needed_stop}


def main():
    positions = json.load(open(POSFILE))["positions"]
    rows = []
    t0 = time.time()
    for threads in THREADS:
        for clock in CLOCKS:
            mates = 0
            zero_nodes = 0
            worst = 0.0
            late = 0
            for p in positions:
                r = run(p["fen"], clock, threads)
                if r["best"] == p["mate_move"]:
                    mates += 1
                if r["nodes"] == 0 or r["nodes"] is None:
                    zero_nodes += 1
                worst = max(worst, r["ms"])
                if r["ms"] > clock * 1.5 + 100:
                    late += 1
            rows.append({"threads": threads, "clock": clock, "n": len(positions),
                         "mate_move": mates, "zero_nodes": zero_nodes,
                         "worst_ms": worst, "late": late})
            print(f"Threads {threads:2d} wtime {clock:3d}: mate-move {mates:2d}/{len(positions)}  "
                  f"0-nodes {zero_nodes:2d}  worst {worst:7.1f} ms  late {late}", flush=True)
    json.dump({"rows": rows, "positions": len(positions)}, open(OUT, "w"), indent=1)
    print(f"total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
