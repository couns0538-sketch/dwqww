#!/usr/bin/env python3
"""kimi5 job 38 Step 0, K7: the twelve cells on the plain build.
One fresh engine process per cell; PC20 options (pc20.opt; the plain build has no
HistoryAge* options, 1024 = the default no-ageing behaviour); ucinewgame + isready
before the search; WAIT for bestmove before quit. Raw output and input log per cell.
Prints one summary line per cell: name bestmove nodes cp.
Usage: k7_j38.py <engine> <outdir> <jobdir>
"""
import hashlib
import os
import subprocess
import sys

ENGINE = sys.argv[1]
OUT = sys.argv[2]
JOB = sys.argv[3]
os.makedirs(OUT, exist_ok=True)

with open(ENGINE, "rb") as f:
    exe_sha = hashlib.sha256(f.read()).hexdigest()

options = []
with open(os.path.join(JOB, "pc20.opt")) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            name, _, value = line.rpartition(" ")
            options.append((name.strip(), value.strip()))

POS = {
    1: "position startpos",
    2: "position fen rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 1",
    3: "position fen 1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    4: "position fen 8/3b4/8/1p1pk2p/7P/P1B1KP1P/1Pr1N3/8 b - - 0 1",
}
ALL = {
    1: "a2a3 b2b3 c2c3 d2d3 e2e3 f2f3 g2g3 h2h3 a2a4 b2b4 c2c4 d2d4 e2e4 f2f4 g2g4 h2h4 b1a3 b1c3 g1f3 g1h3",
    2: "g1e2 c3e2 c3e4 f1e2 d1e2",
    3: "d5d4 e5e4 g7g6 g7g5 f6e4 f6g4 f6d7 f6h7 f6e8 f6g8 f5b1 f5c2 f5d3 f5h3 f5e4 f5g4 f5e6 f5g6 f5d7 f5h7 f5c8 b8b3 b8b4 b8b5 b8b6 b8b7 b8a8 b8c8 b8d8 b8e8 b8f8 b8g8 b8h8 c7b7 c7d7 c7c8 c7d8",
    4: "d5d4 c2c3 e5f5 e5d6 e5e6",
}
TWO = {1: "a2a3 a2a4", 2: "c3e2 c3e4", 3: "b8a8 b8b4", 4: "e5d6 e5e6"}

REFUSALS = ("illegal move", "invalid FEN", "unknown option", "invalid value", "ERROR")

def run_cell(name, pos, go):
    inp = os.path.join(OUT, f"{name}_input.log")
    outp = os.path.join(OUT, f"{name}.txt")
    proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    il = open(inp, "w")
    lines = []

    def send(line):
        il.write(line + "\n")
        il.flush()
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(pred):
        while True:
            line = proc.stdout.readline()
            if not line:
                raise RuntimeError(f"{name}: engine closed output")
            line = line.rstrip("\n")
            lines.append(line)
            if any(r in line for r in REFUSALS):
                raise RuntimeError(f"{name}: REFUSED: {line}")
            if pred(line):
                return

    for n, v in options:
        send(f"setoption name {n} value {v}")
    send("isready")
    read_until(lambda l: l == "readyok")
    send("ucinewgame")
    send("isready")
    read_until(lambda l: l == "readyok")
    send(pos)
    send(go)
    bestmove = None
    last_info = None

    def bm_or_info(l):
        nonlocal bestmove, last_info
        if l.startswith("bestmove"):
            bestmove = l.split()[1]
            return True
        if l.startswith("info depth") and " nodes " in l:
            last_info = l
        return False

    read_until(bm_or_info)
    send("quit")
    proc.wait(timeout=10)
    il.close()
    with open(outp, "w") as f:
        f.write("\n".join(lines) + "\n")
    nodes = cp = "-"
    if last_info:
        parts = last_info.split()
        if "nodes" in parts:
            nodes = parts[parts.index("nodes") + 1]
        if "score" in parts and "cp" in parts:
            cp = parts[parts.index("cp") + 1]
    print(f"{name} {bestmove} {nodes} {cp}", flush=True)

for i in (1, 2, 3, 4):
    run_cell(f"k7_p{i}_plain", POS[i], "go depth 8")
    run_cell(f"k7_p{i}_all", POS[i], f"go depth 8 searchmoves {ALL[i]}")
    run_cell(f"k7_p{i}_two", POS[i], f"go depth 8 searchmoves {TWO[i]}")

print(f"exe sha256 {exe_sha}")
