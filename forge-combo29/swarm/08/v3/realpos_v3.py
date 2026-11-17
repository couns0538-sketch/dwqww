#!/usr/bin/env python3
"""realpos_v3.py OUT — the real-position arm the coordinator required before ANY speed recommendation.

The bench is ~6x optimistic and its node ratios flip sign across benches (established earlier in this run). So this
measures on REAL positions with a FIXED NODE BUDGET, ABBA ordering, n>=120 per arm, and reports the per-position
spread — the four requirements named.

What is compared here is not a patch but a QUESTION the profile raised: the v3 path is 21.46 % of bench time and is
balanced across three functions, so is the v3 path itself expensive on real positions relative to the built-in
evaluation? That is measurable with two arms and gives the baseline any future patch must beat.

  arm A: PC20 + test net  (v3 path active)
  arm B: PC20, no net     (built-in evaluation)

ABBA: A B B A per position, so drift affects both arms equally. `go nodes 200000` fixes the WORK, so the comparison
is time-per-identical-work.

ARGUMENT ORDER: OUT first.
"""
import statistics
import subprocess
import sys
import threading
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/v3/forge"
NET = "/agent/repos/dwqww/forge-combo29/swarm/08/v3/test_v3.fnn3"
FENS = "/tmp/o100.fens"
GO = "go nodes 200000"
OPT = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]

fens = [l.strip() for l in open(FENS) if l.strip()][:120]   # n >= 120


def measure(fen, use_net):
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
    if use_net:
        send("setoption name NNUEArchFile value " + NET)
        sync()
        send("setoption name NNUEArch value true")
        sync()
    for k, v in OPT:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("setoption name Threads value 1")
    sync()
    send("setoption name Hash value 16")
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
    ok = done.wait(120.0)
    wall = (time.monotonic() - t0) * 1000.0
    if not ok:
        p.kill()
        return None
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

emit("## The REAL-POSITION arm: v3 net vs built-in evaluation, fixed nodes, ABBA, n=%d" % len(fens))
emit("")
emit("`%s`, PC20 both arms, Threads 1, Hash 16. ABBA = A B B A per position; A = +test net (v3), B = no net." % GO)
emit("")
emit("| # | fen | A1 ms | B1 ms | B2 ms | A2 ms | A mean | B mean | ratio A/B | nodes A | nodes B |")
emit("|---|---|---|---|---|---|---|---|---|---|---|")
ratios = []
rows = []
for i, fen in enumerate(fens, 1):
    a1 = measure(fen, True)
    b1 = measure(fen, False)
    b2 = measure(fen, False)
    a2 = measure(fen, True)
    if None in (a1, b1, b2, a2):
        continue
    am = (a1["wall"] + a2["wall"]) / 2
    bm = (b1["wall"] + b2["wall"]) / 2
    r = am / bm if bm else float("nan")
    ratios.append(r)
    rows.append({"fen": fen, "a": am, "b": bm, "r": r, "na": a1["nodes"], "nb": b1["nodes"]})
    if i <= 10 or i % 20 == 0:
        emit("| %d | %s | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | **%.3f** | %s | %s |" %
             (i, fen[:34], a1["wall"], b1["wall"], b2["wall"], a2["wall"], am, bm, r,
              f"{a1['nodes']:,}" if a1["nodes"] else "-", f"{b1['nodes']:,}" if b1["nodes"] else "-"))

emit("")
emit("## Summary")
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| positions with a complete ABBA quartet | **%d** |" % len(ratios))
if ratios:
    med = statistics.median(ratios)
    lo = sorted(ratios)[int(0.025 * len(ratios))]
    hi = sorted(ratios)[int(0.975 * len(ratios)) - 1]
    emit("| median ratio (v3 / built-in), time per identical node budget | **%.3f** |" % med)
    emit("| 2.5th / 97.5th percentile of the per-position ratio | %.3f / %.3f |" % (lo, hi))
    emit("| positions where v3 is SLOWER (ratio > 1) | %d of %d |" % (sum(1 for r in ratios if r > 1), len(ratios)))
    emit("| per-position spread (max/min ratio) | **%.2fx** |" % (max(ratios) / min(ratios) if min(ratios) else 0))
    # node identity: fixed node budget should give the same counts in both arms
    same_nodes = sum(1 for d in rows if d["na"] == d["nb"])
    emit("| positions where both arms reported the SAME node count | %d of %d |" % (same_nodes, len(rows)))
    emit("")
    emit("**How to read this:** a median ratio near 1.0 means the v3 path costs about the same as the built-in")
    emit("evaluation per unit of work on real positions — the bench's 21.46 %% v3 share does not translate into a")
    emit("real-position penalty or benefit of that size. The per-position spread is the number that matters for any")
    emit("patch claim: a patch smaller than that spread is not measurable on this sample.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
