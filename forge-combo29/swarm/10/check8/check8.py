#!/usr/bin/env python3
"""check8.py OUTDIR -- two checks in one job, my own harness, Threads 1 throughout.

A) seat 20's S-F16: two mechanisms both print cp 0.
   root shortcut  : halfmove 100 -> 0 nodes, EMPTY pv
   horizon        : halfmove ~90..99 -> many nodes, FULL pv
B) seat 02's S-F7c: the MultiPV x Hash grid under a 5 s clock on PC r15.

Every search: fresh process, read to `bestmove` (EOF-safe), Threads 1 explicit, one `go` each.

Usage: check8.py OUTDIR
"""
import json
import os
import re
import subprocess
import sys
import time

BASE = os.path.expanduser("~/builds/release/forge")
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

# a genuinely WON K+R vs K board; the halfmove field is substituted
KR = "1K6/8/8/3R4/8/8/8/k7 w - - %d 1"


def search(exe, regime, poscmd, go, extra=()):
    lines = ["uci", "isready", "setoption name Threads value 1"]
    if not any(k == "Hash" for k, _ in extra):
        lines.append("setoption name Hash value 16")
    lines += ["setoption name %s value %s" % kv for kv in (S14 if regime == "s14" else PC20)]
    lines += ["setoption name %s value %s" % kv for kv in extra]
    lines += ["isready", "ucinewgame", "isready", poscmd, "isready", go]
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    infos = [l for l in out if l.startswith("info depth")]
    last = infos[-1] if infos else ""
    nodes = None
    m = re.search(r" nodes (\d+)", last)
    if m:
        nodes = int(m.group(1))
    depth = None
    m = re.search(r"^info depth (\d+)", last)
    if m:
        depth = int(m.group(1))
    pv = []
    if " pv " in last:
        pv = last.split(" pv ", 1)[1].split()
    score = None
    m = re.search(r" score (cp|mate) (-?\d+)", last)
    if m:
        score = (m.group(1), int(m.group(2)))
    best = None
    for l in out:
        if l.startswith("bestmove"):
            best = l.split()[1]
    return {"go": go, "info_lines": len(infos), "last_depth": depth, "last_nodes": nodes,
            "pv_len": len(pv), "pv": pv, "score": score, "bestmove": best,
            "all_nodes_zero": (all(re.search(r" nodes 0 ", " " + x) for x in infos) if infos else None)}


out = {"A_two_cp0_mechanisms": {}, "B_multipv_hash_grid": {}}

# ---------------- A: the two cp 0 mechanisms
for bname, exe, regime in (("base_s14", BASE, "s14"), ("pc20", PC, "pc20")):
    rows = []
    for hm in (0, 85, 90, 91, 95, 98, 99, 100, 101):
        r = search(exe, regime, "position fen " + (KR % hm), "go depth 10")
        r["halfmove"] = hm
        rows.append(r)
        print("A %-9s hm=%-3d depth %-3s nodes %-9s pv %-3d score %s"
              % (bname, hm, r["last_depth"], r["last_nodes"], r["pv_len"], r["score"]), flush=True)
    out["A_two_cp0_mechanisms"][bname] = rows
with open(os.path.join(OUT, "check8.json"), "w") as f:
    json.dump(out, f, indent=1)
    f.write("\n")

# ---------------- B: MultiPV x Hash grid, PC r15, 5 s clock
grid = {}
for h in (16, 64, 256, 2048):
    for mpv in (1, 2, 5, 8):
        depths = []
        for rep in range(2):
            r = search(PC, "pc20", "position startpos",
                       "go wtime 5000 btime 5000",
                       extra=[("Hash", str(h)), ("MultiPV", str(mpv))])
            depths.append(r["last_depth"])
        grid["H%d_M%d" % (h, mpv)] = depths
        print("B H=%-5d P=%-2d depths %s" % (h, mpv, depths), flush=True)
        with open(os.path.join(OUT, "check8.json"), "w") as f:
            json.dump(out, f, indent=1)
            f.write("\n")
out["B_multipv_hash_grid"] = grid
with open(os.path.join(OUT, "check8.json"), "w") as f:
    json.dump(out, f, indent=1)
    f.write("\n")

# summary
a = out["A_two_cp0_mechanisms"]
s = {}
for bname, rows in a.items():
    zero = [r for r in rows if r["score"] == ("cp", 0)]
    s[bname] = {"rows_with_cp0": len(zero),
                "cp0_with_zero_nodes": sum(1 for r in zero if r["last_nodes"] == 0),
                "cp0_with_empty_pv": sum(1 for r in zero if r["pv_len"] == 0),
                "cp0_with_nodes_gt_0": sum(1 for r in zero if (r["last_nodes"] or 0) > 0),
                "detail": [(r["halfmove"], r["last_nodes"], r["pv_len"], r["score"]) for r in rows]}
out["A_summary"] = s
out["B_summary"] = {"H16_M8": grid.get("H16_M8"), "H2048_M8": grid.get("H2048_M8"),
                    "monotone_in_hash_at_M8": [grid.get("H%d_M8" % h) for h in (16, 64, 256, 2048)]}
with open(os.path.join(OUT, "check8.json"), "w") as f:
    json.dump(out, f, indent=1)
    f.write("\n")
print(json.dumps({"A_summary": s, "B_summary": out["B_summary"]}, indent=2))
