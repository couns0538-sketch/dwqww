#!/usr/bin/env python3
"""plycost.py SETFILE SCANFILE OUTFILE [TOPN] : for every scanned position, measure the PLY COST of the engine's
choice, so a low signature rate still says something quantitative.

For each position: play-out BOTH the engine's chosen move and the best alternative (by the scan's own scores) with
python-chess, both sides driven by the engine at a fixed depth, and record how many plies the side survives after
each. cost = plies(survives after best alternative) - plies(survives after chosen); positive means the engine's
choice dies sooner.

Bounded: at most TOPN positions (default 12) — the positions with the LARGEST scan gap first, then the median ones,
so the sample spans the distribution rather than only the worst. Play-outs stop at 120 plies or game over.
"""
import hashlib
import os
import re
import subprocess
import sys

import chess

SETF, SCANF, OUTF = sys.argv[1], sys.argv[2], sys.argv[3]
TOPN = int(os.environ.get("PC_TOPN", "12"))
EXE = os.environ.get("PC_EXE", "/home/ubuntu/build-pc/forge")
DEPTH = int(os.environ.get("PC_DEPTH", "12"))
MAXPLY = 120
rawdir = OUTF + ".raw"
os.makedirs(rawdir, exist_ok=True)

S14 = [("Threads", "1"), ("Hash", "16"), ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"),
       ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"),
       ("NullMoveBase", "5"), ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"),
       ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"),
       ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("OwnBook", "false")]


def bestmove(fen, tag):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(os.path.join(rawdir, tag + ".txt"), "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        while True:
            line = p.stdout.readline()
            if line == "":
                raise RuntimeError(f"died waiting {tok} ({tag})")
            raw.write(line)
            raw.flush()
            s = line.strip()
            if s.startswith(tok):
                return s

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    for o, v in S14:
        send(f"setoption name {o} value {v}")
        send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}")
    send("isready"); until("readyok")
    send(f"go depth {DEPTH}")
    mv = None
    while True:
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError(f"died before bestmove ({tag})")
        raw.write(line)
        raw.flush()
        if line.strip().startswith("bestmove"):
            mv = line.split()[1]
            break
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    return mv


def playout(fen, first, tag):
    b = chess.Board(fen)
    if first not in [m.uci() for m in b.legal_moves]:
        return None
    b.push_uci(first)
    plies = 1
    while plies < MAXPLY and not b.is_game_over(claim_draw=False):
        h = hashlib.sha1(b.fen().encode()).hexdigest()[:12]
        mv = bestmove(b.fen(), f"{tag}_p{plies:03d}_{h}")
        if mv == "0000" or mv not in [m.uci() for m in b.legal_moves]:
            break
        b.push_uci(mv)
        plies += 1
    return plies


rows = [l.rstrip("\n").split("\t") for l in open(SETF) if l.strip()]
scan = {}
for line in open(SCANF):
    m = re.match(r"(\d+)\t([^\t]+)\tchosen=(\S+) (?:cp|mate) (-?\d+)[^\t]*\tbest_alt=(\S+) (?:cp|mate) (-?\d+)[^\t]*\tgap=(-?\d+)", line)
    if m:
        scan[int(m.group(1))] = {"fen": m.group(2), "chosen": m.group(3), "alt": m.group(5),
                                 "gap": int(m.group(7))}
items = sorted(scan.items(), key=lambda kv: -abs(kv[1]["gap"]))
picked = items[:TOPN]
out = [f"ply-cost sample: {len(picked)} positions, chosen vs best alternative, play-out at depth {DEPTH}",
       "cost = plies(survives after the alternative) - plies(survives after the engine's chosen move); positive = the",
       "engine's choice dies sooner", "",
       "| idx | gap (scan) | chosen | alt | plies after chosen | plies after alt | cost |", "|---|---|---|---|---|---|---|"]
costs = []
for idx, d in picked:
    pc = playout(d["fen"], d["chosen"], f"i{idx:03d}_chosen")
    pa = playout(d["fen"], d["alt"], f"i{idx:03d}_alt")
    if pc is None or pa is None:
        out.append(f"| {idx} | {d['gap']} | {d['chosen']} | {d['alt']} | — | — | PLAYOUT FAILED |")
        continue
    cost = pa - pc
    costs.append(cost)
    out.append(f"| {idx} | {d['gap']} | {d['chosen']} | {d['alt']} | {pc} | {pa} | {cost:+d} |")
    print(out[-1], flush=True)
if costs:
    costs.sort()
    out.append("")
    out.append(f"costs: n={len(costs)} min={costs[0]:+d} median={costs[len(costs)//2]:+d} max={costs[-1]:+d} "
               f"mean={sum(costs)/len(costs):+.2f}; positive (chosen dies sooner) {sum(1 for c in costs if c>0)}"
               f", zero {sum(1 for c in costs if c==0)}, negative {sum(1 for c in costs if c<0)}")
open(OUTF, "w").write("\n".join(out) + "\n")
print("\n".join(out[-2:]))
