#!/usr/bin/env python3
# O2 driver: 2000 positions, B1 preset, depth 9. Mode A: ucinewgame before each
# position. Mode B: one process, no ucinewgame between positions.
# Usage: run_o2.py <binary> <epdfile> <n> <mode A|B> <rawout> <summaryout>
import subprocess, sys

binary, epdfile, n, mode, rawout, sumout = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
fens = [l.strip() for l in open(epdfile) if l.strip()][:n]
p = subprocess.Popen([binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

def send(s):
    p.stdin.write(s + "\n"); p.stdin.flush()

def read_until_bestmove():
    lines = []
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError("engine closed stdout")
        line = line.strip()
        lines.append(line)
        if line.startswith("bestmove"):
            return lines

send("setoption name BundlePreset value B1")
raw = open(rawout, "w")
summ = open(sumout, "w")
for i, fen in enumerate(fens):
    if mode == "A":
        send("ucinewgame")
    send(f"position fen {fen}")
    send("go depth 9")
    lines = read_until_bestmove()
    for l in lines:
        raw.write(f"[{i}] {l}\n")
    best = [l for l in lines if l.startswith("bestmove")][-1].split()[1]
    infos = [l for l in lines if " depth 9 " in l and " score " in l and " nodes " in l]
    last = infos[-1] if infos else ""
    score = "?"
    nodes = "?"
    if last:
        tok = last.split()
        j = tok.index("score")
        score = f"{tok[j+1]} {tok[j+2]}"
        nodes = tok[tok.index("nodes") + 1]
    summ.write(f"{i} {best} {score} {nodes}\n")
send("quit")
p.wait(timeout=30)
raw.close(); summ.close()
print("O2_DONE", binary, mode)
