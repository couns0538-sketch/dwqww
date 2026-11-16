#!/usr/bin/env python3
"""score_wrong_state.py EXE : is the wrong mate score (S-F1 / S-F8) a state artefact?

For each of the two proven wrong scores, search at depth 12 in four ways:
  1. FRESH process, nothing before the search (the cleanest possible measurement)
  2. fresh process, with `go depth 24` BEFORE it, to confirm the deep answer again
  3. fresh process, the deep search FIRST then depth 12 (does the deep search's TT poison the shallow one?)
  4. same process: depth 12, ucinewgame, depth 12 again (does ucinewgame restore the wrong answer?)
If (1) already gives the wrong score, it is not caused by prior state.
"""
import re
import shlex
import subprocess
import sys

CASES = {
    "S-F1  mate -12 (true -4)": "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1",
    "S-F8  mate  -9 (true -7)": "2b2knr/2qpp3/1r2n1pb/p4pP1/4PPQp/3P3P/PP1KB3/1qB3NR w - - 0 22",
}
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def session(exe, fen, plan):
    """plan: list of (label, depth). Returns list of (label, mate_or_cp, pv_len)."""
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 64\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("setoption name OwnBook value false\nisready\n"); p.stdin.flush(); until("readyok")

    out = []
    for label, depth, do_newgame in plan:
        if do_newgame:
            p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
        p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
        p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
        last = None
        while True:
            line = p.stdout.readline()
            if not line:
                break
            line = line.rstrip("\n")
            if line.startswith("info depth") and " pv " in line:
                last = line
            if line.startswith("bestmove"):
                break
        if last is None:
            out.append((label, "NO-SCORE", 0))
            continue
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        toks = last.split()
        pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
        out.append((label, f"{m.group(1)} {m.group(2)}" if m else "NO-SCORE", len(pv)))
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return out


exe = sys.argv[1]
for name, fen in CASES.items():
    print("=" * 74)
    print(name, "|", fen)

    print("  1. FRESH process, depth 12 only (no ucinewgame, nothing before):")
    for label, sc, plies in session(exe, fen, [("d12", 12, False)]):
        print(f"       {sc:>10}  pv {plies:>2} plies")

    print("  2. fresh process: depth 12, ucinewgame, depth 12:")
    for label, sc, plies in session(exe, fen, [("a", 12, True), ("b", 12, True)]):
        print(f"       {sc:>10}  pv {plies:>2} plies")

    print("  3. fresh process: depth 24 FIRST, then ucinewgame, then depth 12:")
    for label, sc, plies in session(exe, fen, [("d24", 24, True), ("d12", 12, True)]):
        print(f"       {sc:>10}  pv {plies:>2} plies")
