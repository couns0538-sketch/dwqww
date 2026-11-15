#!/usr/bin/env python3
"""P2 identity driver: fixed-depth searches over EPD positions, one process.

usage: identity_run.py <engine> <epd> <count> <outfile>
Per position: ucinewgame, position fen <FEN>, go depth 9.
One output line: <score>|<nodes>|<bestmove>   (score in cp from the engine's
own last info line, mate scores as written by the engine).
"""
import subprocess
import sys
import re

engine, epd, count, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
extra = sys.argv[5].split(";") if len(sys.argv) > 5 and sys.argv[5] else []

fens = []
with open(epd) as f:
    for i, line in enumerate(f):
        if i >= count:
            break
        fens.append(line.strip())

p = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
for cmd in extra:
    p.stdin.write(cmd + "\n")
info_re = re.compile(r"score (cp|mate) (-?\d+).*?nodes (\d+)")
best_re = re.compile(r"bestmove (\S+)")

with open(out, "w") as w:
    for fen in fens:
        p.stdin.write("ucinewgame\nisready\n")
        while True:
            line = p.stdout.readline()
            if line.startswith("readyok"):
                break
        p.stdin.write(f"position fen {fen}\ngo depth 9\n")
        score = nodes = None
        best = None
        while True:
            line = p.stdout.readline()
            m = info_re.search(line)
            if m:
                score = f"{m.group(1)}{m.group(2)}"
                nodes = m.group(3)
            b = best_re.search(line)
            if b:
                best = b.group(1)
                break
        w.write(f"{score}|{nodes}|{best}\n")
        w.flush()
p.stdin.write("quit\n")
p.stdin.close()
p.wait()
