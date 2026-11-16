#!/usr/bin/env python3
"""softnodes.py OUTDIR -- `go softnodes N` on the PC build under PC20, Threads 1, Hash 16.

This is the owner's SELF-PLAY command. File 6 says its intent is "the search stops at the end of the first
depth after 2,000 nodes".

Measured for N in {2000, 20000, 50000, 250000} on four positions:
  determinism : 5 fresh processes per (position, N) -> are bestmove, score and node count identical?
  completion  : is the last reported depth FINISHED (its node count exceeds the previous depth's, pv non-empty)?
  overshoot   : reported nodes / N, and how much of the last depth's work happened after the budget
  comparison  : the same with `go nodes N` (which should stop MID-depth) to show the structural difference
  monotonicity: depth and nodes never DECREASE as N grows

Every search: fresh process, read to `bestmove` (EOF-safe), Threads 1 explicit, Hash 16.

Usage: softnodes.py OUTDIR
"""
import json
import os
import re
import subprocess
import sys

PC = os.path.expanduser("~/builds/pc/forge")
OUT = os.path.abspath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

POSITIONS = {
    "startpos": "position startpos",
    "G_black_mid": "position fen r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
    "G_knight_out": "position fen 1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "tactical": "position fen r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1",
}
NS = [2000, 20000, 50000, 250000]


def one(poscmd, go):
    lines = ["uci", "isready", "setoption name Threads value 1", "setoption name Hash value 16"]
    lines += ["setoption name %s value %s" % kv for kv in PC20]
    lines += ["isready", "ucinewgame", "isready", poscmd, "isready", go]
    p = subprocess.Popen([PC], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for l in lines:
        p.stdin.write(l + "\n")
        p.stdin.flush()
    out = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        out.append(line.rstrip())
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n")
    try:
        p.stdin.flush()
    except Exception:
        pass
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()
    per_depth = []
    for l in out:
        m = re.match(r"info depth (\d+) .*? nodes (\d+)", l)
        if m:
            per_depth.append((int(m.group(1)), int(m.group(2))))
    last = [l for l in out if l.startswith("info depth")]
    last = last[-1] if last else ""
    depth = nodes = score = None
    if last.startswith("info depth"):
        try:
            depth = int(last.split("depth ")[1].split()[0])
        except (IndexError, ValueError):
            pass
        if " nodes " in last:
            try:
                nodes = int(last.split(" nodes ")[1].split()[0])
            except (IndexError, ValueError):
                pass
        m = re.search(r" score (cp|mate) (-?\d+)", last)
        if m:
            score = (m.group(1), int(m.group(2)))
    pv = last.split(" pv ", 1)[1].split() if " pv " in last else []
    best = None
    for l in out:
        if l.startswith("bestmove"):
            best = l.split()[1]
    prev_nodes = None
    if len(per_depth) >= 2:
        prev_nodes = per_depth[-2][1]
    return {"go": go, "depth": depth, "nodes": nodes, "score": score,
            "pv_len": len(pv), "bestmove": best,
            "depths_seen": [d for d, _ in per_depth],
            "prev_depth_nodes": prev_nodes,
            # a FINISHED last depth is one whose node count exceeds the previous depth's
            "last_depth_finished": (prev_nodes is not None and nodes is not None and nodes > prev_nodes),
            "info_depth_lines": len(per_depth)}


res = {"softnodes": {}, "nodes": {}}
for pname, poscmd in POSITIONS.items():
    res["softnodes"][pname] = {}
    for n in NS:
        runs = [one(poscmd, "go softnodes %d" % n) for _ in range(5)]
        same = len({(r["bestmove"], str(r["score"]), r["nodes"], r["depth"]) for r in runs}) == 1
        rec = {"runs": runs, "deterministic": same,
               "overshoot_ratio": (round(runs[0]["nodes"] / n, 2)
                                   if runs[0]["nodes"] else None)}
        res["softnodes"][pname]["N%d" % n] = rec
        print("%-14s softnodes %-7d depth %-3s nodes %-8s ratio %-5s det %s finished %s"
              % (pname, n, runs[0]["depth"], runs[0]["nodes"],
                 rec["overshoot_ratio"], same, runs[0]["last_depth_finished"]), flush=True)
        with open(os.path.join(OUT, "softnodes.json"), "w") as f:
            json.dump(res, f, indent=1)
            f.write("\n")

# the `nodes` comparison on one position, to show the structural difference
for n in (2000, 20000):
    r = one("position startpos", "go nodes %d" % n)
    res["nodes"]["startpos_N%d" % n] = r
    print("startpos  nodes     %-7d depth %-3s nodes %-8s finished %s"
          % (n, r["depth"], r["nodes"], r["last_depth_finished"]), flush=True)

# monotonicity across N at each position
mono = {}
for pname in POSITIONS:
    depths = [res["softnodes"][pname]["N%d" % n]["runs"][0]["depth"] or 0 for n in NS]
    nodes = [res["softnodes"][pname]["N%d" % n]["runs"][0]["nodes"] or 0 for n in NS]
    mono[pname] = {"depths": depths, "nodes": nodes,
                   "depth_monotone": all(b >= a for a, b in zip(depths, depths[1:])),
                   "nodes_monotone": all(b >= a for a, b in zip(nodes, nodes[1:]))}
res["monotonicity"] = mono
with open(os.path.join(OUT, "softnodes.json"), "w") as f:
    json.dump(res, f, indent=1)
    f.write("\n")
print(json.dumps(mono, indent=2))
