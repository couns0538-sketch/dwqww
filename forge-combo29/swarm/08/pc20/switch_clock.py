#!/usr/bin/env python3
"""switch_clock.py OUT — does any single PC20 search switch change CLOCK behaviour?

08-F16 showed the four switches AS A BUNDLE leave the clock arithmetic identical to the base tree. This isolates
them: the same clock controls under S14 (baseline) and under S14 + each switch alone. If the clock medians are equal
within noise for every arm, no switch is responsible and the identity in F16 is a property of the clock code, not of
a lucky cancellation.

Controls measured: `go movetime 50` and `go wtime 1000 btime 1000 winc 0` — 60 searches each arm on the first 60 of
OG200 (60 is enough to see a median shift of >2 ms given the 0.2-0.5 % repeatability measured in 08-F4), Threads 1,
Hash 16, OwnBook false, fresh process per arm, `ucinewgame` before every search.

ARGUMENT ORDER: OUT first.
"""
import json
import subprocess
import sys
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
FENS = [l.strip() for l in open("../job1/OG200.fens") if l.strip()][:60]

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]

ARMS = [("S14 baseline", []),
        ("+ CuckooRep", [("CuckooRep", "true")]),
        ("+ HistRework 2", [("HistRework", "2")]),
        ("+ TtPruneV2", [("TtPruneV2", "true")]),
        ("+ CorrHistV2", [("CorrHistV2", "true")]),
        ("+ MateAlphaGuard", [("MateAlphaGuard", "true")])]

GOS = ["movetime 50", "wtime 1000 btime 1000 winc 0 binc 0", "wtime 10000 btime 10000 winc 0 binc 0"]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def measure(extra, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def read_until(tok, timeout=120.0):
        t0 = time.monotonic()
        got = []
        while True:
            if time.monotonic() - t0 > timeout:
                raise TimeoutError("no %r" % tok)
            l = p.stdout.readline()
            if not l:
                raise EOFError
            l = l.rstrip("\n")
            for b in BAD:
                if b in l:
                    raise RuntimeError("refused: %r" % l)
            got.append(l)
            if l.startswith(tok):
                return got

    def sync():
        send("isready")
        return read_until("readyok")

    send("uci")
    read_until("uciok")
    for n, v in S14 + extra + [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]:
        send("setoption name %s value %s" % (n, v))
        sync()
    walls = []
    depths = []
    nodes = []
    for fen in FENS:
        send("ucinewgame")
        sync()
        send("position fen " + fen)
        sync()
        t0 = time.monotonic()
        send("go " + go)
        lines = read_until("bestmove")
        walls.append((time.monotonic() - t0) * 1000.0)
        lastd = None
        lastn = None
        for l in lines:
            if l.startswith("info depth"):
                t = l.split()
                try:
                    lastd = int(t[2])
                    if "nodes" in t:
                        lastn = int(t[t.index("nodes") + 1])
                except (IndexError, ValueError):
                    pass
        depths.append(lastd)
        nodes.append(lastn)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return walls, depths, nodes


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q / 100.0
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


out = []
def emit(s):
    out.append(s)
    print(s)

import os
CACHE = OUT + ".cache.json"
results = {}
if os.path.exists(CACHE):
    raw = json.load(open(CACHE))
    for k, v in raw.items():
        label, go = k.split("||")
        results[(label, go)] = (v["w"], v["d"], v["n"])
    print("loaded %d cells from cache" % len(results))
else:
    for label, extra in ARMS:
        for go in GOS:
            w, d, n = measure(extra, go)
            results[(label, go)] = (w, d, n)
            print("done %-16s %-42s median %.2f" % (label, go, pct(w, 50)))
    json.dump({(l + "||" + g): {"w": v[0], "d": v[1], "n": v[2]} for (l, g), v in results.items()},
              open(CACHE, "w"))

emit("## Does any single switch change the CLOCK? PC r15, Threads 1, 60 searches per cell")
emit("")
emit("Columns: achieved time = median wall ms; depth reached = median of the last completed depth; nodes = median.")
emit("A switch changes the CLOCK only if the achieved time moves; it changes the SEARCH if depth/nodes move.")
emit("")
for go in GOS:
    emit("### `go %s`" % go)
    emit("")
    emit("| switch (alone, on S14) | achieved time ms | depth reached | nodes | time vs baseline | depth vs baseline |")
    emit("|---|---|---|---|---|---|")
    bw, bd, bn = results[("S14 baseline", go)]
    bmed, bdmed, bnmed = pct(bw, 50), pct([x for x in bd if x is not None], 50), pct([x for x in bn if x is not None], 50)
    for label, _ in ARMS:
        w, d, n = results[(label, go)]
        dd = [x for x in d if x is not None]
        nn = [x for x in n if x is not None]
        med = pct(w, 50)
        dm = pct(dd, 50) if dd else float("nan")
        nm = pct(nn, 50) if nn else float("nan")
        emit("| %s | %.2f | %.0f | %.0f | %+.2f ms | %+.0f |" %
             (label, med, dm, nm, med - bmed, dm - bdmed))
    emit("")

emit("## verdict")
emit("")
worst_t = 0.0
worst_d = 0.0
for label, _ in ARMS:
    if label == "S14 baseline":
        continue
    for go in GOS:
        w, d, n = results[(label, go)]
        bw, bd, bn = results[("S14 baseline", go)]
        worst_t = max(worst_t, abs(pct(w, 50) - pct(bw, 50)))
        dd = [x for x in d if x is not None]
        bdd = [x for x in bd if x is not None]
        if dd and bdd:
            worst_d = max(worst_d, abs(pct(dd, 50) - pct(bdd, 50)))
emit("| quantity | value |")
emit("|---|---|")
emit("| largest achieved-time shift from any single switch | **%.2f ms** |" % worst_t)
emit("| largest depth shift from any single switch | **%.0f plies** |" % worst_d)
emit("| repeatability of an identical run on this box (08-F4) | 0.20 %% of total time |")
emit("")
if worst_t < 2.0:
    emit("**No single switch moves the achieved time by as much as 2 ms**, while the depth column shows which "
         "switches change the SEARCH (if any do). So the clock arithmetic is untouched by every switch, including "
         "MateAlphaGuard — 08-F16's identity is a property of the clock code, not a cancellation.")
else:
    emit("**A switch DOES shift the achieved time** by up to %.2f ms — see the table." % worst_t)

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
