#!/usr/bin/env python3
"""searchmoves_probe.py EXE FEN DEPTH MV... : force the search onto named first moves and report each score.

This separates two different phenomena that look identical in a depth ladder:
  (A) the SAME first move's mate number falling as depth rises  -> the distance shrank
  (B) the depth-N search simply preferring a different first move -> the distance did not shrink, the move changed
If with `searchmoves <move12>` at depth 20 the engine still says the depth-12 number, the ladder's apparent fall was
(B): depth 12 only ever saw the longer mate through that move.
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


def go(exe, fen, depth, moves):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    cmd = f"go depth {depth}" + (f" searchmoves {' '.join(moves)}" if moves else "")
    p.stdin.write(cmd + "\n"); p.stdin.flush()
    lines, best = [], None
    for line in p.stdout:
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill()
    last = lines[-1] if lines else ""
    m = re.search(r"score (cp|mate) (-?\d+)", last)
    t = last.split()
    pv = t[t.index("pv") + 1:] if "pv" in t else []
    return (m.group(0) if m else "?"), best, pv, len(lines)


def main():
    exe, fen, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
    moves = sys.argv[4:]
    score, best, pv, n = go(exe, fen, depth, moves)
    label = f"searchmoves {' '.join(moves)}" if moves else "free search"
    print(f"{label} at depth {depth}: {score}  bestmove {best}  pv_len {len(pv)}  ({n} info lines)")
    print(f"   pv: {' '.join(pv)}")


if __name__ == "__main__":
    main()
