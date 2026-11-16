#!/usr/bin/env python3
"""longmate_match_budget.py EXE -- S-F57 on a sample that can actually show the effect.

S-F57 measured 1/20 truncated at `go nodes 20000` and 0/25, 0/27 at the larger budgets, on 28 mate positions. That
sample is weak: only 3 of those positions had |N| >= 10, the range where the truncation lives. So the 0-at-large-budget
result could be sampling luck.

This builds a mate-rich set SELECTED for long mates first (at a deep search), then tests each of the owner's match
budgets on it. Selection is on |N| at depth 20, never on whether a PV is truncated, so the test is not circular.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
POOL = int(sys.argv[2]) if len(sys.argv) > 2 else 120
MINN = int(sys.argv[3]) if len(sys.argv) > 3 else 8

OPTS = ["setoption name Threads value 1", "setoption name Hash value 16",
        "setoption name OwnBook value false",
        "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
        "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
        "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
        "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
        "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
        "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
        "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
        "setoption name CuckooRep value true", "setoption name HistRework value 2",
        "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
        "setoption name MateAlphaGuard value true"]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def run(fen, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=300):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "":
                return False
            l = l.rstrip()
            L.append(l)
            if any(b in l for b in BAD):
                return False
            if l.startswith(t):
                return True
        return False

    s("uci")
    if not u("uciok"):
        p.kill()
        return None
    for o in OPTS:
        s(o); s("isready")
        if not u("readyok"):
            p.kill()
            return None
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready"); u("readyok")
    s(go)
    ok = u("bestmove")
    s("quit")
    try:
        p.wait(timeout=25)
    except Exception:
        p.kill()
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    plies = len(last.split(" pv ", 1)[1].split()) if " pv " in last else 0
    return (m.group(1) if m else None, int(m.group(2)) if m else None, plies)


BASE = "/agent/repos/dwqww/forge-combo29/swarm/05"
cands = []
for line in open(f"{BASE}/job1/data/G.epd"):
    cands.append(line.split(";")[0].strip())
for line in open(f"{BASE}/job1b/positions/R_seed511.fens"):
    cands.append(line.strip())
cands = [c for c in cands if c][:POOL]

print(f"exe: {EXE}   PC20, Threads 1, Hash 16, OwnBook false   SEQUENTIAL")
print(f"pool {len(cands)} positions; selecting those with |N| >= {MINN} at depth 20")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()

longs = []
for fen in cands:
    r = run(fen, "go depth 20")
    if r and r[0] == "mate" and r[1] and abs(r[1]) >= MINN:
        longs.append((fen, r[1]))
print(f"selected {len(longs)} long-mate positions (|N| >= {MINN} at depth 20)")
print()
if not longs:
    print("NO SUCH POSITIONS IN THE POOL — the test cannot be run on this pool; reported as such, not as a zero.")
    sys.exit(0)

print("Now each match budget on the SELECTED set. A truncated row is `mate N` whose PV is shorter than 2|N|-1.")
print()
print("| budget | long positions with a mate score | truncated | rate | worst case |")
print("|---|---|---|---|---|")
for label, go in [("nodes 20000", "go nodes 20000"),
                  ("nodes 50000", "go nodes 50000"),
                  ("nodes 250000", "go nodes 250000")]:
    mates = trunc = 0
    worst = ""
    worst_gap = -1
    for fen, n20 in longs:
        r = run(fen, go)
        if not r or r[0] != "mate" or not r[1]:
            continue
        mates += 1
        need = 2 * abs(r[1]) - 1 if r[1] > 0 else 2 * abs(r[1])
        if r[2] != need:
            trunc += 1
            gap = need - r[2]
            if gap > worst_gap:
                worst_gap = gap
                worst = f"{fen} mate {r[1]:+d} pv{r[2]}/{need}"
    rate = f"{100.0*trunc/mates:.1f}%" if mates else "no mate scores"
    print(f"| {label} | {mates} | {trunc} | {rate} | {worst if worst else 'none'} |")
print()
print("Because every selected position had |N| >= %d at depth 20, this is the sample where the truncation SHOULD" % MINN)
print("show if it exists at that budget. A zero here is evidence; a zero on the unfiltered 28 was not.")
