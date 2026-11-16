#!/usr/bin/env python3
"""clock99_pc.py EXE LABEL : does the clock-99 draw fire on the PC r15 build under PC20?

File 3 says the PC REPAIRED the drawn-root defect (FORGE_FIX_ROOT_DRAWN), and its known item is
"third occurrence, or halfmove counter 100 OR MORE". My base-tree finding fires at counter **99**, one ply
BEFORE the rule allows. So the question is precise: does the PC build still answer cp 0 at 99?

Tests, Threads 1, Hash 16, PC20:
  - the three proven boards at clocks 97, 98, 99, 100
  - for each, whether a clock-resetting (capture/pawn) move exists
  - a planted control (Rule 1): the same harness on clock 98 must NOT report 0
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
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

EXE, LABEL = sys.argv[1], sys.argv[2]
BOARDS = [
    "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1",
    "r4rk1/1pR4p/p1b1pbp1/5p2/2n2B2/4Q2P/Pq3PP1/1B3RK1 w - - {c} 1",
    "2r3k1/5pb1/4q1np/5Np1/pP1P2P1/4B3/1P1Q1PP1/5RK1 b - - {c} 1",
]


def run(fen, depth=10):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20_EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last, best = None, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    n = re.search(r"nodes (\d+)", last or "")
    return ((m.group(1), int(m.group(2))) if m else None), best, (int(n.group(1)) if n else 0)


print(f"### {LABEL} — clock-99 test, Threads 1, Hash 16, depth 10")
for bi, tpl in enumerate(BOARDS, 1):
    print(f"--- board {bi}")
    for c in (97, 98, 99, 100):
        fen = tpl.format(c=c)
        sc, bm, nd = run(fen)
        b = chess.Board(fen)
        resets = sum(1 for m in b.legal_moves
                     if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN)
        is_draw_by_rule = c >= 100
        flag = ""
        if sc == ("cp", 0) and resets > 0 and not is_draw_by_rule:
            flag = "  <-- WRONG: 0 before the rule applies, with resetting moves available"
        print(f"  clock {c:>3} (rule says draw: {str(is_draw_by_rule):>5}) -> {str(sc):>12} "
              f"nodes {nd:>7} best {bm:>5} resets {resets:>2}{flag}")

# Rule-1 plant: the harness must see a NON-zero score on the same board at clock 98.
sc98, _, _ = run(BOARDS[0].format(c=98))
print()
print(f"PLANT: clock 98 on board 1 -> {sc98}")
print("PASS: harness can see a non-zero score" if sc98 and sc98[1] != 0
      else "FAIL: harness reports 0 where it should not — results not shown")
