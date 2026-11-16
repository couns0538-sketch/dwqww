#!/usr/bin/env python3
"""clock99_repetition.py EXE : is the clock-99 shortcut actually a REPETITION test misfiring?

`is_draw` also returns true for `board.is_repetition(root_history_index_)`. If the engine's repetition
bookkeeping is confused by the halfmove clock, a clock-99 root could be classified as a repetition.

Decisive test: the SAME board at the SAME clock, sent two ways —
  (a) as a bare FEN (no history):           `position fen <board> ... 99 1`
  (b) as a move list from the real walk:    `position startpos moves ...` (the 99-ply walk from reach.txt)
If (b) is zero and (a) is not, history matters. If BOTH are zero, the FEN's clock alone triggers it and the
repetition idea is dead.
Also: a board at clock 99 whose position is the START position (definitely not a repetition).
"""
import re
import shlex
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
EXE = sys.argv[1]


def run(position_cmd, depth=8):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name OwnBook value false\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"{position_cmd}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    infos, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            infos.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", infos[-1] if infos else "")
    n = re.search(r"nodes (\d+)", infos[-1] if infos else "")
    toks = infos[-1].split() if infos else []
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return ((m.group(1), int(m.group(2))) if m else None), (int(n.group(1)) if n else 0), best, len(pv)


V1_99 = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1"
walk = None
for line in open("/agent/repos/dwqww/forge-combo29/swarm/25/pcbuild/reach.txt"):
    if line.strip().startswith("exact move list"):
        walk = next(open("/agent/repos/dwqww/forge-combo29/swarm/25/pcbuild/reach.txt")
                    ).strip()
        break
# the walk line follows the "exact move list" line
txt = open("/agent/repos/dwqww/forge-combo29/swarm/25/pcbuild/reach.txt").read().split("\n")
for i, l in enumerate(txt):
    if l.strip().startswith("exact move list"):
        walk = txt[i + 1].strip()
        break

cases = [
    ("(a) bar FEN, clock 99", f"position fen {V1_99}"),
    ("(b) startpos + the 99-ply walk", f"position startpos moves {walk}"),
    ("(c) start position as a FEN at clock 99", "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 99 1"),
    ("(d) same start position at clock 0", "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
]
print(f"{'case':<42} {'score':>12} {'nodes':>7} {'pvlen':>6} best")
for name, cmd in cases:
    sc, nd, bm, pl = run(cmd)
    print(f"{name:<42} {str(sc):>12} {nd:>7} {pl:>6} {bm}")
