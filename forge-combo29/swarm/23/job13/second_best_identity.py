#!/usr/bin/env python3
"""second_best_identity.py : is a budget-sensitive position exactly one where the SECOND-BEST move changes identity?

The coordinator's hypothesis: the instability may not be about the size of the gap but about whether the identity
of the runner-up move is stable between adjacent depths. This measures that directly.

Method, per position:
  D  = the depth the 20000 budget actually reached (from job10's data)
  C  = the candidate set used in job12: for a changed position the two moves the budgets disagreed about; for an
       unchanged position the bestmove plus up to 3 random legal alternatives
  rank C at depth D-1 and at depth D by scoring each move ALONE (`go depth X searchmoves <move>`)
  signature = does the identity of the SECOND-best move differ between D-1 and D?

Then cross-tabulate the signature against whether the move actually changed between budgets. If the two coincide,
the signature is exact; if not, it is another (weaker) statistic and must be reported as such.

PC r15, PC20, Threads 1, Hash 16, fresh process per search, drained to bestmove (19-F12).
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
OUT = sys.argv[4] if len(sys.argv) > 4 else "second_best_identity.out"

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
    changed = mv20 != mv250
    D = m[20000]["depths"][-1][0]
    board = chess.Board(fen)
    if changed:
        cand = [mv20, mv250]
    else:
        others = [x.uci() for x in board.legal_moves if x.uci() != mv20]
        rng.shuffle(others)
        cand = [mv20] + others[:3]
    cand = list(dict.fromkeys(cand))
    r_next, r_prev = [], []
    for mv in cand:
        s_n = centi(score_of(fen, mv, D))
        s_p = centi(score_of(fen, mv, D - 1))
        if s_n is not None:
            r_next.append((s_n, mv))
        if s_p is not None:
            r_prev.append((s_p, mv))
    r_next.sort(reverse=True)
    r_prev.sort(reverse=True)
    sb_next = r_next[1][1] if len(r_next) > 1 else None
    sb_prev = r_prev[1][1] if len(r_prev) > 1 else None
    best_next = r_next[0][1] if r_next else None
    best_prev = r_prev[0][1] if r_prev else None
    rows.append({"fen": fen, "changed": changed, "D": D,
                 "sb_prev": sb_prev, "sb_next": sb_next,
                 "sb_stable": (sb_next == sb_prev) if (sb_next and sb_prev) else None,
                 "best_prev": best_prev, "best_next": best_next,
                 "best_stable": (best_next == best_prev) if (best_next and best_prev) else None})

ch = [r for r in rows if r["changed"]]
un = [r for r in rows if not r["changed"]]


def tab(group, key):
    a = sum(1 for r in group if r[key] is True)
    b = sum(1 for r in group if r[key] is False)
    c = sum(1 for r in group if r[key] is None)
    return a, b, c


print("SECOND-BEST IDENTITY between the last two depths the 20000 budget reached")
print("PC r15, PC20, Threads 1, Hash 16")
print()
print("| group | n | second-best identity STABLE | second-best identity CHANGED | undetermined |")
print("|---|---|---|---|---|")
for name, g in (("move changed between budgets", ch), ("move unchanged", un)):
    a, b, c = tab(g, "sb_stable")
    print("| %s | %d | %d | %d | %d |" % (name, len(g), a, b, c))
print()
print("| group | n | BEST move stable | best move changed |")
print("|---|---|---|---|")
for name, g in (("move changed between budgets", ch), ("move unchanged", un)):
    a, b, c = tab(g, "best_stable")
    print("| %s | %d | %d | %d |" % (name, len(g), a, b))

# the exact-signature test
tb = sum(1 for r in ch if r["sb_stable"] is False)
fn = sum(1 for r in un if r["sb_stable"] is False)
tp_fp = sum(1 for r in rows if r["sb_stable"] is False)
print()
print("exact-signature test ('second-best identity changed' == 'move changed between budgets'):")
print("  changed positions with the signature : %d of %d" % (tb, len(ch)))
print("  unchanged positions with the signature: %d of %d (these are false alarms)" % (fn, len(un)))
print("  signature fires on %d positions in total" % tp_fp)

with open(OUT, "w") as f:
    f.write("fen changed D sb_prev sb_next sb_stable best_prev best_next best_stable\n")
    for r in rows:
        f.write("%s %s %d %s %s %s %s %s %s\n" % (r["fen"], r["changed"], r["D"], r["sb_prev"],
                                                 r["sb_next"], r["sb_stable"], r["best_prev"],
                                                 r["best_next"], r["best_stable"]))
print()
print("per-position rows -> %s" % OUT)
