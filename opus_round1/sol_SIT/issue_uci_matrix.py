"""Issue #7 UCI matrix on one engine: position fen 8/7k/8/8/8/8/8/K1R5 w - - 0 1 moves <6-ply history>,
go depth D searchmoves a2a1, IntendedThreefold off/on, a fresh process per search (Threads 1, Hash 32, OwnBook false).
usage: python -I -B issue_uci_matrix.py <engine.exe>"""
import re
import subprocess
import sys

EXE = sys.argv[1]
HISTORIES = {"positive": "a1a2 h7h8 a2a1 h8h7 a1a2 h7h8", "control": "a1b1 h7h8 b1b2 h8h7 b2a2 h7h8"}


def score(option, moves, depth):
    flags = getattr(subprocess, "IDLE_PRIORITY_CLASS", 0)
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
                         creationflags=flags)
    for command in ("uci", "setoption name OwnBook value false", "setoption name IntendedThreefold value " + option,
                    "position fen 8/7k/8/8/8/8/8/K1R5 w - - 0 1 moves " + moves, "go depth %d searchmoves a2a1" % depth):
        p.stdin.write(command + "\n")
    p.stdin.flush()
    last = ""
    for line in p.stdout:
        if line.startswith("info depth %d " % depth):
            last = line
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    p.wait(timeout=30)
    return re.search(r"score (cp|mate) (-?\d+)", last).group(0)


print("# issue #7 UCI matrix: position fen 8/7k/8/8/8/8/8/K1R5 w - - 0 1 moves <6-ply history>; go depth D searchmoves "
      "a2a1; fresh process per search, Threads 1, Hash 32 (default), OwnBook false; exe " + EXE)
for name, moves in HISTORIES.items():
    for option in ("false", "true"):
        for depth in (1, 2, 4, 6):
            print("%s IntendedThreefold=%s depth %d: %s" % (name, option, depth, score(option, moves, depth)), flush=True)
