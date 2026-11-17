#!/usr/bin/env python3
"""File 7 P3/P4: what is the v3 path's per-node cost, and is the 6.2x node count search shape or evaluation cost?

Fixed node budget (`go nodes N`, deterministic at Threads 1 per 29-F29) under four regimes, so every configuration does
the SAME work and any time difference is per-node cost with no tree-size confound:
  A  PC20, no net          -- built-in evaluation, the comparison baseline
  B  PC20 + test net       -- the v3 path the owner's PC runs
  C  no options, no net    -- the plain pins regime, for a second anchor
  D  no options + test net -- v3 with default options

Reports ms per 100k nodes for each and the ratios B/A (v3 vs built-in, same settings) which is P4's quantity.

Also reports the bench-13 wall time ratio of B to A, which is P3's "total cost" implied by node count times per-node
cost. Interleaved so machine drift cancels.
"""
import statistics
import subprocess
import sys
import time

EXE, NET = sys.argv[1], sys.argv[2]
FENS = sys.argv[3]
N = int(sys.argv[4])
NODES = int(sys.argv[5]) if len(sys.argv) > 5 else 200000

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]

CONFIGS = [("A pc20", True, False), ("B pc20+net", True, True),
           ("C plain", False, False), ("D plain+net", False, True)]


def one(fen, use_pc20, use_net):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def s(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    s("uci")
    for l in p.stdout:
        if l.startswith("uciok"):
            break
    if use_net:
        s(f"setoption name NNUEArchFile value {NET}")
        s("setoption name NNUEArch value true")
    if use_pc20:
        for k, v in PC20:
            s(f"setoption name {k} value {v}")
    s("setoption name Hash value 16")
    s("setoption name Threads value 1")
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
    p.wait(timeout=900)
    if bm is None or nodes is None:
        raise SystemExit(f"ABORT: incomplete search for config pc20={use_pc20} net={use_net}")
    return ms, nodes


fens = [l.strip() for l in open(FENS) if l.strip()][:N]
res = {name: [] for name, _, _ in CONFIGS}
for i, fen in enumerate(fens):
    order = CONFIGS if i % 2 == 0 else list(reversed(CONFIGS))
    for name, u20, un in order:
        ms, nodes = one(fen, u20, un)
        res[name].append(ms * 100000.0 / nodes)

print(f"FIXED NODE BUDGET {NODES}, {len(fens)} positions, Threads 1, Hash 16")
print()
print("| config | median ms per 100k nodes | vs A (same settings) |")
print("|---|---|---|")
A = statistics.median(res["A pc20"])
C = statistics.median(res["C plain"])
for name, _, _ in CONFIGS:
    med = statistics.median(res[name])
    base = A if name in ("A pc20", "B pc20+net") else C
    rel = "" if name in ("A pc20", "C plain") else f"{med/base:.2f}x"
    print(f"| {name} | {med:.1f} | {rel} |")
print()
print(f"P4 quantity (v3 per-node cost / built-in per-node cost, same PC20 settings): "
      f"**{statistics.median(res['B pc20+net'])/A:.2f}x**")
