#!/usr/bin/env python3
"""abba.py EXE_A EXE_B OUTDIR [BLOCKS] : ABBA timing of two builds on a fixed node budget.

Fixed `go nodes 20000` (no clock), Threads 1, Hash 16, PC20 + test net, one fresh process per search, alternating
A-B-B-A so slow drift in the machine cancels. Reports per-block and pooled medians, the ratio of medians with a
bootstrap 95 % interval, the per-position spread, and the run count.

File 7 Step 3: two builds of each side would be ideal; this times one build of each, which is stated as a limit.
"""
import os
import random
import re
import statistics
import subprocess
import sys
import time

A, B, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3]
BLOCKS = int(sys.argv[4]) if len(sys.argv) > 4 else 30
os.makedirs(OUTDIR, exist_ok=True)
NODES = 20000
NET = "/tmp/test.fnn3"
FENS = "/tmp/OG200.fens"

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]

fens = [l.strip() for l in open(FENS) if l.strip()]
rng = random.Random(20261116)


def timed(exe, fen):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def snd(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def rto(tok, lim=120):
        dl = time.monotonic() + lim
        while time.monotonic() < dl:
            l = p.stdout.readline()
            if not l:
                return False
            if l.strip().startswith(tok):
                return True
        return False

    snd("uci"); rto("uciok", 30)
    for n, v in [("Threads", 1), ("Hash", 16)] + PC20:
        snd(f"setoption name {n} value {v}"); snd("isready"); rto("readyok", 30)
    snd(f"setoption name NNUEArchFile value {NET}"); snd("isready"); rto("readyok", 30)
    snd("setoption name NNUEArch value true"); snd("isready"); rto("readyok", 30)
    snd("ucinewgame"); snd("isready"); rto("readyok", 30)
    snd("position fen " + fen); snd("isready"); rto("readyok", 30)
    t0 = time.monotonic()
    snd(f"go nodes {NODES}")
    ok = rto("bestmove", 120)
    dt = (time.monotonic() - t0) * 1000.0
    snd("quit")
    try:
        p.wait(timeout=15)
    except Exception:
        p.kill()
    if not ok:
        raise RuntimeError("no bestmove")
    return dt


rows = []
print(f"blocks {BLOCKS}, {NODES} nodes each, A={A} B={B}")
for blk in range(BLOCKS):
    fen = fens[rng.randrange(len(fens))]
    # ABBA
    ta1 = timed(A, fen)
    tb1 = timed(B, fen)
    tb2 = timed(B, fen)
    ta2 = timed(A, fen)
    rows.append((blk, fen, ta1, tb1, tb2, ta2))
    if (blk + 1) % 5 == 0:
        print(f"  block {blk+1}/{BLOCKS}", flush=True)

a = [x for r in rows for x in (r[2], r[5])]
b = [x for r in rows for x in (r[3], r[4])]
med_a, med_b = statistics.median(a), statistics.median(b)
ratio = med_a / med_b          # >1 means B is faster (less time)

# bootstrap over BLOCKS (the independent unit) of the ratio of per-block medians
boot = []
for _ in range(4000):
    sample = [rows[rng.randrange(len(rows))] for _ in rows]
    sa = statistics.median([x for r in sample for x in (r[2], r[5])])
    sb = statistics.median([x for r in sample for x in (r[3], r[4])])
    if sb > 0:
        boot.append(sa / sb)
boot.sort()
lo, hi = boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot))]

# per-block spread: the ratio computed inside each block
per_block = [r[2] / r[3] if r[3] else 0 for r in rows]

lines = [
    f"A (baseline)  {A}",
    f"B (patched)   {B}",
    f"budget        go nodes {NODES}, Threads 1, Hash 16, PC20 + test net, fresh process per search",
    f"blocks        {BLOCKS} (ABBA), {len(a)} A-runs and {len(b)} B-runs",
    "",
    f"median A {med_a:.2f} ms   median B {med_b:.2f} ms",
    f"ratio of medians A/B = {ratio:.4f}   bootstrap 95% CI [{lo:.4f}, {hi:.4f}]",
    f"  interpretation: >1 means B is FASTER; a CI containing 1.0 means no effect detected",
    "",
    f"per-block spread of A/B: min {min(per_block):.3f} median {statistics.median(per_block):.3f} "
    f"max {max(per_block):.3f}",
    f"A runs: min {min(a):.2f} median {med_a:.2f} max {max(a):.2f} ms",
    f"B runs: min {min(b):.2f} median {med_b:.2f} max {max(b):.2f} ms",
]
text = "\n".join(lines) + "\n"
print(text)
with open(os.path.join(OUTDIR, "abba.txt"), "w") as fh:
    fh.write(text + "\nblock\tfen\tA1\tB1\tB2\tA2\n")
    for r in rows:
        fh.write(f"{r[0]}\t{r[1]}\t{r[2]:.3f}\t{r[3]:.3f}\t{r[4]:.3f}\t{r[5]:.3f}\n")
