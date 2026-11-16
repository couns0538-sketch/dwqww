#!/usr/bin/env python3
"""Is the TT patch worth more on deep search than on bench? (probe_body is 3.65-4.86 % deep vs 1.4-2.0 % bench.)

Interleaved: for each of N positions, run base then patch (order flipping), one fresh process per search so the
table is COLD (seat 10's rule: a fresh process or ucinewgame), same depth for both. Reports the per-position node
count (must be identical) and the wall-ms ratio, so this is a PC-relevant measurement rather than a bench one.
"""
import statistics, subprocess, sys

BASE, PATCH = sys.argv[1], sys.argv[2]
FENS = [l.strip() for l in open(sys.argv[3]) if l.strip()][:40]
DEPTH = 12


def one(exe, fen):
    cmds = ["uci", "setoption name Hash value 16", "setoption name Threads value 1",
            "setoption name OwnBook value false", "isready", f"position fen {fen}", f"go depth {DEPTH}"]
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    import time
    for c in cmds[:-1]:
        p.stdin.write(c + "\n"); p.stdin.flush()
        if c == "isready":
            for line in p.stdout:
                if line.startswith("readyok"):
                    break
    t0 = time.monotonic()
    p.stdin.write(cmds[-1] + "\n"); p.stdin.flush()
    nodes = None
    for line in p.stdout:
        if line.startswith("info depth"):
            f = line.split(); nodes = int(f[f.index("nodes") + 1])
        if line.startswith("bestmove"):
            break
    ms = (time.monotonic() - t0) * 1000
    p.stdin.write("quit\n"); p.stdin.flush(); p.wait()
    if nodes is None:
        raise SystemExit(f"ABORT: no info line for {fen} -- refusing to record a zero")
    return ms, nodes


pairs = []
for i, fen in enumerate(FENS):
    if i % 2 == 0:
        b, q = one(BASE, fen), one(PATCH, fen)
    else:
        q, b = one(PATCH, fen), one(BASE, fen)
    if b[1] != q[1]:
        raise SystemExit(f"ABORT: node counts differ on {fen}: base {b[1]} patch {q[1]}")
    pairs.append((b[0], q[0], b[1]))
    print(f"{i+1:2d} nodes {b[1]:>8} base {b[0]:7.1f} ms  patch {q[0]:7.1f} ms  ratio {q[0]/b[0]:.3f}")

bt = [x[0] for x in pairs]; pt = [x[1] for x in pairs]
r = [y / x for x, y in zip(bt, pt)]
print()
print(f"positions {len(pairs)}, all node counts identical (cold, fresh process each)")
print(f"base  median {statistics.median(bt):7.1f} ms   patch median {statistics.median(pt):7.1f} ms")
print(f"total wall base {sum(bt):8.1f} ms   patch total {sum(pt):8.1f} ms")
print(f"mean ratio patch/base = {statistics.mean(r):.4f}  (median {statistics.median(r):.4f})")
