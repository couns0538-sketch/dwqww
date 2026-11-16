#!/usr/bin/env python3
"""file6_rule1.py : apply FABLE_TO_swarm_6's rule 1 EXACTLY, on the PC build under PC20 at Threads 1.

File 6: "A cp 0 at a high counter is a defect ONLY when a forced mate exists that ends no later than the 100th
half-move. Test: the same board with counter 0, `go depth 20` or more, read `mate N`; it is a defect only if
2N - 1 <= 100 - counter AND the board at the real counter still scores cp 0 at that depth. Put both numbers in
the finding line."

So for each board and each counter H I:
  1. build the counter-0 version and search it at `go depth D` (D=20 default), read `mate N`;
  2. compute plies_needed = 2N-1 (N>0) and slack = 100 - H;
  3. search the SAME board at counter H for the SAME depth D and record the score;
  4. verdict = DEFECT only if (mate found) and (plies_needed <= slack) and (score at H is cp 0).
Otherwise NOT A DEFECT under file 6.
This is a decision procedure, so a case that fails to produce a mate is reported as such, never as "fine".
"""
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else "../job7/pc20_opts.txt"
OUT = sys.argv[3] if len(sys.argv) > 3 else "rule1.out"
DEPTH = int(sys.argv[4]) if len(sys.argv) > 4 else 20

# boards chosen to be WON (mating material) so a mate must exist, plus one drawn control
BOARDS = [
    ("KQ_vs_K",   "8/5K2/7Q/4k3/8/8/8/8 w - - {} 1"),
    ("KR_vs_K",   "8/1K6/8/8/3R4/8/8/k7 w - - {} 1"),
    ("KQ_vs_K2",  "8/8/8/8/8/1k6/8/3QK3 w - - {} 1"),
    ("drawn_KK",  "8/8/8/8/4k3/8/8/4K3 w - - {} 1"),
]
COUNTERS = [0, 50, 90, 91, 99, 100, 150]

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")


import chess


def check_fen(fen):
    b = chess.Board(fen)
    if not b.is_valid():
        raise RuntimeError("REFUSING to measure an invalid FEN: %r (status %s)" % (fen, b.status()))


def search(fen, depth):
    check_fen(fen)
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        l = p.stdout.readline()
        if not l or l.strip() == "uciok":
            break
        if l.startswith("option name "):
            names.add(l.split("option name ")[1].split(" type ")[0])
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
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None
    nodes = 0
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)))
            nm2 = re.search(r"nodes (\d+)", s)
            if nm2:
                nodes = int(nm2.group(1))
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return last, nodes


rows = []
print("exe %s depth %d threads 1" % (EXE, DEPTH))
print()
print("| board | counter H | counter-0 score | plies needed | slack (100-H) | score at H | verdict under file 6 |")
print("|---|---|---|---|---|---|---|")
for name, pattern in BOARDS:
    base_fen = pattern.format("0")
    ref, refnodes = search(base_fen, DEPTH)
    if ref is None:
        print("| %s | - | NO SCORE | - | - | - | harness problem, not a verdict |" % name)
        continue
    kind, val = ref
    if kind == "mate" and val > 0:
        need = 2 * val - 1
    elif kind == "mate":
        need = 2 * abs(val)
    else:
        need = None
    for h in COUNTERS:
        fen = pattern.format(str(h))
        got, nodes = search(fen, DEPTH)
        score = "%s %d" % got if got else "NO SCORE"
        if kind != "mate":
            verdict = "n/a (no mate at counter 0: %s %d)" % (kind, val)
        elif h >= 100:
            verdict = "game already drawn at this counter (no claim applies)"
        else:
            slack = 100 - h
            if need <= slack and got == ("cp", 0):
                verdict = "**DEFECT** (mate in %d plies fits in %d)" % (need, slack)
            elif need <= slack:
                verdict = "not a defect (mate fits but score is %s %d)" % got
            else:
                verdict = "not a defect (needs %d plies, only %d left)" % (need, slack)
        rows.append((name, h, "%s %d" % (kind, val), need, score, verdict))
        print("| %s | %d | %s %d | %s | %s | %s | %s |" %
              (name, h, kind, val, need if need else "-",
               (100 - h) if h < 100 else "drawn", score, verdict))
print()
print("decision rule: DEFECT only when a mate exists at counter 0 AND 2N-1 <= 100-H AND the board at H scores cp 0.")
