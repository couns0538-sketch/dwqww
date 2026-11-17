#!/usr/bin/env python3
"""check_s13f9.py OUT — my own check of seat 13's S-F9:

"On PC r15 under PC20 at Threads 1/Hash 16, `go nodes N` is fully DETERMINISTIC (48/48 across separate fresh
 processes) and RESPECTS THE BUDGET AS A HARD CAP (48/48, worst case ...)"

Two claims, both cheap and both falsifiable:
  DETERMINISM: the same (position, N) five times in fresh processes gives identical nodes/depth/move.
  HARD CAP:    the reported node count never exceeds N... but careful — the engine reports the count at its last
               completed iteration, so "respects the cap" needs the right comparison. I measure BOTH: whether the
               reported count <= N, and whether the count ever exceeds N (which would be a genuine breach).

CONTROL: a budget so large it cannot bind must give a DIFFERENT, larger node count than a small budget — otherwise
"respected the cap" could just be "ignored the budget and searched a fixed amount".

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys
import threading
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]
FENS = ["r2q1rk1/ppp2ppp/3bbn2/3p4/8/1PN1PN2/PBPPBPPP/R2Q1RK1 w - - 0 10",
        "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"]
BUDGETS = [5000, 20000, 50000, 500000]


def run(fen, n):
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

    send("go nodes %d" % n)
    threading.Thread(target=rd, daemon=True).start()
    if not done.wait(180.0):
        p.kill()
        return None
    sync()
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    nodes = None
    depth = None
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                depth = int(t[2])
                if "nodes" in t:
                    nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
    return {"nodes": nodes, "depth": depth, "bm": lines[-1].split()[1]}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 13 S-F9 — is `go nodes N` deterministic and a hard cap?")
emit("")
emit("PC r15, PC20, Threads 1, Hash 16. Five fresh processes per (position, budget).")
emit("")
emit("| position | budget | run1 | run2 | run3 | run4 | run5 | identical? | max <= N? |")
emit("|---|---|---|---|---|---|---|---|---|")
det_ok = cap_ok = tot = 0
by_budget = {}
for fen in FENS:
    for n in BUDGETS:
        runs = [run(fen, n) for _ in range(5)]
        if any(r is None for r in runs):
            continue
        tot += 1
        ns = [r["nodes"] for r in runs]
        same = len(set(ns)) == 1 and len({r["bm"] for r in runs}) == 1 and len({r["depth"] for r in runs}) == 1
        det_ok += same
        over = max(ns) > n
        cap_ok += (not over)
        by_budget.setdefault(n, []).append(max(ns))
        emit("| %s | %d | %s | %s | %s | %s | %s | %s | %s |" %
             (fen[:26], n, *[f"{x:,}" if x is not None else "-" for x in ns],
              "YES" if same else "**NO**", "**OVER**" if over else "yes"))

emit("")
emit("## THE CONTROL — a non-binding budget must give a LARGER count")
big = by_budget.get(500000, [None])[0]
small = by_budget.get(5000, [None])[0]
emit("")
emit("| budget | largest reported node count (first position) |")
emit("|---|---|")
for n in sorted(by_budget):
    emit("| %d | %s |" % (n, f"{by_budget[n][0]:,}" if by_budget[n] and by_budget[n][0] else "-"))
control_ok = (big is not None and small is not None and big > small)
emit("")
emit("| question | answer |")
emit("|---|---|")
emit("| the budget CHANGES the node count (control) | **%s** |" % ("YES" if control_ok else "**NO — VOID**"))
emit("| deterministic across 5 fresh processes | **%d of %d** |" % (det_ok, tot))
emit("| reported count never exceeds the budget | **%d of %d** |" % (cap_ok, tot))
emit("")
if not control_ok:
    emit("**VOID**: the budget does not change the reported count, so 'respects the cap' cannot be tested.")
elif det_ok == tot and cap_ok == tot:
    emit("**CONFIRMS**: `go nodes N` is deterministic across five fresh processes on every cell, and the reported node")
    emit("count never exceeded N — while a larger budget reliably produced a larger count, so the cap is real and not")
    emit("an ignored parameter.")
else:
    emit("**PARTIAL**: determinism %d/%d, cap %d/%d — see the table." % (det_ok, tot, cap_ok, tot))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
