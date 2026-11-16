#!/usr/bin/env python3
"""deepseek6 long 61: MultiPV correctness on all of O at depth 10.

Per position and per MultiPV k in {1, 3, 5}: one fresh process, S14, Threads 1, Hash 16, and
read the LAST complete iteration's k lines. Checks, per position:
  * the k lines carry k DIFFERENT legal moves
  * the scores do not increase down the list (multipv 1 >= 2 >= ... >= k)
  * the moves are legal on the board (python-chess)
and across k: the first line's move under k=3 and k=5 against k=1's bestmove.

WHY PERSISTENT STDIN: this engine aborts a search when stdin closes (long-25 lesson), so the
driver holds stdin open until `bestmove`.

usage: multipv61.py <exe> <fens> <outdir>
"""
import os
import re
import subprocess
import sys

import chess

EXE, FENS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DEPTH = 10
KS = [1, 3, 5]
os.makedirs(OUT, exist_ok=True)
fens = [l.strip() for l in open(FENS) if l.strip()]

S14 = ["name Threads value 1", "name Hash value 16", "name OwnBook value false",
       "name LmrQuietBase value 93", "name LmrQuietDivisor value 205", "name LmrNoisyBase value 13",
       "name LmrNoisyDivisor value 333", "name LmrHistoryDivisor value 5643", "name NullMoveBase value 5",
       "name LmpBase value 8", "name HistoryPruneMultiplier value 2220", "name HistoryBonusQuadratic value 24",
       "name HistoryBonusLinear value 54", "name HistoryBonusMax value 2212", "name SingularDepth value 6",
       "name IirDepth value 2", "name NonPawnCorrection value true"]

LINE = re.compile(r"info depth (\d+) multipv (\d+) score (\S+) (\S+) .*nodes (\d+).* pv (\S+)")


def run(fen, k, board_legal_count):
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
    for o in S14 + ["name MultiPV value %d" % k]:
        w("setoption %s" % o)
    w("isready")
    while True:
        l = p.stdout.readline()
        if not l or l.startswith("readyok"):
            break
    w("ucinewgame")
    w("isready")
    while True:
        l = p.stdout.readline()
        if not l or l.startswith("readyok"):
            break
    w("position fen %s" % fen)
    w("go depth %d" % DEPTH)
    lines = []
    bm = None
    while True:
        l = p.stdout.readline()
        if not l:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("bestmove"):
            bm = l.split()[1]
            break
    w("quit")
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    # the last complete iteration: the highest depth with exactly k multipv entries
    per = {}
    for l in lines:
        m = re.search(r"info depth (\d+) multipv (\d+) score (cp|mate) (-?\d+) .*nodes (\d+).*? pv (\S+)", l)
        if m:
            d, i, kind, val, nodes, mv = int(m.group(1)), int(m.group(2)), m.group(3), int(m.group(4)), int(m.group(5)), m.group(6)
            per.setdefault(d, {})[i] = (kind, val, nodes, mv)
            continue
        # MultiPV 1 prints the plain form, with no "multipv" token
        m = re.search(r"info depth (\d+) seldepth \d+ score (cp|mate) (-?\d+) .*nodes (\d+).*? pv (\S+)", l)
        if m:
            d, kind, val, nodes, mv = int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4)), m.group(5)
            per.setdefault(d, {})[1] = (kind, val, nodes, mv)
    want = min(k, board_legal_count)
    best_d = None
    for d in sorted(per):
        if len(per[d]) == want:
            best_d = d
    if best_d is None:
        return None, bm, "no complete iteration with %d lines" % k
    rows = [per[best_d][i] for i in range(1, k + 1) if i in per[best_d]]
    return rows, bm, None, k


def score_of(kind, val):
    """Mate scores outrank everything and rank by magnitude; cp is centipawns."""
    return (1000000 - abs(val)) if kind == "mate" and val > 0 else (-1000000 + abs(val)) if kind == "mate" else val


bad = []
first1 = {}
firstk = {3: {}, 5: {}}
for idx, fen in enumerate(fens, 1):
    board = chess.Board(fen)
    legal = {m.uci() for m in board.legal_moves}
    for k in KS:
        rows, bm, err, want = run(fen, k, len(legal))
        if err:
            bad.append((idx, k, "iteration", err))
            continue
        moves = [r[3] for r in rows]
        if len(set(moves)) != len(moves):
            bad.append((idx, k, "duplicate_move", moves))
        scores = [score_of(r[0], r[1]) for r in rows]
        if any(scores[i] < scores[i + 1] for i in range(len(scores) - 1)):
            bad.append((idx, k, "score_order", scores))
        if any(mv not in legal for mv in moves):
            bad.append((idx, k, "illegal_pv", [mv for mv in moves if mv not in legal]))
        if moves[0] != bm:
            bad.append((idx, k, "first_line_vs_bestmove", (moves[0], bm)))
        if k == 1:
            first1[idx] = bm
        else:
            firstk[k][idx] = moves[0]
    if idx % 25 == 0:
        print("...%d/200" % idx, flush=True)

print()
print("== MultiPV CHECK ON ALL %d POSITIONS OF O, DEPTH %d" % (len(fens), DEPTH))
print("violations: %d" % len(bad))
for b in bad[:20]:
    print("  pos %d k=%d %s %r" % b)
for k in (3, 5):
    same = sum(1 for i in first1 if firstk[k].get(i) == first1[i])
    print("k=%d: first line equals k=1's bestmove on %d of %d (different on %d)" %
          (k, same, len(first1), len(first1) - same))
