#!/usr/bin/env python3
"""check_06SF1.py : independent check of seat 06's S-F1 (eval is exactly colour-symmetric).

Claim: `eval` gives 0 differences in hce/nnue/total over thousands of colour-mirrored position pairs.

Method: for each position, read `eval`'s three numbers; read the same for the colour-flipped mirror; the MIRRORED
evaluation must report the NEGATION of the original (a colour flip swaps the point of view), so the test is
total_orig + total_mirror == 0, likewise hce and nnue.

CONTROLS, mandatory before any zero is believed:
  - a position against ITSELF must give identical numbers (not negated) — this shows the harness can read the same
    board twice and that it is not silently comparing a position to itself when it should compare to a mirror;
  - the mirror must actually be a different board (piece squares flipped, side to move swapped), asserted.
"""
import re
import subprocess
import sys

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else ""
FENS = sys.argv[3] if len(sys.argv) > 3 else "../job5/R_2401.fens"
N = int(sys.argv[4]) if len(sys.argv) > 4 else 200

EVAL = re.compile(r"eval hce (-?\d+) nnue (-?\d+) total (-?\d+)")


def evals(fen, opts):
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
    for line in opts:
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
    p.stdin.write("eval\n"); p.stdin.flush()
    got = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in eval")
        s = l.strip()
        m = EVAL.search(s)
        if m:
            got = tuple(int(m.group(i)) for i in (1, 2, 3))
        if s == "readyok" or m:
            # eval answers then isready-completes; take the first eval line
            if got:
                break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return got


opts = []
if OPTFILE:
    opts = [x.strip() for x in open(OPTFILE) if x.strip() and not x.startswith("#")]

# --- mandatory controls ---
print("== controls")
b = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3")
same = evals(b.fen(), opts)
again = evals(b.fen(), opts)
print("  same board twice: %s and %s -> identical: %s (must be True)" % (same, again, same == again))
mir = b.mirror()
assert mir.fen() != b.fen(), "mirror must differ"
assert mir.turn == (not b.turn), "mirror must swap side to move"
print("  mirror is a different board with the other side to move: PASS")
me = evals(mir.fen(), opts)
print("  original %s vs mirror %s -> totals sum to %d (colour symmetry says 0)" % (same, me, same[2] + me[2]))

fens = [l.strip() for l in open(FENS) if l.strip()][:N]
print()
print("== %d positions, base build, Threads 1, Hash 16" % len(fens))
tot_eq = hce_eq = nnue_eq = 0
tot = 0
worst = []
for fen in fens:
    a = evals(fen, opts)
    m = evals(chess.Board(fen).mirror().fen(), opts)
    if a is None or m is None:
        continue
    tot += 1
    dt = a[2] + m[2]
    dh = a[0] + m[0]
    dn = a[1] + m[1]
    if dt == 0:
        tot_eq += 1
    if dh == 0:
        hce_eq += 1
    if dn == 0:
        nnue_eq += 1
    if dt != 0:
        worst.append((abs(dt), fen, a, m))
print("| component | pairs where original + mirror == 0 | of |")
print("|---|---|---|")
print("| hce | %d | %d |" % (hce_eq, tot))
print("| nnue | %d | %d |" % (nnue_eq, tot))
print("| total | %d | %d |" % (tot_eq, tot))
worst.sort(reverse=True)
if worst:
    print()
    print("largest total asymmetries:")
    for d, fen, a, m in worst[:5]:
        print("  |sum| %d  fen=%s orig=%s mirror=%s" % (d, fen, a, m))
