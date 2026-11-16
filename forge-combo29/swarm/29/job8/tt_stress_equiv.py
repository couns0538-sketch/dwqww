#!/usr/bin/env python3
"""Stress the 29-F12 TT patch on the paths it touches: heavy TT REPLACEMENT (many positions against a SMALL table
so clusters fill and evict), deeper searches, and hash-resize between searches. Compares base vs patch on
score, nodes, and bestmove for each case; any single difference is printed and counted.

Cold by construction: a fresh process per (exe, case) with Hash 1 (the minimum) so the replacement path is
 exercised hard rather than avoided.
"""
import subprocess, sys

BASE, PATCH = sys.argv[1], sys.argv[2]
CASES = [
    ("startpos", 1, 14),
    ("kiwipete", 1, 12),
    ("endgame", 1, 16),
    ("middlegame", 1, 13),
]
FENS = {
    "startpos": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "kiwipete": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "endgame": "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "middlegame": "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
}


def one(exe, name, hashmb, depth):
    cmds = ["uci", f"setoption name Hash value {hashmb}", "setoption name Threads value 1",
            "setoption name OwnBook value false", "isready",
            f"position fen {FENS[name]}", f"go depth {depth}"]
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    for c in cmds[:-1]:
        p.stdin.write(c + "\n"); p.stdin.flush()
        if c == "isready":
            for line in p.stdout:
                if line.startswith("readyok"):
                    break
    p.stdin.write(cmds[-1] + "\n"); p.stdin.flush()
    nodes = score = pv = bm = None
    for line in p.stdout:
        if line.startswith("info depth"):
            f = line.split()
            nodes = int(f[f.index("nodes") + 1])
            score = f[f.index("score") + 1:f.index("score") + 3]
            pv = f[f.index("pv") + 1:] if "pv" in f else []
        if line.startswith("bestmove"):
            bm = line.strip(); break
    p.stdin.write("quit\n"); p.stdin.flush(); p.wait()
    if nodes is None or bm is None:
        raise SystemExit(f"ABORT: {name} produced no complete result -- refusing to compare a missing value")
    return nodes, tuple(score), tuple(pv), bm


same = diff = 0
for name, h, d in CASES:
    b = one(BASE, name, h, d)
    q = one(PATCH, name, h, d)
    ok = b == q
    print(f"{name:11s} Hash {h} depth {d}: nodes {b[0]:>9}  "
          f"{'IDENTICAL' if ok else 'DIFFERENT'}")
    if not ok:
        print(f"   base : {b}")
        print(f"   patch: {q}")
        diff += 1
    else:
        same += 1
print(f"\nidentical: {same}   different: {diff}   (a difference here would falsify 29-F12)")
if diff:
    raise SystemExit(1)
