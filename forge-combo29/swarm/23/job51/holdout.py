#!/usr/bin/env python3
"""job51 holdout : test the generation-order hypotheses on positions NEVER used to form them.

T1: the piece-type sequence is ONE block and the priority is exactly P,N,B,R,Q,K
T2: within the pawn block the class order is non-decreasing: single <= double <= capture
T3: index 0 is a pawn move whenever pawn moves exist
Holdout = odd multiples of 400 lines (200, 600, 1000, ...), which were not in the 12-position sample.
"""
import re, subprocess, os, sys
import chess

MOVELINE = re.compile(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$")
SUM = re.compile(r"^nodes (\d+)$")
BASE = os.path.expanduser("~/build/forge")
NAMES = {1: 'P', 2: 'N', 3: 'B', 4: 'R', 5: 'Q', 6: 'K'}


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


def div(p, fen):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go perft 1\n"); p.stdin.flush()
    o = []
    tot = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in perft")
        s = l.strip()
        m = MOVELINE.match(s)
        if m:
            o.append(m.group(1))
        ms = SUM.match(s)
        if ms:
            tot = int(ms.group(1))
            break
    return o, tot


fens = [l.strip() for l in open('../job1/R_2301.fens') if l.strip()]
idxs = [i for i in range(199, len(fens), 400)][:15]
hold = [fens[i] for i in idxs]
print("holdout: %d positions at lines %s (never used to form the hypotheses)" % (len(hold), [i + 1 for i in idxs]))
print()
print("| # | #mv | priority | pawn classes | T1 | T2 | T3 |")
print("|---|---|---|---|---|---|---|")
p = conn()
ok1 = ok2 = ok3 = tot = 0
fails = []
for n, fen in enumerate(hold, 1):
    o, t = div(p, fen)
    if not o or t != len(o):
        print("| %d | **PARSE FAILURE** (%d vs %s) | - | - | - | - | - |" % (n, len(o), t))
        fails.append((n, "parse"))
        continue
    b = chess.Board(fen)
    types = []
    seq = []
    idx0 = None
    for j, mv in enumerate(o):
        m = chess.Move.from_uci(mv)
        pc = b.piece_at(m.from_square)
        types.append(NAMES[pc.piece_type])
        if j == 0:
            idx0 = pc.piece_type
        if pc.piece_type == chess.PAWN:
            cap = b.is_capture(m)
            dbl = abs(m.to_square - m.from_square) == 16
            seq.append('c' if cap else ('d' if dbl else 's'))
    prio = []
    for tt in types:
        if tt not in prio:
            prio.append(tt)
    order = {'s': 0, 'd': 1, 'c': 2}
    t2 = all(order[a] <= order[bb] for a, bb in zip(seq, seq[1:]))
    # T1 restated: the priority must equal the FIXED order P,N,B,R,Q,K RESTRICTED to the piece types actually
    # present. My first version compared against the literal "PNBRQK", so a position with no knights (observed
    # "PBRQK") counted as a failure — the hypothesis was fine and the TEST was wrong. Same shape as instance 17.
    present = set(types)
    expected = "".join(x for x in "PNBRQK" if x in present)
    t1 = ("".join(prio) == expected)
    t3 = (idx0 == chess.PAWN) if seq else None
    tot += 1
    ok1 += t1
    ok2 += t2
    ok3 += 1 if t3 else 0
    if not (t1 and t2):
        fails.append((n, "T1" if not t1 else "", "T2" if not t2 else ""))
    print("| %d | %d | %s | %s | %s | %s | %s |" % (n, len(o), "".join(prio), "".join(seq),
                                                   "pass" if t1 else "**FAIL**",
                                                   "pass" if t2 else "**FAIL**",
                                                   "pass" if t3 else ("n/a" if t3 is None else "**FAIL**")))
p.stdin.write("quit\n"); p.stdin.flush()
print()
print("HOLDOUT: T1 %d/%d   T2 %d/%d   T3 %d/%d" % (ok1, tot, ok2, tot, ok3, tot))
if fails:
    print("failures:", fails[:6])
