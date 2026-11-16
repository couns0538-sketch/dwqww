#!/usr/bin/env python3
"""deep155.py OUTFILE : the full treatment of position 155.

Records, for depths 16, 18 and 20, on four builds:
  base           -- the base tree
  r15_pc         -- the PC build under PC20 (the binary the owner plays)
  B_lmr1_ot0     -- base + ported rules, shipped switch combination
  B_lmr0_ot0     -- base + ported rules, both off (i.e. behaviourally the base tree)
For each: the full `info depth D` line (score, nodes, pv) and the bestmove.

The point is to see WHERE in the PV the two answers diverge and whether the PC's line is lost (a negative mate
score) while the base's is not. Threads 1, Hash 16, OwnBook false; PC20 sent to the PC build only (it is the build
that has those options).
"""
import os
import re
import subprocess
import sys

OUT = sys.argv[1]
FEN = "1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"
rawdir = OUT + ".raw"
os.makedirs(rawdir, exist_ok=True)

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"),
        ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]

BUILDS = [
    ("base", "/home/ubuntu/build-rel/forge", False),
    ("r15_pc_PC20", "/home/ubuntu/build-pc/forge", True),
    ("B_lmr1_ot0", "/home/ubuntu/build-B_lmr1_ot0/forge", False),
    ("B_lmr0_ot0", "/home/ubuntu/build-B_lmr0_ot0/forge", False),
]


def run(exe, depth, pc20, tag):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(os.path.join(rawdir, tag + ".txt"), "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        lines = []
        while True:
            line = p.stdout.readline()
            if line == "":
                raise RuntimeError(f"died waiting {tok} ({tag})")
            raw.write(line)
            raw.flush()
            s = line.strip()
            lines.append(s)
            if s.startswith(tok):
                return lines

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    opts = [("Threads", "1"), ("Hash", "16")] + (PC20 if pc20 else [("OwnBook", "false")])
    for o, v in opts:
        send(f"setoption name {o} value {v}")
        send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {FEN}")
    send("isready"); until("readyok")
    send(f"go depth {depth}")
    lines = until("bestmove")
    send("quit")
    try:
        p.wait(timeout=600)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    bm = [s for s in lines if s.startswith("bestmove")][-1].split()[1]
    last = None
    for s in lines:
        m = re.match(rf"info depth {depth} .*?(score (?:cp|mate) -?\d+).*?(nodes \d+).*? pv (.+)$", s)
        if m:
            last = m
    if last is None:
        return bm, None, None, None
    return bm, last.group(1), int(last.group(2).split()[1]), last.group(3)


out = [f"position: {FEN}   (white to move; base plays c6d6, PC plays c6c7)", ""]
for depth in (16, 18, 20):
    out.append(f"=== depth {depth}")
    for name, exe, use_pc20 in BUILDS:
        bm, score, nodes, pv = run(exe, depth, use_pc20, f"d{depth}_{name}")
        out.append(f"{name:12s} bestmove {bm:6s} score {score} nodes {nodes}")
        out.append(f"             pv {pv}")
    out.append("")

open(OUT, "w").write("\n".join(out) + "\n")
print("\n".join(out))
