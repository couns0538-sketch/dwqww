#!/usr/bin/env python3
"""Is the clock-allocation plateau (S-F19) general, or one position's artefact?

S-F19 found that on ONE middlegame position, `go wtime` 10,000 / 12,000 / 15,000 / 20,000 all produced
the identical search (depth 23, 1,520,334 nodes). If that is a property of the allocator, other positions
should show plateaus too (at their own step points). If it was a coincidence of that position, other
positions will scale smoothly with the clock.

Method: for each of several positions spanning material types, sweep wtime over a geometric ladder and
record depth and nodes. A "plateau" is a pair of consecutive clock values giving the IDENTICAL node count.

Settings: canonical PC20 from lib/settings.py (asserted 22 entries), Threads 1, Hash 16.

Usage: plateau.py EXE OUTDIR
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
from settings import PC20, describe  # noqa: E402  (PC20 asserts its own length/membership at import)

EXE = sys.argv[1]
OUTDIR = sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
BAD = ("unknown option", "invalid value", "error")

POSITIONS = [
    ("open middlegame", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("tactical", "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("endgame rook", "8/8/4k3/8/8/4K3/8/R7 w - - 0 1"),
    ("queen endgame", "8/8/4k3/8/8/4K3/8/Q7 w - - 0 1"),
]
CLOCKS = [1000, 2000, 4000, 6000, 8000, 10000, 12000, 15000, 20000, 30000, 60000]


def run(fen, wtime):
    import re
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
    t0 = time.monotonic()
    send("go wtime %d btime %d" % (wtime, wtime))
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
    wall = (time.monotonic() - t0) * 1000.0
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    d = re.search(r"\bdepth (\d+)", last) if last else None
    n = re.search(r"\bnodes (\d+)", last) if last else None
    mt = re.search(r"score mate (-?\d+)", last) if last else None
    return {"wtime": wtime, "wall_ms": round(wall, 1),
            "depth": int(d.group(1)) if d else None,
            "nodes": int(n.group(1)) if n else None,
            "mate": int(mt.group(1)) if mt else None,
            "bestmove": (bm.split()[1] if bm and len(bm.split()) > 1 else None)}


rows = []
for name, fen in POSITIONS:
    for wt in CLOCKS:
        r = run(fen, wt)
        r.update({"position": name, "fen": fen})
        rows.append(r)
        print("%-16s wtime %-6d depth %-3s nodes %-9s wall %6.0f ms %s"
              % (name, wt, r["depth"], r["nodes"], r["wall_ms"],
                 "mate %d" % r["mate"] if r["mate"] is not None else ""), flush=True)
    print()

# plateau detection: consecutive clock values with IDENTICAL node counts
summary = {"exe": os.path.abspath(EXE), "settings": describe(PC20), "clocks": CLOCKS,
           "positions": len(POSITIONS), "runs": len(rows)}
per_pos = {}
for name, fen in POSITIONS:
    sel = sorted([r for r in rows if r["position"] == name], key=lambda r: r["wtime"])
    plateaus = []
    for a, b in zip(sel, sel[1:]):
        if a["nodes"] is not None and a["nodes"] == b["nodes"]:
            plateaus.append({"from_ms": a["wtime"], "to_ms": b["wtime"],
                             "nodes": a["nodes"], "depth": a["depth"]})
    per_pos[name] = {"plateaus": plateaus,
                     "distinct_node_counts": len({r["nodes"] for r in sel if r["nodes"] is not None}),
                     "clock_values": len(sel)}
    print("%-16s %d clock values -> %d DISTINCT node counts, %d plateau interval(s)"
          % (name, len(sel), per_pos[name]["distinct_node_counts"], len(plateaus)))
    for pl in plateaus:
        print("    plateau %6d..%-6d ms -> identical %d nodes at depth %s"
              % (pl["from_ms"], pl["to_ms"], pl["nodes"], pl["depth"]))
summary["per_position"] = per_pos
summary["positions_with_a_plateau"] = sum(1 for v in per_pos.values() if v["plateaus"])
json.dump({"summary": summary, "rows": rows},
          open(os.path.join(OUTDIR, "plateau.json"), "w"), indent=1)
print()
print("positions with at least one plateau:", summary["positions_with_a_plateau"], "of", len(POSITIONS))
