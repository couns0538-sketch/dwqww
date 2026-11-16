#!/usr/bin/env python3
"""top_two_gap.py : the predictor the coordinator asked for.

For EACH of the 60 positions in ../job10/out_60.json:
  1. read the depth the 20000 budget actually reached (from the engine's own last info line at that budget);
  2. at THAT depth, score the two moves that the budgets disagreed about (or, for an unchanged position, the
     bestmove and the strongest alternative) each alone with `go depth D searchmoves <move>`;
  3. record the gap |score1 - score2|.

Then compare the gap DISTRIBUTION for changed versus unchanged positions. If changed positions have systematically
smaller gaps, the margin is a measured predictor rather than a guess.

Protocol: PC r15, PC20, Threads 1, Hash 16, fresh process per search, drained to bestmove (19-F12).
For an unchanged position the "second move" is the highest-scoring alternative found by trying a few legal moves
at the same depth — enough to characterise separation without searching every move.
"""
import json
import random
import re
import subprocess
import sys

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else "../job7/pc20_opts.txt"
DATA = sys.argv[3] if len(sys.argv) > 3 else "../job10/out_60.json"
OUT = sys.argv[4] if len(sys.argv) > 4 else "top_two_gap.out"

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

rng = random.Random(20240117)
rows = []
for fen, m in per.items():
    mv20 = m[20000]["bestmove"]
    mv250 = m[250000]["bestmove"]
    depth = m[20000]["depths"][-1][0]          # the depth the 20000 budget actually reached
    board = chess.Board(fen)
    changed = mv20 != mv250
    if changed:
        cand = [mv20, mv250]
    else:
        # the bestmove plus up to 3 random legal alternatives; keep the two highest scorers
        others = [x.uci() for x in board.legal_moves if x.uci() != mv20]
        rng.shuffle(others)
        cand = [mv20] + others[:3]
    scored = []
    for mv in cand:
        sc = centi(score_of(fen, mv, depth))
        if sc is not None:
            scored.append((sc, mv))
    scored.sort(reverse=True)
    if len(scored) < 2:
        rows.append({"fen": fen, "changed": changed, "depth": depth, "gap": None})
        continue
    gap = scored[0][0] - scored[1][0]
    rows.append({"fen": fen, "changed": changed, "depth": depth, "gap": gap,
                 "top": scored[0][1], "second": scored[1][1]})

meas = [r for r in rows if r["gap"] is not None]
ch = sorted(r["gap"] for r in meas if r["changed"])
un = sorted(r["gap"] for r in meas if not r["changed"])


def stats(xs):
    if not xs:
        return "-"
    return "n=%d min=%d median=%d max=%d" % (len(xs), xs[0], xs[len(xs) // 2], xs[-1])


print("top-two score gap at the depth the 20000 budget actually reached")
print("PC r15, PC20, Threads 1, Hash 16; each move scored alone at that same depth")
print()
print("| group | count | gap statistics (centipawns) |")
print("|---|---|---|")
print("| positions whose move CHANGED between budgets | %d | %s |" % (len(ch), stats(ch)))
print("| positions whose move did NOT change | %d | %s |" % (len(un), stats(un)))
if ch and un:
    print()
    print("median gap, changed = %d cp; median gap, unchanged = %d cp" % (ch[len(ch) // 2], un[len(un) // 2]))
    print("changed positions with gap <= 30 cp: %d of %d" % (sum(1 for g in ch if g <= 30), len(ch)))
    print("unchanged positions with gap <= 30 cp: %d of %d" % (sum(1 for g in un if g <= 30), len(un)))

with open(OUT, "w") as f:
    f.write("fen changed depth gap top second\n")
    for r in sorted(rows, key=lambda r: (not r["changed"], r["gap"] if r["gap"] is not None else -1)):
        f.write("%s %s %d %s %s %s\n" % (r["fen"], r["changed"], r["depth"], r["gap"],
                                         r.get("top", "-"), r.get("second", "-")))
print()
print("per-position rows -> %s" % OUT)
