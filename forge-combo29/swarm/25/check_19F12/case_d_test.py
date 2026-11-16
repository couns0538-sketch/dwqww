#!/usr/bin/env python3
"""case_d_test.py EXE : the pattern my run_pv.py actually uses.

Keeps stdin OPEN, reads stdout until `bestmove` arrives, only then sends quit.
If this gives a real search (nodes > 0, info lines present, sane bestmove) then my recorded
results are not the pipelined failure mode of 19-F12. It also records EOF-instead-of-bestmove
and fabricated-move cases so a failure cannot pass silently.
"""
import subprocess
import sys

EXE = sys.argv[1]


def case(name, close_stdin_early):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for cmd in ["uci", "isready", "ucinewgame", "isready"]:
        p.stdin.write(cmd + "\n")
        p.stdin.flush()
        if cmd == "uci":
            for line in p.stdout:
                if line.strip() == "uciok":
                    break
        else:
            for line in p.stdout:
                if line.strip() == "readyok":
                    break

    p.stdin.write("position startpos\n")
    p.stdin.write("go depth 12\n")
    p.stdin.flush()
    if close_stdin_early:
        p.stdin.close()

    infos = []
    best = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            infos.append(line)
        if line.startswith("bestmove"):
            best = line
            break
    if not close_stdin_early:
        p.stdin.write("quit\n")
        p.stdin.flush()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()

    last = infos[-1] if infos else "(none)"
    print(f"{name}: info_lines={len(infos)} bestmove={best!r}")
    print(f"   last info: {last[:120]}")


print("case D: stdin kept OPEN, read until bestmove, then quit  <-- my harness pattern")
case("D", False)
print()
print("case E: stdin CLOSED right after go (the 19-F12 failure mode, for contrast)")
case("E", True)
