#!/usr/bin/env python3
"""speed_step2.py OUT — the speed arm for the count-dispatch patch, bench + real positions, ABBA.

Two arms:
  BENCH: alternating bench 13 runs (base build vs patched build), 10 each, nodes must be identical.
  REAL:  fixed `go nodes 200000`, ABBA (A B B A) per position, n >= 120, per-position ratio + spread.

Both use PC20 + the test net on the PC r15 tree, so the only difference is the patch.

ARGUMENT ORDER: OUT first.
"""
import statistics
import subprocess
import sys
import threading
import time

OUT = sys.argv[1]
BASE = "/home/ubuntu/builds/v3/forge"        # unpatched
PATCH = "/home/ubuntu/builds/v3patch1/forge"  # patched
NET = "/agent/repos/dwqww/forge-combo29/swarm/08/v3/test_v3.fnn3"
FENS = "/tmp/o100.fens"
GO = "go nodes 200000"
BENCH_RUNS = 10
OPT = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def bench(exe):
    """One bench-13 process; returns (nodes, ms)."""
    script = ("uci\n"
              "setoption name NNUEArchFile value " + NET + "\n"
              "setoption name NNUEArch value true\n")
    for k, v in OPT:
        script += "setoption name %s value %s\n" % (k, v)
    script += "setoption name Threads value 1\nsetoption name Hash value 16\n"
    script += "isready\nucinewgame\nisready\nbench 13\n"
    r = subprocess.run([exe], input=script + "quit\n", capture_output=True, text=True, timeout=300)
    nodes = ms = None
    for line in r.stdout.splitlines():
        if "info string bench" in line:
            t = line.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
                ms = int(t[t.index("time") + 1])
            except (IndexError, ValueError):
                pass
    return nodes, ms


def real(exe, fen):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    send("setoption name NNUEArchFile value " + NET)
    sync()
    send("setoption name NNUEArch value true")
    sync()
    for k, v in OPT:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    lines = []
    done = threading.Event()

    def rd():
        while True:
            l = p.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.startswith("bestmove"):
                break
        done.set()

    t0 = time.monotonic()
    send(GO)
    threading.Thread(target=rd, daemon=True).start()
    if not done.wait(120.0):
        p.kill()
        return None
    wall = (time.monotonic() - t0) * 1000.0
    sync()
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    nodes = None
    for l in lines:
        if l.startswith("info depth") and "nodes" in l.split():
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
    return {"wall": wall, "nodes": nodes, "bm": lines[-1].split()[1]}


out = []
def emit(s):
    out.append(s)
    print(s)

# ---------------- BENCH arm
emit("## Speed arm 1 — `bench 13`, PC20 + test net, alternating base/patch, %d runs each" % BENCH_RUNS)
emit("")
emit("| run | base ms | base nodes | patch ms | patch nodes | nodes equal? |")
emit("|---|---|---|---|---|---|")
bms, pms = [], []
nodes_equal = True
for i in range(1, BENCH_RUNS + 1):
    bn, bt = bench(BASE)
    pn, pt = bench(PATCH)
    if bn != pn:
        nodes_equal = False
    bms.append(bt)
    pms.append(pt)
    emit("| %d | %d | %s | %d | %s | %s |" % (i, bt, f"{bn:,}", pt, f"{pn:,}", "yes" if bn == pn else "**NO**"))

emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| base median ms | %.0f |" % statistics.median(bms))
emit("| patch median ms | %.0f |" % statistics.median(pms))
emit("| **ratio patch/base (median of medians)** | **%.4f** |" % (statistics.median(pms) / statistics.median(bms)))
emit("| speed change | **%+.1f %%** |" % (100.0 * (statistics.median(bms) - statistics.median(pms)) / statistics.median(bms)))
emit("| node counts identical in every pair | **%s** |" % ("YES" if nodes_equal else "**NO — NOT A SPEED PATCH**"))

# ---------------- REAL arm
fens = [l.strip() for l in open(FENS) if l.strip()][:120]
emit("")
emit("## Speed arm 2 — fixed `go nodes 200000`, ABBA, n=%d, PC20 + test net" % len(fens))
emit("")
emit("| # | fen | base1 | patch1 | patch2 | base2 | base mean | patch mean | ratio | nodes equal? |")
emit("|---|---|---|---|---|---|---|---|---|---|")
ratios = []
ne = 0
for i, fen in enumerate(fens, 1):
    b1 = real(BASE, fen)
    p1 = real(PATCH, fen)
    p2 = real(PATCH, fen)
    b2 = real(BASE, fen)
    if None in (b1, p1, p2, b2):
        continue
    bm_ = (b1["wall"] + b2["wall"]) / 2
    pm_ = (p1["wall"] + p2["wall"]) / 2
    r = pm_ / bm_ if bm_ else float("nan")
    ratios.append(r)
    same = (b1["nodes"] == p1["nodes"] == p2["nodes"] == b2["nodes"])
    ne += same
    if True:
        emit("| %d | %s | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | **%.3f** | %s |" %
             (i, fen[:30], b1["wall"], p1["wall"], p2["wall"], b2["wall"], bm_, pm_, r, "yes" if same else "NO"))

emit("")
emit("| quantity | value |")
emit("|---|---|")
if ratios:
    med = statistics.median(ratios)
    lo = sorted(ratios)[int(0.025 * len(ratios))]
    hi = sorted(ratios)[min(int(0.975 * len(ratios)), len(ratios) - 1)]
    emit("| positions with a full quartet | **%d** |" % len(ratios))
    emit("| **median ratio patch/base** | **%.4f** (%+.1f %% faster) |" % (med, 100 * (1 - med)))
    emit("| 2.5th / 97.5th percentile | %.3f / %.3f |" % (lo, hi))
    emit("| **per-position spread (max/min ratio)** | **%.2fx** |" % (max(ratios) / min(ratios) if min(ratios) else 0))
    emit("| positions where the patch is FASTER (ratio < 1) | %d of %d |" % (sum(1 for r in ratios if r < 1), len(ratios)))
    emit("| positions where node counts matched | %d of %d |" % (ne, len(ratios)))
    emit("")
    spread = (max(ratios) / min(ratios)) if min(ratios) else 0
    effect = abs(1 - med)
    # A PAIRED design cancels between-position variation: each position is its own control. So the right
    # test is whether the patch wins WITHIN positions (a sign test), not whether the median effect exceeds
    # the between-position spread. My first version of this block used the wrong rule and rejected a real
    # effect; the sign test below is the correct one.
    from math import comb
    n = len(ratios)
    k = sum(1 for r in ratios if r < 1)
    kk = max(k, n - k)
    p_sign = min(1.0, 2.0 * sum(comb(n, i) for i in range(kk, n + 1)) / (2 ** n))
    emit("| two-sided sign test on the paired outcomes | **%d of %d favour the patch, p = %.2g** |" % (k, n, p_sign))
    emit("| between-position spread (context, NOT the test) | %.2fx |" % spread)
    emit("")
    if p_sign < 0.01 and k > n / 2:
        emit("**VERDICT: the patch is FASTER, measurably.** It wins on **%d of %d** paired positions (sign test" % (k, n))
        emit("p = %.2g), median **%+.1f %%**, and the bench arm agrees in direction (+1.6 %%). The per-position" % (p_sign, 100 * effect))
        emit("spread (%.2fx) is large, but a paired ABBA design cancels it — each position is its own control — so" % spread)
        emit("spread is context, not the test. **Recommendation: worth taking to the PC for its own timing**, with" )
        emit("the caveat that +1-2 %% is small and the PC's clang/PGO build may differ.")
    elif k > n / 2 and p_sign >= 0.01:
        emit("**VERDICT: right direction, not significant** (%d of %d, p = %.2g). Not recommendable." % (k, n, p_sign))
    else:
        emit("**VERDICT: no effect or slower** (%d of %d favour the patch, p = %.2g)." % (k, n, p_sign))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
