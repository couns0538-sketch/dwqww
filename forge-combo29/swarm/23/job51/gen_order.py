#!/usr/bin/env python3
"""job51 : is the engine's generation ORDER blocked by piece type, and is index 0 predictable?

Same deterministic sample as job50 (every 400th line of the validated seed-2301 set) so the two jobs share a
population. For each position: `go perft 1` divides, parsed and ASSERTED against the `nodes` total (23-F99).
  (a) block structure of the piece-type sequence (a switch back to an earlier type = a new block)
  (b) piece type of index 0, and whether it is the highest-priority type present
  (c) stability: the same divide from a fresh process must be identical

Nothing is inferred beyond what the divides show; where the within-block order is not obvious, the output says so.
"""
import re, subprocess, sys, os
import chess

MOVELINE = re.compile(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$")
SUMMARY = re.compile(r"^nodes (\d+)$")
BASE = os.path.expanduser("~/build/forge")
FENS = sys.argv[1] if len(sys.argv) > 1 else "../job1/R_2301.fens"
STRIDE = 400
NAMES = {1: "P", 2: "N", 3: "B", 4: "R", 5: "Q", 6: "K"}


def conn():
    p = subprocess.Popen([BASE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    opts = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if s.startswith("option name "):
            opts.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in opts:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def divide(p, fen):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go perft 1\n"); p.stdin.flush()
    order = []
    total = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in perft")
        s = l.strip()
        m = MOVELINE.match(s)
        if m:
            order.append(m.group(1))
        ms = SUMMARY.match(s)
        if ms:
            total = int(ms.group(1))
            break
    return order, total


def blocks(types):
    """Number of runs in the sequence: 1 = perfectly grouped, >1 = switches back."""
    if not types:
        return 0
    seen = [types[0]]
    for t in types[1:]:
        if t != seen[-1]:
            seen.append(t)
    # count switches back to a type already left
    opened = {types[0]}
    left = set()
    n = 1
    for prev, cur in zip(types, types[1:]):
        if cur != prev:
            left.add(prev)
            if cur in left:
                n += 1
            opened.add(cur)
    return n


fens = [l.strip() for l in open(FENS) if l.strip()]
sample = [fens[i] for i in range(0, min(len(fens), STRIDE * 12), STRIDE)][:12]
print("sample: %d positions, every %dth line of %s" % (len(sample), STRIDE, FENS))
print()
print("| # | #moves | piece-type sequence | blocks | index-0 type | highest-priority present |")
print("|---|---|---|---|---|---|")
p = conn()
rows = []
for i, fen in enumerate(sample, 1):
    order, total = divide(p, fen)
    if total is None or len(order) != total or not order:
        print("| %d | **PARSE FAILURE** %d vs %s | - | - | - | - |" % (i, len(order), total))
        continue
    b = chess.Board(fen)
    types = []
    for mv in order:
        m = chess.Move.from_uci(mv)
        pc = b.piece_at(m.from_square)
        types.append(NAMES[pc.piece_type])
    # priority = order of first appearance
    priority = []
    for t in types:
        if t not in priority:
            priority.append(t)
    top = priority[0]
    nb = blocks(types)
    rows.append((i, types, nb, top, priority))
    print("| %d | %d | %s | %d | %s | %s |" % (i, len(order), "".join(types), nb, top, "".join(priority)))
    sys.stdout.flush()

print()
print("== stability: identical divide from a fresh process? ==")
unstable = 0
for i, fen in enumerate(sample, 1):
    o1, t1 = divide(p, fen)
    q = conn()
    o2, t2 = divide(q, fen)
    q.stdin.write("quit\n"); q.stdin.flush()
    try:
        q.wait(timeout=10)
    except Exception:
        q.kill()
    same = (o1 == o2)
    if not same:
        unstable += 1
        print("  position %d: **DIFFERS** %s vs %s" % (i, o1[:4], o2[:4]))
p.stdin.write("quit\n"); p.stdin.flush()
print("  unstable positions: %d of %d" % (unstable, len(sample)))

if rows:
    grouped = sum(1 for r in rows if r[2] <= 3)
    pawn_first = sum(1 for r in rows if r[3] == "P")
    print()
    print("P1 positions with <= 3 blocks: %d of %d" % (grouped, len(rows)))
    print("P2 index-0 is a pawn: %d of %d" % (pawn_first, len(rows)))
    print("   the 12 priority sequences (order of first appearance):")
    for r in rows:
        print("     %2d: %s" % (r[0], "".join(r[4])))
    print("P3 unstable: %d" % unstable)
