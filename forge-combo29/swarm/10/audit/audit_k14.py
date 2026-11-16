#!/usr/bin/env python3
"""audit_k14.py -- K14: "a root restricted by searchmoves (even to every legal move) searches a
different, mostly smaller tree: IIR fires at the root, and no hash entry is stored for a restricted
root".

Design (my own):
  A unrestricted depth 10, fresh process                 -> nodes_A
  B restricted to ALL 20 legal moves, depth 10, fresh     -> nodes_B
  C unrestricted twice in ONE process, depth 10           -> nodes_C1, nodes_C2
  D restricted twice in ONE process, depth 10             -> nodes_D1, nodes_D2
The "no hash entry stored for a restricted root" half is tested by comparing the SECOND search's node
count with the FIRST: a stored root entry should shrink the repeat. It shrinks for C and, if the claim
holds, does not shrink for D.

Usage: audit_k14.py EXE OUTDIR
"""
import json
import os
import re
import subprocess
import sys

EXE = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
os.makedirs(OUT, exist_ok=True)

DEPTH = 10
ALLMOVES = "a2a3 a2a4 b1a3 b1c3 b2b3 b2b4 c2c3 c2c4 d2d3 d2d4 e2e3 e2e4 f2f3 f2f4 g1f3 g1h3 g2g3 g2g4 h2h3 h2h4"


def go_lines(count, restrict):
    out = []
    for _ in range(count):
        cmd = "go depth %d" % DEPTH
        if restrict:
            cmd += " searchmoves " + ALLMOVES
        out.append(cmd)
    return out


def run(tag, gos):
    lines = ["uci", "isready", "position startpos", "isready"] + gos
    p = subprocess.run([EXE], input="\n".join(lines) + "\nquit\n",
                       capture_output=True, text=True, timeout=1800)
    with open(os.path.join(OUT, tag + ".txt"), "w") as f:
        f.write("=== exe %s\n" % EXE)
        for l in lines:
            f.write("  " + l + "\n")
        f.write(p.stdout)
        f.write("=== stderr\n" + p.stderr)
    nodes, bests = [], []
    cur = None
    for l in p.stdout.splitlines():
        if l.startswith("info") and " nodes " in l:
            m = re.search(r" nodes (\d+)", l)
            if m:
                cur = int(m.group(1))
        if l.startswith("bestmove"):
            nodes.append(cur)
            bests.append(l.strip().split()[1])
            cur = None
    return nodes, bests


A, bestA = run("A_unrestricted_once", go_lines(1, False))
B, bestB = run("B_allmoves_once", go_lines(1, True))
C, bestC = run("C_unrestricted_twice", go_lines(2, False))
D, bestD = run("D_allmoves_twice", go_lines(2, True))

summary = {
    "depth": DEPTH,
    "searchmoves_lists_all": len(ALLMOVES.split()) == 20,
    "A_unrestricted_nodes": A, "A_bestmove": bestA,
    "B_allmoves_nodes": B, "B_bestmove": bestB,
    "C_unrestricted_twice_nodes": C, "C_bestmoves": bestC,
    "D_allmoves_twice_nodes": D, "D_bestmoves": bestD,
    "B_smaller_than_A": (B and A and B[0] < A[0]) if (A and B) else None,
    "B_equal_to_A": (A == B),
    "bestmove_same_A_B": bestA == bestB,
    "unrestricted_repeat_shrinks": (len(C) == 2 and C[1] < C[0]),
    "restricted_repeat_shrinks": (len(D) == 2 and D[1] < D[0]),
    "verdict": None,
}
summary["verdict"] = (
    "PASS" if (summary["B_smaller_than_A"] is True and
               summary["unrestricted_repeat_shrinks"] is True and
               summary["restricted_repeat_shrinks"] is False) else "PARTLY/REFUTED"
)
with open(os.path.join(OUT, "K14.json"), "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")
print(json.dumps(summary, indent=2))
