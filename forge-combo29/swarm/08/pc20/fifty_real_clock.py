#!/usr/bin/env python3
"""fifty_real_clock.py OUT — does the 43-million-node high-counter case fit the owner's real clock, and does time
management cope?

The residual question from my fifty-move withdrawal: at H=91 the engine needs ~43M nodes to reach depth 20 (a
search that takes ~20 s at ~2M nps). On a 6 s + 0.06 clock it cannot finish that. Does the time manager handle it,
and does the MOVE degrade?

Method: the SAME board at H=0 and H=91, `go wtime 6000 btime 6000 winc 60 binc 60`, PC20, Threads 1, 3 fresh
processes each. Record depth reached, wall time, bestmove, score, and the deep reference (depth 20) bestmove so
"degraded move" is measurable rather than judged.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - %d 1"
CLOCK = "go wtime 6000 btime 6000 winc 60 binc 60"
RUNS = 3
COUNTERS = [0, 91]


def probe(counter, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            if l.startswith("readyok"):
                return

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + (FEN % counter))
    sync()
    t0 = time.monotonic()
    send(go)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        l = l.rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    wall = (time.monotonic() - t0) * 1000.0
    sync()
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    score = nodes = None
    maxd = 0
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                d = int(t[2])
                maxd = max(maxd, d)
                if "score" in t and "nodes" in t:
                    si = t.index("score")
                    score = "%s %s" % (t[si + 1], t[si + 2])
                    nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
    return {"wall": wall, "bm": lines[-1].split()[1], "score": score, "depth": maxd, "nodes": nodes}


out = []
def emit(s):
    out.append(s)
    print(s)

# deep references first, so "degraded" is measurable
ref = {}
for c in COUNTERS:
    r = probe(c, "go depth 20")
    ref[c] = r
    print("reference H=%d: depth %d bestmove %s score %s (%s nodes, %.0f ms)"
          % (c, r["depth"], r["bm"], r["score"], f"{r['nodes']:,}" if r["nodes"] else "?", r["wall"]))

emit("## The H=91 case at the owner's real clock (6 s + 0.06), PC r15, PC20, Threads 1")
emit("")
emit("| H | run | depth reached | wall ms | nodes | score | bestmove | deep (depth 20) bestmove | move degraded? |")
emit("|---|---|---|---|---|---|---|---|---|")
rows = {}
for c in COUNTERS:
    runs = [probe(c, CLOCK) for _ in range(RUNS)]
    rows[c] = runs
    for i, r in enumerate(runs, 1):
        degraded = "—" if c == 0 else ("NO" if r["bm"] == ref[c]["bm"] else "**YES (differs from depth-20 ref)**")
        emit("| %d | %d | %d | %.1f | %s | %s | %s | %s | %s |" %
             (c, i, r["depth"], r["wall"], f"{r['nodes']:,}" if r["nodes"] else "-", r["score"], r["bm"],
              ref[c]["bm"], degraded))

emit("")
emit("## Verdict")
emit("")
emit("| question | H=0 | H=91 |")
emit("|---|---|---|")
r0, r91 = rows[0], rows[91]
emit("| depth reached on the 6 s clock | %s | %s |" %
     (", ".join(str(x["depth"]) for x in r0), ", ".join(str(x["depth"]) for x in r91)))
emit("| wall ms | %s | %s |" %
     (", ".join("%.0f" % x["wall"] for x in r0), ", ".join("%.0f" % x["wall"] for x in r91)))
emit("| bestmove | %s | %s |" %
     (", ".join(x["bm"] for x in r0), ", ".join(x["bm"] for x in r91)))
emit("| score | %s | %s |" %
     (", ".join(x["score"] for x in r0), ", ".join(x["score"] for x in r91)))
emit("| deep (depth 20) reference bestmove | %s | %s |" % (ref[0]["bm"], ref[91]["bm"]))
emit("")
worst91 = max(x["wall"] for x in r91)
over91 = sum(1 for x in r91 if x["wall"] > 6000)
emit("| quantity | value |")
emit("|---|---|")
emit("| worst wall at H=91 | %.0f ms |" % worst91)
emit("| runs at H=91 exceeding the 6000 ms clock | **%d of %d** |" % (over91, len(r91)))
emit("| H=91 bestmove == depth-20 reference | **%d of %d** |" %
     (sum(1 for x in r91 if x["bm"] == ref[91]["bm"]), len(r91)))
emit("")
if worst91 < 6000 and all(x["bm"] == ref[91]["bm"] for x in r91):
    emit("**CLOSED AS A COST TIME MANAGEMENT ABSORBS.** On the owner's clock the H=91 board never approaches the 6 s "
         "limit and plays the same move as a depth-20 search, so the 43M-node case does not degrade the move — the "
         "time manager simply stops at a shallower depth.")
else:
    emit("**OPEN — see the table.** Either the clock was approached or the move differed from the deep reference.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
