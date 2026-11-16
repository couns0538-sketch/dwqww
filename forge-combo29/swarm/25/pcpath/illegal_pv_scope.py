#!/usr/bin/env python3
"""illegal_pv_scope.py EXE : when does an intermediate info line carry an ILLEGAL PV move?

S-C9 established the narrow defect: at `go nodes 20000` on a bare endgame, an intermediate line's PV contains a
move that is not legal at that point in the line. This maps WHEN it fires:
  * across node budgets (1000 .. 250000)
  * across depths (go depth d) - does the depth path ever do it?
  * on several mate-rich endgame boards, to see whether it is board-specific or general
That gives the owner a scope statement instead of one example.
"""
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
BOARDS = [
    "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1",
    "8/8/7Q/8/8/6k1/K7/R7 w - - 0 1",
    "8/8/8/4k3/8/8/8/K1R5 w - - 0 1",
]


def infos(fen, go):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    out = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " pv" in s:
            out.append(s)
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    return out


def illegal_count(fen, lines):
    bad = 0
    first = None
    for line in lines:
        toks = line.split()
        if "pv" not in toks:
            continue
        pv = toks[toks.index("pv") + 1:]
        b = chess.Board(fen)
        for i, mv in enumerate(pv):
            try:
                mm = chess.Move.from_uci(mv)
            except ValueError:
                mm = None
            if mm is None or mm not in b.legal_moves:
                bad += 1
                if first is None:
                    d = re.search(r"depth (\d+)", line)
                    first = (int(d.group(1)) if d else -1, mv, i)
                break
            b.push(mm)
    return bad, first


print(f"### scope of the illegal-PV intermediate line — PC r15/PC20, Threads 1, Hash 16")
print()
for fen in BOARDS:
    print("=" * 78)
    print(f"board: {fen}")
    print(f"{'command':<22} {'info lines':>10} {'lines w/ illegal pv':>20}  first offender (depth, move, ply)")
    for n in (1000, 5000, 10000, 20000, 50000, 250000):
        ls = infos(fen, f"go nodes {n}")
        bad, first = illegal_count(fen, ls)
        print(f"{'go nodes ' + str(n):<22} {len(ls):>10} {bad:>20}  {first if first else '-'}")
    for d in (8, 10, 12, 16):
        ls = infos(fen, f"go depth {d}")
        bad, first = illegal_count(fen, ls)
        print(f"{'go depth ' + str(d):<22} {len(ls):>10} {bad:>20}  {first if first else '-'}")
    print()
