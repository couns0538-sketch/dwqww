#!/usr/bin/env python3
"""clock_control.py EXE : same board, only the halfmove clock changes.

Takes the three F_clock99 boards that scored exactly 0, and re-searches each at clocks 0, 50, 90,
98 and 99 at depth 10. If a board scores non-zero at clock 0 but 0 at clock 99, the clock changed the
answer. The job is then to say whether that is correct (every legal line really does hit 100) or a
fault (a capture rescues the game but the engine reports 0 anyway).
"""
import re
import subprocess
import sys

EXE = sys.argv[1]
BOARDS = [
    "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1",
    "r4rk1/1pR4p/p1b1pbp1/5p2/2n2B2/4Q2P/Pq3PP1/1B3RK1 w - - {c} 1",
    "2r3k1/5pb1/4q1np/5Np1/pP1P2P1/4B3/1P1Q1PP1/5RK1 b - - {c} 1",
]


def run(fen, depth=10):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in ["uci", "isready", "setoption name Threads value 1", "isready",
              "ucinewgame", "isready", f"position fen {fen}", "isready", f"go depth {depth}"]:
        p.stdin.write(c + "\n")
        p.stdin.flush()
        if c == "uci":
            for l in p.stdout:
                if l.strip() == "uciok":
                    break
        elif c == "isready":
            for l in p.stdout:
                if l.strip() == "readyok":
                    break
    infos = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            infos.append(line)
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    p.wait(timeout=5)
    return infos[-1] if infos else "(no info)"


for tpl in BOARDS:
    print("=" * 70)
    print("board:", tpl.format(c="0"))
    for clock in (0, 50, 90, 98, 99):
        line = run(tpl.format(c=clock))
        m = re.search(r"score (cp|mate) (-?\d+).*?nodes (\d+)", line)
        if m:
            print(f"  clock {clock:>2}: score {m.group(1)} {m.group(2):>5}  nodes {m.group(3):>6}")
        else:
            print(f"  clock {clock:>2}: {line[:100]}  <-- NO SCORE PARSED")
