#!/usr/bin/env python3
"""check_19F59.py EXE : does the depth-24 switch to f6f5 happen, and is the mate PV short?

SEAT 19's 19-F59, which I am checking:
  On `6k1/8/5K2/8/6r1/8/8/8 w` (PC r15, PC20, Threads 1, Hash 16):
    go depth 16 -> `f6e7` (cp -490)
    go depth 20 -> `f6e7` (cp -490)
    go depth 24 -> `f6f5` (**mate -15**)
  So the switch happens only at depth 24, which makes position 11 a CALIBRATION CASE rather than a bug.
  ALSO claimed: the depth-24 `mate -15` comes with a 25-ply PV while -15 needs 29 plies, so the SCORE is right
  but the LINE is 4 plies short.

WHY BOTH HALVES ARE CHECKABLE AND WHY I CHECK BOTH:
  * the move switch is a plain observation at three depths;
  * the PV-length claim is arithmetic I can verify by replaying the PV with python-chess - and it is exactly the kind
    of claim my own S-C31 filter rule predicts (a mate score whose PV is short is a converging mate, not a wrong one).

Note 19-C11 records that seat 27 measured DIFFERENT magnitudes on this board and that the two runs agree on the
depth-24 switch existing. So the switch is the robust part; the exact cp/mate numbers may be build-specific. I test
both and say which parts reproduce.
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
EXE = sys.argv[1]
FEN = "6k1/8/5K2/8/6r1/8/8/8 w - - 0 1"


def run(depth):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

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
    p.stdin.write(f"position fen {FEN}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last, best = None, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " pv " in s:
            last = s
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=120)
    except subprocess.TimeoutExpired:
        p.kill()
    score, pv, nodes = "?", [], 0
    if last:
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        score = m.group(0) if m else "?"
        toks = last.split()
        pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
        n = re.search(r"nodes (\d+)", last)
        nodes = int(n.group(1)) if n else 0
    return score, best, pv, nodes


def verify_pv(pv, mate):
    """Replay the PV; is it checkmate, and how many plies does the claim need?"""
    b = chess.Board(FEN)
    for i, mv in enumerate(pv):
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            return None, f"bad uci at {i}"
        if m not in b.legal_moves:
            return None, f"illegal {mv} at {i}"
        b.push(m)
    need = 2 * abs(mate)
    return (b.is_checkmate(), len(pv), need)


print("### 19-F59 check: the depth-24 switch and the mate-PV length")
print(f"fen {FEN} | PC20, Threads 1, Hash 16, fresh process per depth")
print()
print(f"{'depth':>6} {'score':>12} {'bestmove':>9} {'pv plies':>9} {'nodes':>10}  PV check")
for d in (16, 20, 24):
    score, best, pv, nodes = run(d)
    note = ""
    m = re.search(r"score mate (-?\d+)", score)
    if m:
        mate = int(m.group(1))
        r = verify_pv(pv, mate)
        if r and r[0] is not None:
            is_mate, plies, need = r
            note = f"checkmate={is_mate} plies={plies} need={need}" + (" (SHORT)" if plies < need else "")
        else:
            note = str(r)
    print(f"{d:>6} {score:>12} {str(best):>9} {len(pv):>9} {nodes:>10}  {note}")
print()
print("19-F59 claims: d16/d20 -> f6e7 cp -490 ; d24 -> f6f5 mate -15 ; the mate PV is 25 plies where 29 are needed.")
