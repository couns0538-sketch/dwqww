#!/usr/bin/env python3
"""margins.py : why does the budget change the move? Measure the MARGIN between the two candidate moves.

For each position and budget: take the move chosen at 20000 and the move chosen at 250000, then search EACH of
them alone at a FIXED depth (18) with `go depth 18 searchmoves <move>` — same depth for both, so the comparison is
like-for-like and does not depend on the budget. The gap between those two scores is the margin.

Protocol: PC r15, PC20, Threads 1, Hash 16, fresh process per search, drained to bestmove (19-F12).
"""
import json
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else "../job7/pc20_opts.txt"
DATA = sys.argv[3] if len(sys.argv) > 3 else "../job10/out_60.json"
OUT = sys.argv[4] if len(sys.argv) > 4 else "margins.out"
FIXED_DEPTH = int(sys.argv[5]) if len(sys.argv) > 5 else 18

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")


def score_of(fen, move, depth):
    """score the engine gives to `move` alone at a fixed depth (searchmoves restricts the root to it)."""
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


def centi(score):
    """mate scores put far outside any cp range, ordered by distance."""
    if score is None:
        return None
    kind, val = score
    if kind == "mate":
        return 100000 - 100 * abs(val) if val > 0 else -100000 + 100 * abs(val)
    return val


d = json.load(open(DATA))
per = {}
for r in d["records"]:
    per.setdefault(r["fen"], {})[r["n"]] = r

changed, unchanged = [], []
for fen, m in per.items():
    a = m[20000]["bestmove"]
    c = m[250000]["bestmove"]
    if a == c:
        # unchanged: compare the top move with the second-best root move the engine reports, if any
        unchanged.append((fen, a, None))
    else:
        changed.append((fen, a, c))

print("exe %s, options %s, fixed depth %d for both candidates" % (EXE, OPTFILE, FIXED_DEPTH))
print()
rows = []
print("== CHANGED positions: score of the 20000-move and the 250000-move, each alone, at depth %d" % FIXED_DEPTH)
print("| fen | move@20000 | score | move@250000 | score | gap (cp) | winner |")
print("|---|---|---|---|---|---|---|")
for fen, a, c in changed:
    sa = centi(score_of(fen, a, FIXED_DEPTH))
    sc = centi(score_of(fen, c, FIXED_DEPTH))
    if sa is None or sc is None:
        print("| %s | %s | MISSING | %s | MISSING | - | - |" % (fen, a, c))
        continue
    gap = abs(sa - sc)
    # A tie must be its own outcome: `a if sa > sc else c` credits an equal score to c,
    # and the c-count below would then read the tie as evidence for the 250000 budget (23-F225).
    if sa > sc:
        winner = a
    elif sc > sa:
        winner = c
    else:
        winner = "tie"
    rows.append({"fen": fen, "a": a, "sa": sa, "c": c, "sc": sc, "gap": gap, "winner": winner})
    print("| %s | %s | %d | %s | %d | %d | %s |" % (fen, a, sa, c, sc, gap, winner))

if rows:
    gaps = sorted(r["gap"] for r in rows)
    med = gaps[len(gaps) // 2]
    better_250 = sum(1 for r in rows if r["winner"] == r["c"])
    ties = sum(1 for r in rows if r["winner"] == "tie")
    print()
    print("changed positions measured: %d" % len(rows))
    print("gap (centipawns, both candidates at depth %d): min %d, median %d, max %d"
          % (FIXED_DEPTH, gaps[0], med, gaps[-1]))
    print("positions where the 250000 move scores HIGHER at the fixed depth: %d of %d (%.0f %%)"
          % (better_250, len(rows), 100.0 * better_250 / len(rows)))
    print("ties (equal score at the fixed depth, counted for NEITHER budget): %d" % ties)
    print("positions where the two candidates are within 30 cp: %d" % sum(1 for g in gaps if g <= 30))

with open(OUT, "w") as f:
    f.write("fixed depth %d, PC r15, PC20, Threads 1, Hash 16\n" % FIXED_DEPTH)
    for r in rows:
        f.write("%s a=%s(%d) c=%s(%d) gap=%d winner=%s\n"
                % (r["fen"], r["a"], r["sa"], r["c"], r["sc"], r["gap"], r["winner"]))
print()
print("rows -> %s" % OUT)
