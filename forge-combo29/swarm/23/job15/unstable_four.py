#!/usr/bin/env python3
"""unstable_four.py : what do the four genuinely-unstable positions share?

The four are the positions where only the 20000 budget differs AND the 250000 move does NOT score higher at
D_big (23-F29). For each one I record, as observable facts rather than interpretations:
  - the gap at the small (20000) depth, and at D_big
  - whether each candidate move is QUIET (no capture, no check, not a promotion) or not
  - whether the 20000 move and the 250000 move give CHECK
  - whether a capture appears on the board at the larger depth (a tactic the small budget could not see)
  - the evaluation swing between the two depths for the move the small budget chose

With four cases this can only produce a HYPOTHESIS, never a predictor, and the file says so.
PC r15, PC20, Threads 1, Hash 16, fresh process per search, drained to bestmove (19-F12).
"""
import json
import re
import subprocess
import sys

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else "../job7/pc20_opts.txt"
DATA = sys.argv[3] if len(sys.argv) > 3 else "../job10/out_60.json"
OUT = sys.argv[4] if len(sys.argv) > 4 else "unstable_four.out"

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


def describe(fen, uci):
    """observable properties of a move in the position, from the board only."""
    b = chess.Board(fen)
    m = chess.Move.from_uci(uci)
    capture = b.is_capture(m)
    b2 = b.copy()
    b2.push(m)
    check = b2.is_check()
    promo = m.promotion is not None
    quiet = not capture and not check and not promo
    return {"capture": capture, "check": check, "promotion": promo, "quiet": quiet}


d = json.load(open(DATA))
per = {}
for r in d["records"]:
    per.setdefault(r["fen"], {})[r["n"]] = r

unstable = []
for fen, m in per.items():
    a = m[20000]["bestmove"]
    b50 = m[50000]["bestmove"]
    c = m[250000]["bestmove"]
    if not (a != b50 and b50 == c):        # only the 20000 budget differs
        continue
    D_small = m[20000]["depths"][-1][0]
    D_big = m[250000]["depths"][-1][0]
    sa_small = centi(score_of(fen, a, D_small))
    sc_small = centi(score_of(fen, c, D_small))
    sa_big = centi(score_of(fen, a, D_big))
    sc_big = centi(score_of(fen, c, D_big))
    if sa_big is None or sc_big is None:
        continue
    if sa_big > sc_big:                    # the big budget's move is better -> a correction, not instability
        continue
    unstable.append({"fen": fen, "a": a, "c": c, "D_small": D_small, "D_big": D_big,
                     "gap_small": None if (sa_small is None or sc_small is None) else abs(sa_small - sc_small),
                     "gap_big": sa_big - sc_big, "sa_big": sa_big, "sc_big": sc_big,
                     "a_props": describe(fen, a), "c_props": describe(fen, c)})

print("THE GENUINELY UNSTABLE POSITIONS (only the 20000 budget differs, and the 250000 move is NOT better)")
print("PC r15, PC20, Threads 1, Hash 16")
print()
print("| # | fen | D_small | D_big | gap at D_small | 20000 move (quiet?) | 250000 move (quiet?) | score gap at D_big |")
print("|---|---|---|---|---|---|---|---|")
for i, u in enumerate(unstable, 1):
    print("| %d | %s | %d | %d | %s | %s (%s) | %s (%s) | %d |" %
          (i, u["fen"], u["D_small"], u["D_big"],
           u["gap_small"] if u["gap_small"] is not None else "n/a",
           u["a"], "quiet" if u["a_props"]["quiet"] else "tactical",
           u["c"], "quiet" if u["c_props"]["quiet"] else "tactical",
           u["gap_big"]))

print()
print("what they share (counts, with the caveat that n = %d):" % len(unstable))
both_quiet = sum(1 for u in unstable if u["a_props"]["quiet"] and u["c_props"]["quiet"])
any_capture = sum(1 for u in unstable if u["a_props"]["capture"] or u["c_props"]["capture"])
any_check = sum(1 for u in unstable if u["a_props"]["check"] or u["c_props"]["check"])
print("  both candidate moves QUIET (no capture, check or promotion): %d of %d" % (both_quiet, len(unstable)))
print("  at least one candidate is a CAPTURE:                          %d of %d" % (any_capture, len(unstable)))
print("  at least one candidate gives CHECK:                           %d of %d" % (any_check, len(unstable)))
gaps_small = [u["gap_small"] for u in unstable if u["gap_small"] is not None]
if gaps_small:
    gaps_small.sort()
    print("  gap at the small depth: min %d, median %d, max %d"
          % (gaps_small[0], gaps_small[len(gaps_small) // 2], gaps_small[-1]))
gaps_big = sorted(u["gap_big"] for u in unstable)
print("  signed gap at the big depth (negative = the 20000 move is better): min %d, max %d" % (gaps_big[0], gaps_big[-1]))

with open(OUT, "w") as f:
    for u in unstable:
        f.write("%s a=%s(%s) c=%s(%s) D_small=%d D_big=%d gap_small=%s gap_big=%d\n"
                % (u["fen"], u["a"], "quiet" if u["a_props"]["quiet"] else "tactical",
                   u["c"], "quiet" if u["c_props"]["quiet"] else "tactical",
                   u["D_small"], u["D_big"], u["gap_small"], u["gap_big"]))
print()
print("rows -> %s" % OUT)
