#!/usr/bin/env python3
"""deepseek6 long 66: the engine's static evaluation, checked for mirror symmetry.

For each FEN it asks the engine `eval` (one process for the whole run) and parses the terminal
line `info string eval hce <h> nnue <n> total <t> [incheck 1]`. The number compared is `total`,
which the engine reports from the side to move's point of view; the harness does not re-sign it.

Three comparisons:
  control     position 1 compared with itself (must be equal)
  colour      board.mirror() -- colours and side to move swapped, castling and ep mirrored
  lefright    board.transform(chess.flip_horizontal), ONLY positions with no castling rights

usage: evalsym.py <exe> <fens> <outdir> <tag>
"""
import os
import re
import subprocess
import sys

import chess

EXE, FENS, OUT, TAG = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(OUT, exist_ok=True)
fens = [l.strip() for l in open(FENS) if l.strip()]

EVAL = re.compile(r"info string eval hce (-?\d+) nnue (-?\d+) total (-?\d+)( incheck 1)?")

p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, text=True, bufsize=1)
assert p.stdin and p.stdout


def w(s):
    p.stdin.write(s + "\n")
    p.stdin.flush()


w("uci")
while True:
    l = p.stdout.readline()
    if not l or l.startswith("uciok"):
        break
w("setoption name Threads value 1")
w("setoption name OwnBook value false")
w("isready")
while True:
    l = p.stdout.readline()
    if not l or l.startswith("readyok"):
        break


def ask(fen):
    w("position fen %s" % fen)
    w("eval")
    w("isready")
    total = None
    incheck = False
    while True:
        line = p.stdout.readline()
        if not line:
            break
        m = EVAL.search(line)
        if m:
            total = int(m.group(3))
            incheck = bool(m.group(4))
        if line.startswith("readyok"):
            break
    return total, incheck


rows = []
for i, fen in enumerate(fens, 1):
    total, inc = ask(fen)
    rows.append((i, fen, total, inc))
    if i % 100 == 0:
        print("...%d/%d" % (i, len(fens)), flush=True)

w("quit")
try:
    p.wait(timeout=60)
except subprocess.TimeoutExpired:
    p.kill()

with open(os.path.join(OUT, TAG + ".evals.tsv"), "w") as f:
    f.write("pos\ttotal\tincheck\tfen\n")
    for i, fen, t, inc in rows:
        f.write("%d\t%s\t%s\t%s\n" % (i, t, 1 if inc else 0, fen))


# ---- control ----
p2 = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, text=True, bufsize=1)


def w2(s):
    p2.stdin.write(s + "\n")
    p2.stdin.flush()


w2("uci")
while True:
    l = p2.stdout.readline()
    if not l or l.startswith("uciok"):
        break
w2("isready")
while True:
    l = p2.stdout.readline()
    if not l or l.startswith("readyok"):
        break


def ask2(fen):
    w2("position fen %s" % fen)
    w2("eval")
    w2("isready")
    t = None
    while True:
        line = p2.stdout.readline()
        if not line:
            break
        m = EVAL.search(line)
        if m:
            t = int(m.group(3))
        if line.startswith("readyok"):
            break
    return t


self_total = ask2(rows[0][1])
print()
print("== CONTROL: position 1 with itself")
print("   first read %s, second read %s -> %s" % (rows[0][2], self_total,
                                                  "EQUAL" if rows[0][2] == self_total else "DIFFER"))

# ---- colour mirror ----
colour_diff = []
for i, fen, t, inc in rows:
    b = chess.Board(fen)
    mb = b.mirror()
    mt = ask2(mb.fen())
    _, minc = None, None
    colour_diff.append((i, fen, t, mt, mb.fen()))

# ---- left-right mirror (no castling rights only) ----
lr_rows = [(i, fen, t) for i, fen, t, inc in rows if chess.Board(fen).castling_rights == 0]
lr_diff = []
for i, fen, t in lr_rows:
    b = chess.Board(fen)
    tb = b.transform(chess.flip_horizontal)
    tt = ask2(tb.fen())
    lr_diff.append((i, fen, t, tt, tb.fen()))

w2("quit")
try:
    p2.wait(timeout=60)
except subprocess.TimeoutExpired:
    p2.kill()

ceq = sum(1 for i, fen, a, bb, mfen in colour_diff if a == bb)
print()
print("== COLOUR FLIP over all %d G positions" % len(colour_diff))
print("   equal: %d   differ: %d" % (ceq, len(colour_diff) - ceq))
for i, fen, a, bb, mfen in colour_diff:
    if a != bb:
        print("   DIFF pos %d: %s  vs mirror %s -> %s and %s (delta %+d)" %
              (i, fen, mfen, a, bb, bb - a))

print()
print("== LEFT-RIGHT FLIP over the %d positions with NO castling rights" % len(lr_rows))
print("   equal: %d   differ: %d" % (sum(1 for i, fen, a, bb, mfen in lr_diff if a == bb),
                                     sum(1 for i, fen, a, bb, mfen in lr_diff if a != bb)))
for i, fen, a, bb, mfen in lr_diff:
    if a != bb:
        print("   DIFF pos %d: %s -> %s and %s (delta %+d)" % (i, fen, a, bb, bb - a))

with open(os.path.join(OUT, TAG + ".colour.tsv"), "w") as f:
    f.write("pos\toriginal\tmirror\tdelta\tfen\tmirror_fen\n")
    for i, fen, a, bb, mfen in colour_diff:
        f.write("%d\t%s\t%s\t%s\t%s\t%s\n" % (i, a, bb, ("" if a is None or bb is None else bb - a), fen, mfen))
with open(os.path.join(OUT, TAG + ".lefright.tsv"), "w") as f:
    f.write("pos\toriginal\tflipped\tdelta\tfen\tflipped_fen\n")
    for i, fen, a, bb, mfen in lr_diff:
        f.write("%d\t%s\t%s\t%s\t%s\t%s\n" % (i, a, bb, ("" if a is None or bb is None else bb - a), fen, mfen))
print()
print("written to", OUT)
