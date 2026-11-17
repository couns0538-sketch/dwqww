#!/usr/bin/env python3
"""choice_trace.py EXE FEN MAXDEPTH [MPV] : free search at each depth 1..MAXDEPTH, fresh process each time.

Reports bestmove + score per depth, so a change in the reported mate number can be attributed to a change in the
CHOSEN MOVE rather than to the distance of any one move shrinking. With MPV>1 it also asks the engine to rank the
top moves at a single depth, which shows whether the shorter mate was reachable at that depth at all.
"""
import json
import re
import shlex
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def search(exe, fen, depth, mpv):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    if mpv > 1:
        p.stdin.write(f"setoption name MultiPV value {mpv}\n")
    for n, v in S14:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
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
    return lines, best


def parse(lines):
    """Last line per multipv index."""
    by = {}
    for l in lines:
        t = l.split()
        m = re.search(r"score (cp|mate) (-?\d+)", l)
        idx = 1
        if "multipv" in t:
            idx = int(t[t.index("multipv") + 1])
        pv = t[t.index("pv") + 1:] if "pv" in t else []
        by[idx] = {"score": f"{m.group(1)} {m.group(2)}" if m else "?",
                   "first": pv[0] if pv else None, "pv_len": len(pv), "pv": pv}
    return by


def main():
    exe, fen, maxd = sys.argv[1], sys.argv[2], int(sys.argv[3])
    mpv = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    for d in range(1, maxd + 1):
        lines, best = search(exe, fen, d, mpv)
        by = parse(lines)
        row = {"depth": d, "bestmove": best, "lines": by}
        print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
