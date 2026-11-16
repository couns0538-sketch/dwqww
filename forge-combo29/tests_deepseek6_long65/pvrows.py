#!/usr/bin/env python3
"""deepseek6 long 65: collect the LAST `info ... pv` line of every search, and check PV legality.

One fresh engine process per position (the rows.py path), S14, ucinewgame + isready before every
`go`. For each search it stores index | nodes | bestmove | score | pv, where `pv` is the PV of
the LAST info line that carried one (the deepest completed iteration).

Then it replays each PV with python-chess and reports:
  * every ply legal, and the first illegal ply if not
  * mate scores: `mate N` with N>0 must end in checkmate after 2N-1 plies; N<0 after 2|N| plies
  * PVs that end in checkmate while the score is a plain centipawn score
  * PV length distribution

usage: pvrows.py <exe> <fens> <outdir> <tag>
"""
import os
import re
import subprocess
import sys

import chess

EXE, FENS, OUT, TAG = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
DEPTH = 12
os.makedirs(OUT, exist_ok=True)
fens = [l.strip() for l in open(FENS) if l.strip()]

S14 = ["name Threads value 1", "name Hash value 16", "name OwnBook value false",
       "name LmrQuietBase value 93", "name LmrQuietDivisor value 205", "name LmrNoisyBase value 13",
       "name LmrNoisyDivisor value 333", "name LmrHistoryDivisor value 5643", "name NullMoveBase value 5",
       "name LmpBase value 8", "name HistoryPruneMultiplier value 2220", "name HistoryBonusQuadratic value 24",
       "name HistoryBonusLinear value 54", "name HistoryBonusMax value 2212", "name SingularDepth value 6",
       "name IirDepth value 2", "name NonPawnCorrection value true"]

INFO = re.compile(r"^info depth \d+ (?:multipv \d+ )?.*score (cp|mate) (-?\d+) .*? pv (.+)$")

rows_path = os.path.join(OUT, TAG + ".pvrows")
with open(rows_path, "w") as rf:
    rf.write("pos\tnodes\tbestmove\tscore_kind\tscore\tpv\n")
    for idx, fen in enumerate(fens, 1):
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
        for o in S14:
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
        nodes = None
        bm = None
        kind = None
        val = None
        pv = None
        while True:
            line = p.stdout.readline()
            if not line:
                break
            if line.startswith("bestmove"):
                parts = line.split()
                bm = parts[1] if len(parts) > 1 else "NOBM"
                break
            m = re.search(r"\bnodes (\d+)", line)
            if line.startswith("info depth") and m:
                nodes = int(m.group(1))
            mi = INFO.match(line)
            if mi:
                kind, val, pv = mi.group(1), int(mi.group(2)), mi.group(3).split()
        w("quit")
        try:
            p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            p.kill()
        rf.write("%d\t%s\t%s\t%s\t%s\t%s\n" % (idx, nodes, bm, kind, val, " ".join(pv) if pv else ""))
        if idx % 50 == 0:
            print("...%d/%d" % (idx, len(fens)), flush=True)

print("written", rows_path)


# ---------------- the checker ----------------
def check(rows_path, fens):
    bad_legal = []
    mate_mismatch = []
    mate_total = 0
    mate_ok = 0
    checkmate_nonmate = 0
    lengths = []
    unparsed = 0
    total = 0
    for line in open(rows_path):
        f = line.rstrip("\n").split("\t")
        if len(f) != 6 or f[0] == "pos":
            continue
        idx, nodes, bm, kind, val, pv = f
        idx = int(idx) - 1
        total += 1
        board = chess.Board(fens[idx])
        moves = pv.split() if pv else []
        if not moves:
            unparsed += 1
            continue
        lengths.append(len(moves))
        legal_until = 0
        for ply, mv in enumerate(moves, 1):
            try:
                m = chess.Move.from_uci(mv)
            except Exception:
                bad_legal.append((idx + 1, ply, mv, "unparseable"))
                legal_until = -1
                break
            if m not in board.legal_moves:
                bad_legal.append((idx + 1, ply, mv, "illegal"))
                legal_until = -1
                break
            board.push(m)
            legal_until = ply
        if legal_until < 0:
            continue
        ends_mate = board.is_checkmate()
        if kind == "mate":
            mate_total += 1
            n = int(val)
            want = (2 * n - 1) if n > 0 else (2 * abs(n))
            if ends_mate and len(moves) == want:
                mate_ok += 1
            else:
                mate_mismatch.append((idx + 1, n, want, len(moves), ends_mate))
        elif ends_mate:
            checkmate_nonmate += 1
    return dict(total=total, bad_legal=bad_legal, mate_total=mate_total, mate_ok=mate_ok,
                mate_mismatch=mate_mismatch, checkmate_nonmate=checkmate_nonmate,
                unparsed=unparsed, lengths=lengths)


r = check(rows_path, fens)
L = r["lengths"]
print()
print("== %s" % TAG)
print("searches: %d   PVs with at least one move: %d   empty/unparsed: %d" %
      (r["total"], len(L), r["unparsed"]))
print("PVs fully legal: %d of %d" % (len(L) - len(r["bad_legal"]), len(L)))
print("first illegal ply (up to 10):")
for b in r["bad_legal"][:10]:
    print("   pos %d ply %d move %s (%s)" % b)
print("mate scores: %d   whose PV ends in mate at the stated length: %d" % (r["mate_total"], r["mate_ok"]))
for m in r["mate_mismatch"][:10]:
    print("   MISMATCH pos %d mate %d (want %d plies), PV has %d, ends in mate: %s" % m)
print("PVs ending in checkmate with a non-mate score: %d" % r["checkmate_nonmate"])
if L:
    print("PV length: min %d, max %d, plies < 4: %d (%.1f %%), plies > 64: %d" %
          (min(L), max(L), sum(1 for x in L if x < 4), 100.0 * sum(1 for x in L if x < 4) / len(L),
           sum(1 for x in L if x > 64)))
