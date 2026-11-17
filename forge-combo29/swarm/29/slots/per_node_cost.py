#!/usr/bin/env python3
"""Which PC20 switch carries the per-node cost? Fix the node budget, measure wall time.

29-F53 shows PC20 searches 10.7-11.9 % fewer nodes; 29-F56 shows no measurable wall-time saving. The obvious
explanation is extra per-node work. This isolates it: run at a FIXED NODE BUDGET (`go nodes N`, deterministic at
Threads 1 per 29-F29) so every configuration does the SAME work, then compare wall time. Any difference is per-node
cost, with no confound from tree size.

Configurations: S14 baseline, then S14 + ONE switch at a time, then all four (PC20's search switches minus the
bookkeeping-only ones). MateAlphaGuard and OwnBook are excluded from the comparison set because one is a guard and the
other disables the book, neither of which adds per-node work in the search.

Reports ms per 100k nodes, interleaved ABBA against the baseline so machine drift cancels.
"""
import random
import statistics
import subprocess
import sys
import time

EXE = sys.argv[1]
FENS = sys.argv[2]
N = int(sys.argv[3])
NODES = int(sys.argv[4]) if len(sys.argv) > 4 else 100000

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
SWITCHES = {
    "CuckooRep": [("CuckooRep", "true")],
    "HistRework2": [("HistRework", 2)],
    "TtPruneV2": [("TtPruneV2", "true")],
    "CorrHistV2": [("CorrHistV2", "true")],
}
ALL4 = [x for v in SWITCHES.values() for x in v]
CONFIGS = [("S14", [])] + [(k, v) for k, v in SWITCHES.items()] + [("all4", ALL4)]


def one(fen, extra):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def s(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    s("uci")
    for l in p.stdout:
        if l.startswith("uciok"):
            break
    s("setoption name Hash value 16")
    s("setoption name Threads value 1")
    for k, v in S14:
        s(f"setoption name {k} value {v}")
    for k, v in extra:
        s(f"setoption name {k} value {v}")
    s("isready")
    for l in p.stdout:
        if l.startswith("readyok"):
            break
    s(f"position fen {fen}")
    t0 = time.monotonic()
    s(f"go nodes {NODES}")
    nodes = bm = None
    for l in p.stdout:
        if l.startswith("info depth"):
            f = l.split()
            if "nodes" in f:
                nodes = int(f[f.index("nodes") + 1])
        if l.startswith("bestmove"):
            bm = l.split()[1]
            break
    ms = (time.monotonic() - t0) * 1000.0
    s("quit")
    p.wait(timeout=600)
    if bm is None or nodes is None:
        raise SystemExit(f"ABORT: incomplete search under {extra}")
    return ms, nodes


fens = [l.strip() for l in open(FENS) if l.strip()][:N]
results = {name: [] for name, _ in CONFIGS}
for i, fen in enumerate(fens):
    # interleave: baseline first or last, alternating by position index
    order = CONFIGS if i % 2 == 0 else list(reversed(CONFIGS))
    for name, extra in order:
        ms, nodes = one(fen, extra)
        results[name].append(ms * 100000.0 / nodes)   # ms per 100k nodes

print(f"FIXED NODE BUDGET {NODES} per search, {len(fens)} positions, Threads 1, Hash 16")
print()
print("| config | ms per 100k nodes (median) | vs S14 |")
print("|---|---|---|")
base = statistics.median(results["S14"])
for name, _ in CONFIGS:
    med = statistics.median(results[name])
    rel = 100.0 * (med - base) / base
    print(f"| {name} | {med:.1f} | {'—' if name == 'S14' else f'{rel:+.1f} %'} |")
print()
print("A config that raises ms/100k while searching the same number of nodes is carrying per-node cost.")
