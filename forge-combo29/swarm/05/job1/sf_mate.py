#!/usr/bin/env python3
"""sf_mate.py FEN [MOVETIME_MS] -- ask Stockfish 16 (Ubuntu package, official) for its mate score via
`go mate <N>` (search until mate found) with a movetime cap, and print its score + bestmove.
Used only as an outside authority on what the true mate distance is.
"""
import re
import subprocess
import sys

SF = "/usr/games/stockfish"
fen = sys.argv[1]
movetime = int(sys.argv[2]) if len(sys.argv) > 2 else 3000

script = ["uci", "setoption name Threads value 1", "setoption name Hash value 64", "isready",
          "ucinewgame", "isready", f"position fen {fen}", "isready",
          f"go movetime {movetime}", "quit"]
p = subprocess.run([SF], input="\n".join(script) + "\n", capture_output=True, text=True, timeout=600)
lines = p.stdout.splitlines()
pvlines = [l for l in lines if re.search(r"\binfo\b.*\bscore\b", l)]
bestmoves = [l for l in lines if l.startswith("bestmove")]
print(f"fen: {fen}")
print(f"stockfish: {next((l for l in lines if l.startswith('id name')), '?')}")
print(f"movetime_ms: {movetime}")
if pvlines:
    last = pvlines[-1]
    print("last info line: " + last)
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    print(f"score: {m.group(1)} {m.group(2)}" if m else "score: (none)")
    if m and m.group(1) == "mate":
        n = int(m.group(2))
        print(f"stockfish says: mate in {2*n-1 if n>0 else 2*(-n)} plies")
print("bestmove: " + (bestmoves[0] if bestmoves else "(none)"))
