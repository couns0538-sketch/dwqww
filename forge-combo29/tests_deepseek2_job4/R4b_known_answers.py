#!/usr/bin/env python3
"""Job 4 part A: the known-answer table across three builds.

Each row is one `go` line, sent to a fresh process from the start position after
`e2e4`, with `Threads 1`, `OwnBook false`, `Move Overhead 10` unless the line says
otherwise.  "At once" means `bestmove` arrived within 150 ms without `stop`.

Builds: --unpatched, --r4 (job 3's R4 as delivered), --r4b (this job's repair).
The script prints one row per line with the three verdicts side by side and the
exact fields where they are visible from the outside (bestmove, ms, nodes).
"""

import json
import queue
import subprocess
import sys
import threading
import time

AT_ONCE_MS = 150.0
WAIT_MS = 5000.0


def one(engine, line, overhead=10):
    p = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
                ln = q.get(timeout=max(0.01, limit - (time.time() - t0)))
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
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send(f"setoption name Move Overhead value {overhead}")
    send("setoption name OwnBook value false")
    send("isready")
    collect(lambda l: l.strip() == "readyok", 10)
    send("position startpos moves e2e4")
    t0 = time.time()
    send(line)
    got, answered = collect(lambda l: l.startswith("bestmove"), WAIT_MS / 1000.0)
    elapsed = (time.time() - t0) * 1000.0
    needed_stop = False
    if not answered:
        send("stop")
        more, answered = collect(lambda l: l.startswith("bestmove"), 3.0)
        got += more
        needed_stop = True
        elapsed = (time.time() - t0) * 1000.0
    best = None
    nodes = None
    depth = None
    for ln in got:
        if ln.startswith("bestmove"):
            best = ln.split()[1]
        if " nodes " in ln:
            try:
                nodes = int(ln.split(" nodes ")[1].split()[0])
            except Exception:
                pass
        if ln.startswith("info depth"):
            try:
                depth = int(ln.split()[1])
            except Exception:
                pass
    send("quit")
    try:
        p.wait(timeout=5)
        rc = p.returncode
    except Exception:
        p.kill()
        rc = "killed"
    return {"line": line, "best": best, "ms": round(elapsed), "nodes": nodes,
            "depth": depth, "stop": needed_stop, "exit": rc,
            "at_once": (not needed_stop) and elapsed <= AT_ONCE_MS}


LINES = [
    "go wtime -50 btime -50",
    "go wtime 0 btime 0",
    "go movetime -1",
    "go depth 0",
    "go depth -3",
    "go nodes -1",
    "go nodes 0",
    "go wtime btime 50",
    "go movestogo 0 wtime 2000 btime 2000",
    "go mate 0",
    "go btime wtime 2000 btime 2000",
    "go movetime 99999999999999999999 wtime 2000 btime 2000",
]


def main():
    unpatched, r4, r4b = sys.argv[1], sys.argv[2], sys.argv[3]
    out = sys.argv[4]
    rows = []
    for line in LINES:
        a = one(unpatched, line)
        b = one(r4, line)
        c = one(r4b, line)
        rows.append({"line": line, "unpatched": a, "r4": b, "r4b": c})
        print(f"{line:52s} unpatched {a['ms']:6d}ms at_once={str(a['at_once']):5s} | "
              f"R4 {b['ms']:6d}ms at_once={str(b['at_once']):5s} | "
              f"R4b {c['ms']:6d}ms at_once={str(c['at_once']):5s}", flush=True)
    json.dump(rows, open(out, "w"), indent=1)
    print()
    print(f"{'line':52s} {'unpatched':>26s} {'R4':>26s} {'R4b':>26s}")
    for r in rows:
        cells = []
        for key in ("unpatched", "r4", "r4b"):
            x = r[key]
            cells.append(f"{x['ms']}ms n={x['nodes']} d={x['depth']}"[:26])
        print(f"{r['line']:52s} {cells[0]:>26s} {cells[1]:>26s} {cells[2]:>26s}")


if __name__ == "__main__":
    main()
