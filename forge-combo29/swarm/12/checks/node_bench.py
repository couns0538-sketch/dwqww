#!/usr/bin/env python3
"""node_bench.py EXE [--runs N] — a FIXED-NODE-COUNT benchmark, and a check of whether
`go nodes N` actually searches N nodes.

Why fixed nodes: the work is identical on every machine, so wall-ms per million nodes measures
MACHINE SPEED only. It does not involve Hash, MultiPV or any option, which is what makes it a
better absolute anchor than a depth-6 wall time (a depth search's work varies with pruning).

It also reports reported-nodes/N: if the engine stops well short of the requested count, then
"nodes per second" computed from the request is wrong, and the benchmark must use the reported
count instead. That is measured here rather than assumed.

Every run: fresh process, Threads 1, Hash 16, MultiPV 1, OwnBook false, startpos, and the harness
READS to `bestmove` before sending anything else (never pipelines `quit`).
"""
import queue
import re
import statistics
import subprocess
import sys
import threading
import time

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def run(exe, nodes, hash_mb=16, bound=180.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    out = []
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pred, limit):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            try:
                ln = q.get(timeout=0.2)
            except queue.Empty:
                if p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            out.append(ln)
            if pred(ln):
                return ln
        return None

    send("uci")
    wait(lambda l: l == "uciok", 30)
    for name, value in (("Hash", hash_mb), ("MultiPV", 1), ("Threads", 1),
                        ("OwnBook", "false")):
        send(f"setoption name {name} value {value}")
        send("isready")
        wait(lambda l: l == "readyok", 30)
    send(f"position fen {FEN}")
    send("isready")
    wait(lambda l: l == "readyok", 30)

    t0 = time.monotonic()
    send(f"go nodes {nodes}")
    bm = wait(lambda l: l.startswith("bestmove"), bound)
    wall = time.monotonic() - t0
    send("quit")
    try:
        p.stdin.close()
    except (OSError, ValueError):
        pass
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()

    reported = None
    depth = 0
    info = 0
    for l in out:
        if l.startswith("info depth"):
            info += 1
            m = re.search(r"^info depth (\d+)", l)
            if m:
                depth = max(depth, int(m.group(1)))
            n = re.search(r" nodes (\d+)", l)
            if n:
                reported = int(n.group(1))
    return {"requested": nodes, "reported": reported, "wall_s": wall, "depth": depth,
            "info_lines": info,
            "answered": isinstance(bm, str) and bm.startswith("bestmove")}


def main():
    exe = sys.argv[1]
    runs = 5
    if "--runs" in sys.argv:
        runs = int(sys.argv[sys.argv.index("--runs") + 1])
    print(f"exe {exe}   Threads 1, Hash 16, MultiPV 1, startpos, {runs} runs per count\n")
    print(f"{'requested':>10} {'reported':>10} {'ratio':>7} {'median ms':>10} {'min':>7} "
          f"{'max':>7} {'nps (reported)':>15}")
    out = []
    for n in (100000, 300000, 1000000):
        rs = [run(exe, n) for _ in range(runs)]
        ok = [r for r in rs if r["answered"] and r["info_lines"] > 0]
        if not ok:
            print(f"{n:>10} -- no completed search in {runs} runs --")
            continue
        ms = [r["wall_s"] * 1000 for r in ok]
        rep = ok[0]["reported"]
        med = statistics.median(ms)
        nps = rep / (med / 1000) if med else 0
        out.append({"requested": n, "reported": rep, "median_ms": round(med, 1),
                    "min_ms": round(min(ms), 1), "max_ms": round(max(ms), 1),
                    "nps": round(nps), "runs": len(ok)})
        print(f"{n:>10} {str(rep):>10} {rep/n:>7.2f} {med:>10.0f} {min(ms):>7.0f} "
              f"{max(ms):>7.0f} {nps:>15,.0f}")
    print()
    short = [r for r in out if r["reported"] and r["reported"] < r["requested"] * 0.98]
    if short:
        print("NOTE: `go nodes N` stopped short of N on:")
        for r in short:
            print(f"  requested {r['requested']:,} -> reported {r['reported']:,} "
                  f"({r['reported']/r['requested']:.0%}) — so any nodes/second figure must use the")
        print("  REPORTED count, not the requested one, or it is inflated.")
    # the anchor: ms per million REPORTED nodes, averaged over the runs that did the most work
    if out:
        best = out[-1]
        per_m = best["median_ms"] / (best["reported"] / 1e6)
        print(f"\nANCHOR: {per_m:,.0f} ms per million reported nodes "
              f"(from `go nodes {best['requested']:,}` = {best['reported']:,} nodes in "
              f"{best['median_ms']:.0f} ms)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
