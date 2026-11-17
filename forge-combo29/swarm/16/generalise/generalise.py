#!/usr/bin/env python3
"""generalise.py BASEEXE CANONEXE OUTDIR : does S-F35's full canonicalisation generalise?

60 G positions, depths 1 and 2, both builds, colour-mirror pairs. PC20 options, Threads 1, Hash 16, cold per
search. Reports per build and depth how many pairs have equal node counts, and the per-position verdicts so a
residue can be inspected.
"""
import os
import re
import subprocess
import sys
import time

import chess

BASE, CANON, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUTDIR, exist_ok=True)
NPOS = 60
DEPTHS = [1, 2]

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


def nodes(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=240):
        out = []
        dl = time.monotonic() + lim
        while time.monotonic() < dl:
            l = p.stdout.readline()
            if not l:
                return out, False
            l = l.rstrip("\n")
            out.append(l)
            if l.strip().startswith(tok):
                return out, True
        return out, False

    send("uci"); uci, ok = to("uciok", 20)
    if not ok:
        raise Missing("no uciok")
    known = {m.group(1) for l in uci for m in [re.match(r"option name (.*) type ", l)] if m}
    send("isready"); to("readyok", 20)
    for n, v in PC20.items():
        if n not in known:
            raise Missing(f"option {n} absent")
        send(f"setoption name {n} value {v}")
        send("isready"); to("readyok", 20)
    send("ucinewgame"); send("isready"); to("readyok", 20)
    send("position fen " + fen); send("isready"); to("readyok", 20)
    send(f"go depth {depth}")
    lines, ok = to("bestmove", 240)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove")
    n = None
    for l in lines:
        m = re.search(rf"^info depth {depth} .*nodes (\d+)", l)
        if m:
            n = int(m.group(1))
    if n is None:
        raise Missing(f"no nodes at depth {depth}")
    return n


fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/generalise/set_G.epd")
        if l.strip()][:NPOS]
rows = []
out = [f"base {BASE}", f"canon {CANON}", f"positions {len(fens)}", "",
       "idx\tdepth\tbase_A\tbase_m\tbase_eq\tcanon_A\tcanon_m\tcanon_eq"]
print(out[1])
for i, fen in enumerate(fens):
    mir = chess.Board(fen).mirror().fen()          # computed, never typed
    for d in DEPTHS:
        try:
            ba, bm = nodes(BASE, fen, d), nodes(BASE, mir, d)
            ca, cm = nodes(CANON, fen, d), nodes(CANON, mir, d)
        except Missing as exc:
            out.append(f"{i}\t{d}\tERROR\t{exc}")
            continue
        rows.append({"i": i, "d": d, "ba": ba, "bm": bm, "ca": ca, "cm": cm})
        out.append(f"{i}\t{d}\t{ba}\t{bm}\t{ba==bm}\t{ca}\t{cm}\t{ca==cm}")
    if (i + 1) % 10 == 0:
        print(f"  {i+1}/{len(fens)}", flush=True)

summary = []
for d in DEPTHS:
    sr = [r for r in rows if r["d"] == d]
    beq = sum(1 for r in sr if r["ba"] == r["bm"])
    ceq = sum(1 for r in sr if r["ca"] == r["cm"])
    summary.append(f"depth {d}: base equal {beq}/{len(sr)}   canonical equal {ceq}/{len(sr)}")
beq = sum(1 for r in rows if r["ba"] == r["bm"])
ceq = sum(1 for r in rows if r["ca"] == r["cm"])
summary.append(f"ALL    : base equal {beq}/{len(rows)}   canonical equal {ceq}/{len(rows)}")
worse = [r for r in rows if r["ba"] == r["bm"] and r["ca"] != r["cm"]]
summary.append(f"cases the fix BROKE (equal before, unequal after): {len(worse)}")
for r in worse[:5]:
    summary.append(f"  broke idx {r['i']} depth {r['d']}: base {r['ba']}/{r['bm']} canon {r['ca']}/{r['cm']}")
resid = [r for r in rows if r["ca"] != r["cm"]]
summary.append(f"canonical RESIDUE cases: {len(resid)}")
for r in resid[:10]:
    summary.append(f"  residue idx {r['i']} depth {r['d']}: canon {r['ca']}/{r['cm']} "
                   f"(base {r['ba']}/{r['bm']})")
text = "\n".join(out) + "\n\n" + "\n".join(summary) + "\n"
with open(os.path.join(OUTDIR, "generalise.txt"), "w") as fh:
    fh.write(text)
print("\n".join(summary))
