#!/usr/bin/env python3
"""Practical match question: does the TIME CONTROL change the move the engine plays?

S-F21 showed the search is identical across wide clock ranges (depth quantisation). The step from that to
match design is: if the search is identical, the bestmove should be too — so a match at a generous clock
may be identical play to a fast one.

That is an inference. This measures it directly over a real position set: for each position, play the same
search at several time controls and compare the BESTMOVE. Reports how many positions change their move
between each pair of controls.

This is deliberately a MOVE comparison, not a score comparison: the move is what a match result depends on,
and the swarm's rule is that Threads-1 moves are trustworthy while scores need Threads 1 (which we have).

Settings: canonical PC20 from lib/settings.py (asserted), Threads 1, Hash 16, fresh process per search.
Positions: the G set (real engine-game positions), first N.

Usage: clockmoves.py EXE FENS OUTDIR [MAXPOS]
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
from settings import PC20, describe  # noqa: E402

EXE = sys.argv[1]
FENS = sys.argv[2]
OUTDIR = sys.argv[3]
MAXPOS = int(sys.argv[4]) if len(sys.argv) > 4 else 60
os.makedirs(OUTDIR, exist_ok=True)
BAD = ("unknown option", "invalid value", "error")

# The owner's setting plus a fast and a generous one, to bracket what a match might use.
CLOCKS = [2000, 6000, 20000, 60000]


def run(fen, wtime):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if pred(l):
                return l

    send("uci")
    seen = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            seen.append(l)
        if l == "uciok":
            break
    for n, v in PC20:
        if not any(o.startswith("option name %s " % n) for o in seen):
            raise SystemExit("FAIL: option %r not advertised" % n)
        send("setoption name %s value %s" % (n, v))
        send("isready")
        until(lambda s: s == "readyok")
    send("position fen " + fen)
    send("isready")
    until(lambda s: s == "readyok")
    send("go wtime %d btime %d winc 60 binc 60" % (wtime, wtime))
    last = None
    bm = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died during search")
        l = l.rstrip("\n")
        if l.startswith("info depth"):
            last = l
        if l.startswith("bestmove"):
            bm = l
            break
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    d = re.search(r"\bdepth (\d+)", last) if last else None
    n = re.search(r"\bnodes (\d+)", last) if last else None
    return {"wtime": wtime,
            "bestmove": (bm.split()[1] if bm and len(bm.split()) > 1 else None),
            "depth": int(d.group(1)) if d else None,
            "nodes": int(n.group(1)) if n else None}


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()][:MAXPOS]
    if not fens:
        raise SystemExit("FAIL: no positions in %s" % FENS)
    rows = []
    for i, fen in enumerate(fens):
        got = {}
        for wt in CLOCKS:
            got[wt] = run(fen, wt)
        row = {"position": i, "fen": fen, "by_clock": {str(k): v for k, v in got.items()}}
        # pairwise move agreement
        for a in range(len(CLOCKS)):
            for b in range(a + 1, len(CLOCKS)):
                ka, kb = CLOCKS[a], CLOCKS[b]
                row["same_%d_%d" % (ka, kb)] = (got[ka]["bestmove"] == got[kb]["bestmove"])
        rows.append(row)
        if (i + 1) % 10 == 0:
            print("%d/%d positions" % (i + 1, len(fens)), flush=True)

    pairs = {}
    for a in range(len(CLOCKS)):
        for b in range(a + 1, len(CLOCKS)):
            ka, kb = CLOCKS[a], CLOCKS[b]
            key = "%d_vs_%d" % (ka, kb)
            same = sum(1 for r in rows if r["same_%d_%d" % (ka, kb)])
            pairs[key] = {"same": same, "differ": len(rows) - same,
                          "pct_same": round(100.0 * same / len(rows), 1)}
    summary = {"exe": os.path.abspath(EXE), "settings": describe(PC20),
               "positions": len(rows), "clocks": CLOCKS, "pairs": pairs,
               "note": "move comparison at winc 60; fresh process per search; Threads 1/Hash 16"}
    json.dump({"summary": summary, "rows": rows},
              open(os.path.join(OUTDIR, "clockmoves.json"), "w"), indent=1)
    print()
    print("positions:", len(rows))
    for k, v in pairs.items():
        print("  %-16s identical move on %d of %d (%.1f %%), differ on %d"
              % (k, v["same"], len(rows), v["pct_same"], v["differ"]))
    # show a few differing examples so the result is inspectable
    for r in rows:
        if not r["same_2000_60000"]:
            print("  e.g. position %d differs between 2000 and 60000 ms: %s"
                  % (r["position"], {k: v["bestmove"] for k, v in r["by_clock"].items()}))
            break


main()
