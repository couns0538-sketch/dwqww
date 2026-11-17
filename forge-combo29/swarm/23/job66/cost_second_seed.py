#!/usr/bin/env python3
"""job66b : does F101's ~625 cp cost of generator index 0 hold on a DIFFERENT seed set?

F101 sampled every 400th line of the validated seed-2301 set and got a median 625.5 cp. One seed set is one fixture
family, so by the one-fixture rule this needs a second. Seed 2401 exists in the seat (job4/R_2301.fens is 2301; look for
a 2401 file) — if it is unavailable, use every 400th line of the same file OFFSET by 200, which is a disjoint sample from
the same generator and therefore a weaker but real second draw. Say which was used.
"""
import re, subprocess, os, sys, statistics
INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
MOVELINE = re.compile(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$")
SUM = re.compile(r"^nodes (\d+)$")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")
SRC = sorted([p for p in (sys.argv[1] if len(sys.argv) > 1 else "../job1/R_2301.fens",) if os.path.exists(p)])[0]


def conn(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    o = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if s.startswith("option name "):
            o.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in o:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def perft1(p, fen):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go perft 1\n"); p.stdin.flush()
    order = []
    tot = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in perft")
        s = l.strip()
        m = MOVELINE.match(s)
        if m:
            order.append(m.group(1))
        ms = SUM.match(s)
        if ms:
            tot = int(ms.group(1))
            break
    return order, tot


def search(p, fen, depth=12):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
        if s.startswith("bestmove"):
            return last, s.split()[1]


def score_after(pc, fen, move, depth=12):
    import chess
    b = chess.Board(fen)
    b.push(chess.Move.from_uci(move))
    (kind, val, nodes), bm = search(pc, b.fen(), depth)
    if kind == "mate":
        stm = (100000 - 1000 * val) if val > 0 else (-100000 - 1000 * val)
        return -stm, kind
    return -val, kind


fens = [l.strip() for l in open(SRC) if l.strip()]
OFFSET = int(sys.argv[2]) if len(sys.argv) > 2 else 200
sample = [fens[i] for i in range(OFFSET, min(len(fens), OFFSET + 400 * 12), 400)][:12]
print("source: %s | offset %d | %d positions (DISJOINT from F101's offset-0 sample)" % (SRC, OFFSET, len(sample)))
print()
cb = conn(BASE)
cp_ = conn(PC)
print("| # | g0 | searched best | score after g0 | score after best | cost |")
print("|---|---|---|---|---|---|")
costs = []
absurd = 0
for i, fen in enumerate(sample, 1):
    order, tot = perft1(cb, fen)
    if not order or tot != len(order):
        print("| %d | **PARSE FAILURE** (%d vs %s) | - | - | - | - |" % (i, len(order), tot))
        absurd += 1
        continue
    g0 = order[0]
    (bk, bv, bn), best = search(cb, fen, 12)
    s_g0, k_g0 = score_after(cp_, fen, g0)
    s_best, k_best = score_after(cp_, fen, best)
    cost = s_best - s_g0
    if cost < -200 and k_best != "mate":
        print("| %d | **ABSURDITY %d** | %s | %s | %s | %s |" % (i, -cost, g0, best, s_g0, s_best))
        absurd += 1
        continue
    costs.append(cost)
    print("| %d | %s | %s | %s | %s | **%d** |" % (i, g0, best, s_g0, s_best, cost))
cb.stdin.write("quit\n"); cb.stdin.flush()
cp_.stdin.write("quit\n"); cp_.stdin.flush()
print()
if costs:
    print("parsed %d, absurd %d" % (len(costs), absurd))
    print("costs:", costs)
    print("median: %.1f | min %d | max %d | >=300 cp: %d of %d" % (
        statistics.median(costs), min(costs), max(costs), sum(1 for c in costs if c >= 300), len(costs)))
