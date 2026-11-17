#!/usr/bin/env python3
"""first_mate_depth.py EXE -- WHAT is the truncation tied to?

S-W10 refuted my "node limit" claim: `go depth 11` reproduces exactly what `go nodes 50000` gave. That leaves the
question the refutation raises: is the defect tied to depth 11 specifically, or to THE DEPTH AT WHICH A POSITION'S
MATE IS FIRST REPORTED?

Method: for each mate position, run `go depth d` for d = 6..20 in one fresh process per depth, record the first depth
that reports a mate, and whether THAT line's PV is complete. If truncation happens exactly at the first-mate depth and
not before (there is nothing to truncate before) and clears afterwards, the defect is "the first mate score comes
before the PV can be carried" — a per-position depth, not a fixed 11.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"

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

POSITIONS = [
    ("S-F58 violator", "r2r4/pB2kpp1/n1p4p/1p5p/2n5/1q1bP2P/2PBN3/4K2R b - - 1 40"),
    ("G/192", "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"),
    ("G/59", "4Q3/8/r2K4/8/2B5/5R2/1k6/8 w - - 0 1"),
    ("G/306", "8/7k/7P/8/5pK1/4q3/8/8 b - - 0 1"),
]


def run(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def u(t, lim=200):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "":
                return False
            l = l.rstrip(); L.append(l)
            if any(b in l for b in BAD):
                return False
            if l.startswith(t):
                return True
        return False

    s("uci")
    if not u("uciok"):
        p.kill(); return None
    for o in OPTS:
        s(o); s("isready")
        if not u("readyok"):
            p.kill(); return None
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready"); u("readyok")
    s(f"go depth {depth}")
    ok = u("bestmove")
    s("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    if not m:
        return None
    moves = last.split(" pv ", 1)[1].split() if " pv " in last else []
    return dict(kind=m.group(1), val=int(m.group(2)), plies=len(moves))


print(f"exe: {EXE}   PC20, Threads 1, Hash 16, OwnBook false   fresh process per (position, depth)")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()

for label, fen in POSITIONS:
    print(f"### {label}")
    print()
    print("| depth | score | pv plies | needed | complete? |")
    print("|---|---|---|---|---|")
    first_mate_depth = None
    for d in range(6, 21):
        r = run(fen, d)
        if r is None:
            continue
        if r["kind"] == "mate" and r["val"] != 0:
            need = 2 * abs(r["val"]) - 1 if r["val"] > 0 else 2 * abs(r["val"])
            comp = "yes" if r["plies"] == need else f"**NO** ({r['plies']}/{need})"
            if first_mate_depth is None:
                first_mate_depth = d
                mark = " <- FIRST MATE"
            else:
                mark = ""
            print(f"| {d} | mate {r['val']:+d} | {r['plies']} | {need} | {comp}{mark} |")
    print()
    print(f"first depth reporting a mate: **{first_mate_depth}**")
    print()
