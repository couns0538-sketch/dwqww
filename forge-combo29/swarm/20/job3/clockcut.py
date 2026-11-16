#!/usr/bin/env python3
"""clockcut.py — seat 20. Do CLOCKED searches ('go wtime ...') also return an unsearched move when the
budget is tiny? Interactive driver: send go, wait for bestmove, record info depth count and move.

Criterion (stated before the run): UNSEARCHED = a `bestmove` with ZERO `info depth` lines before it.
Reference move = the engine's own choice with a normal budget (go depth 12, same position).
"""
import subprocess
import sys
import threading
import time

EXE = sys.argv[1]
FENS = {
    "startpos": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "italian": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1",
    "midgame": "r2q1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 1",
}


def ask(exe, fen, go, timeout=30.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []

    def rdo():
        for line in p.stdout:
            out.append(line.rstrip("\n"))
    threading.Thread(target=rdo, daemon=True).start()
    for cmd in ("uci", "setoption name OwnBook value false", "isready", "ucinewgame", "isready",
                f"position fen {fen}"):
        p.stdin.write(cmd + "\n")
    p.stdin.flush()
    t0 = time.monotonic()
    p.stdin.write(go + "\n")
    p.stdin.flush()
    while time.monotonic() - t0 < timeout:
        if any(x.startswith("bestmove") for x in out):
            break
        time.sleep(0.002)
    elapsed = time.monotonic() - t0
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if any("book move" in x for x in out):
        return (-1, "BOOK", elapsed, out)
    depths = [x for x in out if x.startswith("info depth")]
    bm = [x for x in out if x.startswith("bestmove")]
    return (len(depths), bm[-1].split()[1] if bm else "<none>", elapsed, out)


print(f"exe={EXE}  nproc-check: see meta.txt")
print()
GOS = ["go depth 12", "go wtime 1000 btime 1000", "go wtime 100 btime 100", "go wtime 30 btime 30",
       "go wtime 10 btime 10", "go wtime 5 btime 5", "go wtime 1 btime 1", "go wtime 0 btime 0",
       "go movetime 50", "go movetime 10", "go movetime 1", "go nodes 500", "go nodes 1"]
print(f"{'fen':9s} {'go':24s} {'runs':>4s} {'unsearched':>10s} {'moves seen':28s} {'ref(depth12)':12s}")
for name, fen in FENS.items():
    ref = ask(EXE, fen, "go depth 12")[1]
    for go in GOS:
        uns = 0
        moves = []
        nd = []
        for _ in range(5):
            n, bm, el, _raw = ask(EXE, fen, go)
            nd.append(n)
            moves.append(bm)
            if n == 0 and bm != "<none>":
                uns += 1
        uniq = ",".join(sorted(set(moves)))
        flag = "  <== UNSEARCHED" if uns else ""
        print(f"{name:9s} {go:24s} {5:4d} {uns:10d} {uniq:28s} {ref:12s}{flag}")
