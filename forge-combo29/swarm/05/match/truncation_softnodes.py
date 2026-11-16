#!/usr/bin/env python3
"""truncation_softnodes.py EXE -- the mate-PV truncation (S-F1/S-F9/S-F27) under the PC's ACTUAL self-play budget.

S-F27 showed the truncation happens when the reported mate distance needs more plies than the search carries. The
PC's self-play uses `go softnodes 2000`, which reaches only about depth 7. So the question that matters for the
owner: at the self-play budget, does a mate score ever come with a PV too short to be that mate?

Method: take the positions my runs found to carry a mate score, search each with `go softnodes 2000` (PC20, Threads 1,
Hash 16, OwnBook false), and apply the 2N-1 rule to whatever mate score comes back.
"""
import json
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
N = 2000

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


def run(fen, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=120):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "":
                return False
            l = l.rstrip()
            L.append(l)
            if l.startswith(t):
                return True
        return False

    s("uci"); u("uciok")
    for o in OPTS:
        s(o); s("isready"); u("readyok")
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready"); u("readyok")
    s(go); ok = u("bestmove"); s("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    d = re.search(r"depth (\d+)", last)
    n = re.search(r"\bnodes (\d+)", last)
    plies = len(last.split(" pv ", 1)[1].split()) if " pv " in last else 0
    return dict(kind=m.group(1) if m else None, val=int(m.group(2)) if m else None,
                depth=int(d.group(1)) if d else None, nodes=int(n.group(1)) if n else None,
                plies=plies)


fens = []
for path in ("../job1/out/rows.jsonl", "../job1b/outR/rows.jsonl"):
    for line in open(path):
        r = json.loads(line)
        lp = r.get("last_pv")
        if lp and lp.get("score", ("", 0))[0] == "mate" and lp["score"][1] != 0:
            fens.append(r["fen"])

print(f"exe: {EXE}   go softnodes {N} (the PC self-play budget)   PC20, Threads 1, Hash 16, OwnBook false")
print(f"positions: {len(fens)} (the ones my depth-12 runs found to carry a mate score)")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| # | softnodes 2000: score | depth | nodes | pv plies | 2N-1 rule |")
print("|---|---|---|---|---|---|")
mates = trunc = 0
for i, fen in enumerate(fens):
    r = run(fen, f"go softnodes {N}")
    if r is None:
        print(f"| {i} | NO PV | - | - | - | - |")
        continue
    if r["kind"] == "mate" and r["val"]:
        mates += 1
        need = 2 * abs(r["val"]) - 1 if r["val"] > 0 else 2 * abs(r["val"])
        ok = r["plies"] == need
        if not ok:
            trunc += 1
        print(f"| {i} | mate {r['val']:+d} | {r['depth']} | {r['nodes']} | {r['plies']} | "
              f"{'ok' if ok else f'**SHORT {need - r[plies] if False else need - r['plies']}**'} |")
    else:
        print(f"| {i} | {r['kind']} {r['val']:+d} | {r['depth']} | {r['nodes']} | {r['plies']} | not a mate score |")
print()
print(f"mate scores at softnodes {N}: {mates}   truncated: {trunc}"
      f" = {100.0*trunc/mates if mates else 0:.1f}%")
