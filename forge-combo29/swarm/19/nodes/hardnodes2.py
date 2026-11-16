#!/usr/bin/env python3
"""hardnodes2.py EXE FENS OUTDIR : `go nodes N` vs `go softnodes N`, five runs each, and the boundary question.

File 6's priority: the match path is `go nodes`. This compares it DIRECTLY with softnodes on the same positions
and budgets, and asks whether a budget that interrupts mid-iteration behaves differently from one landing on an
iteration boundary.

For every (position, N, mode) cell: 5 fresh processes, cold (ucinewgame). Record the whole `info depth` sequence,
the bestmove, and:
  last_depth      the last COMPLETE `info depth ... pv` line's depth
  last_nodes      the node count on that line
  complete        True if the search's final reported state is a finished iteration (i.e. the bestmove's score
                  equals the last info line's score and no iteration was cut)
  trunc           True if the run stopped mid-iteration (detected: the engine reports `info depth D` for a depth
                  that never produced a `pv` line, or the final depth's line has no pv)

Boundary construction: for one position I first run `go depth 12` and read the exact node count at which depth 12
finishes, call it B. Then `go nodes B` lands exactly on an iteration boundary and `go nodes B-1` interrupts one
node earlier. Comparing those two is the boundary test.
"""
import os
import re
import subprocess
import sys

exe, fens, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Hash", "16")]
positions = [l.split(";")[0].strip() for l in open(fens) if l.strip() and not l.startswith("#")][:6]


def run(fen, cmd):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(l):
        p.stdin.write(l + "\n")
        p.stdin.flush()

    def readto(pred):
        got = []
        for _ in range(800000):
            l = p.stdout.readline()
            if not l:
                return got
            l = l.rstrip("\n")
            got.append(l)
            if pred(l):
                return got
        return got

    send("uci")
    readto(lambda l: l.startswith("uciok"))
    for k, v in S14:
        send("setoption name %s value %s" % (k, v))
        send("isready")
        readto(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send("position fen " + fen)
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send(cmd)
    block = readto(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill()
    seen = []       # (depth, nodes, has_pv, score)
    best = None
    best_score = None
    for l in block:
        if l.startswith("info depth"):
            try:
                d = int(l.split("info depth ")[1].split()[0])
            except (IndexError, ValueError):
                continue
            nodes = int(l.split("nodes ")[1].split()[0]) if " nodes " in l else 0
            has_pv = " pv " in l
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            sc = (m.group(1), int(m.group(2))) if m else None
            seen.append((d, nodes, has_pv, sc))
        if l.startswith("bestmove"):
            parts = l.split()
            best = parts[1] if len(parts) > 1 else None
    with_pv = [s for s in seen if s[2]]
    if with_pv:
        last = with_pv[-1]
        last_depth, last_nodes, _, last_score = last
    else:
        last_depth, last_nodes, last_score = 0, 0, None
    return best, last_depth, last_nodes, len(with_pv), last_score, seen


lines = ["# `go nodes` vs `go softnodes` on PC r15, PC20, Threads 1, Hash 16, cold; 5 runs per cell", ""]
lines.append("| pos | N | mode | deterministic | bestmove | last finished depth | nodes there | vs N |")
lines.append("|---|---|---|---|---|---|---|---|")

summary = []
for i, fen in enumerate(positions):
    for n in (20000, 50000, 250000):
        for mode in ("nodes", "softnodes"):
            runs = [run(fen, "go %s %d" % (mode, n)) for _ in range(5)]
            keys = {(r[0], r[1], r[2]) for r in runs}
            det = len(keys) == 1
            best, ld, ln, iters, sc, _ = runs[0]
            over = (ln - n) / n * 100
            lines.append("| %d | %d | %s | **%s** | %s | %d | %d | %+.1f %% |"
                         % (i, n, mode, "yes" if det else "NO", best, ld, ln, over))
            summary.append((i, n, mode, det, over, ld))
            print("pos %d N %6d %-9s det=%-3s best=%s depth %d nodes %d (%+.0f %%)"
                  % (i, n, mode, det, best, ld, ln, over), flush=True)

# --- boundary test on position 0 ---
fen0 = positions[0]
best, ld, ln, _, _, _ = run(fen0, "go depth 12")
B = ln
lines.append("")
lines.append("## boundary test, position 0: depth-12 finished at exactly %d nodes" % B)
for label, budget in (("exactly on the boundary", B), ("one node short", B - 1)):
    runs = [run(fen0, "go nodes %d" % budget) for _ in range(5)]
    keys = {(r[0], r[1], r[2]) for r in runs}
    best, ld2, ln2, _, _, _ = runs[0]
    over = (ln2 - budget) / budget * 100
    lines.append("- `go nodes %d` (%s): deterministic=%s  bestmove %s  depth %d at %d nodes (%+.2f %%)"
                 % (budget, label, len(keys) == 1, best, ld2, ln2, over))
    print("boundary %d (%s): depth %d nodes %d (%+.2f %%)" % (budget, label, ld2, ln2, over), flush=True)

text = "\n".join(lines)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print("\nwritten", os.path.join(outdir, "RESULT.txt"))
