#!/usr/bin/env python3
"""gap_at_big_depth.py : measure the margin at the depth the LARGER budget reached.

Motivation (23-F28): the identity test failed, most likely because I measured at the 20000 budget's final depth
while the flip happens at 250000's. This job fixes exactly that: for every position, D_big = the depth the 250000
budget actually reached, and the two moves (the 20000 choice and the 250000 choice) are scored alone AT D_big.

Sub-population of greatest interest: the 11 positions of 23-F24 where ONLY 250000 differs (20000 == 50000).
If the gap at D_big is what decides the flip, those 11 should be the SMALLEST gaps.

PC r15, PC20, Threads 1, Hash 16, fresh process per search, drained to bestmove (19-F12).
"""
import json
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else "../job7/pc20_opts.txt"
DATA = sys.argv[3] if len(sys.argv) > 3 else "../job10/out_60.json"
OUT = sys.argv[4] if len(sys.argv) > 4 else "gap_at_big_depth.out"

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")


def score_of(fen, move, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in uci")
        s = l.strip()
        if s.startswith("option name "):
            names.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    for line in [x.strip() for x in open(OPTFILE) if x.strip() and not x.startswith("#")]:
        nm = line.split("name ")[1].split(" value ")[0]
        if nm not in names:
            raise RuntimeError("STOP: %r not in uci list" % nm)
        p.stdin.write(line + "\n"); p.stdin.flush()
        p.stdin.write("isready\n"); p.stdin.flush()
        while p.stdout.readline().strip() != "readyok":
            pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s\n" % fen); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d searchmoves %s\n" % (depth, move)); p.stdin.flush()
    last = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)))
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return last


def centi(sc):
    if sc is None:
        return None
    kind, val = sc
    if kind == "mate":
        return 100000 - 100 * abs(val) if val > 0 else -100000 + 100 * abs(val)
    return val


d = json.load(open(DATA))
per = {}
for r in d["records"]:
    per.setdefault(r["fen"], {})[r["n"]] = r

rows = []
for fen, m in per.items():
    a = m[20000]["bestmove"]
    b = m[50000]["bestmove"]
    c = m[250000]["bestmove"]
    if a == b == c:
        continue
    kind = ("only250" if (a == b and b != c) else
            "only20000" if (b == c and a != b) else "allthree")
    D_big = m[250000]["depths"][-1][0]
    sa = centi(score_of(fen, a, D_big))
    sc = centi(score_of(fen, c, D_big))
    if sa is None or sc is None:
        continue
    rows.append({"fen": fen, "kind": kind, "D_big": D_big, "a": a, "c": c,
                 "sa": sa, "sc": sc, "gap": abs(sa - sc),
                 "better": a if sa > sc else c})

print("gap between the two candidate moves, both scored ALONE at the depth the 250000 budget reached")
print("PC r15, PC20, Threads 1, Hash 16")
print()
print("| shape | n | gap min | gap median | gap max | 250000's move scores higher |")
print("|---|---|---|---|---|---|")
for kind, label in (("only250", "only 250000 differs"),
                    ("only20000", "only 20000 differs"),
                    ("allthree", "all three differ")):
    g = [r for r in rows if r["kind"] == kind]
    if not g:
        print("| %s | 0 | - | - | - | - |" % label)
        continue
    gaps = sorted(r["gap"] for r in g)
    bet = sum(1 for r in g if r["better"] == r["c"])
    print("| %s | %d | %d | %d | %d | %d of %d |" %
          (label, len(g), gaps[0], gaps[len(gaps) // 2], gaps[-1], bet, len(g)))

allg = sorted(r["gap"] for r in rows)
print()
print("all changed positions: n=%d, gap min %d, median %d, max %d"
      % (len(allg), allg[0], allg[len(allg) // 2], allg[-1]))

with open(OUT, "w") as f:
    f.write("fen shape D_big a sa c sc gap better\n")
    for r in sorted(rows, key=lambda r: r["gap"]):
        f.write("%s %s %d %s %d %s %d %d %s\n" % (r["fen"], r["kind"], r["D_big"], r["a"],
                                                  r["sa"], r["c"], r["sc"], r["gap"], r["better"]))
print()
print("per-position rows -> %s" % OUT)
