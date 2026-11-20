#!/usr/bin/env python3
"""kimi5 job 39: K2 eval runner. One fresh engine process; uci; Threads 1, Hash 16,
OwnBook false; optional extra options; then per row: position fen <FEN>, isready, eval.
Parses the number after 'total' in the eval line.
Refusal scan on EVERY stdout line: 'unknown option', 'invalid value', 'illegal move',
'invalid FEN', 'ERROR' -> write raw files, print the line, exit 2, print NO table.
Files: <tag>_input.log (commands), <tag>_full.txt (raw stdout), <tag>.rows
('<row> <total> <fen>' per line). Existing output STOPS the run (no overwrite).
Usage: eval_k2.py <engine> <outdir> <tag> [--extra 'Name value']...
"""
import hashlib
import os
import subprocess
import sys

REFUSALS = ("unknown option", "invalid value", "illegal move", "invalid FEN", "ERROR")

ROWS = [
    ("Q1", "8/8/8/4k3/8/8/Q7/3K4 w - - 0 1"),
    ("Q2", "8/8/8/4k3/8/3K4/Q7/8 w - - 0 1"),
    ("Q3", "4k3/8/8/8/8/8/Q7/3K4 w - - 0 1"),
    ("Q4", "4k3/8/4K3/8/8/8/Q7/8 w - - 0 1"),
    ("Q5", "7k/8/8/8/8/8/Q7/3K4 w - - 0 1"),
    ("Q6", "7k/8/5K2/8/8/8/Q7/8 w - - 0 1"),
    ("R1", "8/8/8/4k3/8/8/R7/3K4 w - - 0 1"),
    ("R2", "8/8/8/4k3/8/3K4/R7/8 w - - 0 1"),
    ("R3", "4k3/8/8/8/8/8/R7/3K4 w - - 0 1"),
    ("R4", "4k3/8/4K3/8/8/8/R7/8 w - - 0 1"),
    ("R5", "7k/8/8/8/8/8/R7/3K4 w - - 0 1"),
    ("R6", "7k/8/5K2/8/8/8/R7/8 w - - 0 1"),
    ("C1", "7k/8/5K2/8/8/8/8/BN6 w - - 0 1"),
    ("C2", "k7/8/2K5/8/8/8/8/BN6 w - - 0 1"),
    ("C3", "4k3/8/4K3/8/8/8/8/BB6 w - - 0 1"),
    ("L1", "4k3/8/4K3/8/8/8/Q7/8 b - - 0 1"),
    ("S1", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
    ("P1", "4k3/8/4K3/8/8/8/RP6/8 w - - 0 1"),
    ("N1", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("N2", "7k/8/5K2/8/8/8/8/N7 w - - 0 1"),
    ("N3", "7k/8/5K2/8/8/8/8/NN6 w - - 0 1"),
    ("N4", "7k/8/5K2/8/8/8/8/1B6 w - - 0 1"),
    ("N5", "4k3/8/4K3/8/8/8/P7/8 w - - 0 1"),
    ("N6", "4k3/7p/4K3/8/8/8/Q7/8 w - - 0 1"),
    ("N7", "7k/8/5K2/8/8/8/P7/BN6 w - - 0 1"),
]

ENGINE, OUTDIR, TAG = sys.argv[1], sys.argv[2], sys.argv[3]
extras = []
i = 4
while i < len(sys.argv):
    if sys.argv[i] == "--extra":
        extras.append(sys.argv[i + 1])
        i += 2
    else:
        i += 1

os.makedirs(OUTDIR, exist_ok=True)
rows_path = os.path.join(OUTDIR, f"{TAG}.rows")
input_log = os.path.join(OUTDIR, f"{TAG}_input.log")
full_path = os.path.join(OUTDIR, f"{TAG}_full.txt")
for path in (rows_path, input_log, full_path):
    if os.path.exists(path):
        raise SystemExit(f"REFUSING TO OVERWRITE existing output: {path}")

with open(ENGINE, "rb") as f:
    exe_sha = hashlib.sha256(f.read()).hexdigest()

proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, bufsize=1)
il = open(input_log, "w")
full = open(full_path, "w")

refused = []

def send(line):
    il.write(line + "\n")
    proc.stdin.write(line + "\n")
    proc.stdin.flush()

def readline():
    line = proc.stdout.readline()
    if line == "":
        refused.append("ENGINE EXITED")
        return ""
    full.write(line)
    for r in REFUSALS:
        if r in line:
            refused.append(line.rstrip("\n"))
    return line

send("uci")
while True:
    if readline().startswith("uciok") or refused:
        break
for opt in ["Threads 1", "Hash 16", "OwnBook false"] + extras:
    name, _, value = opt.rpartition(" ")
    send(f"setoption name {name} value {value}")

rows = []
for name, fen in ROWS:
    if refused:
        break
    send(f"position fen {fen}")
    send("isready")
    while True:
        line = readline()
        if line.startswith("readyok") or refused:
            break
    if refused:
        break
    send("eval")
    total = None
    while True:
        line = readline()
        if refused:
            break
        if " total " in line:
            total = line.split(" total ")[1].split()[0]
            break
        if line == "":
            break
    rows.append((name, total, fen))

send("quit")
try:
    proc.wait(timeout=10)
except Exception:
    proc.kill()
il.close()
full.close()

if refused:
    print("REFUSED:", refused[0])
    print(f"exe_sha256 {exe_sha}")
    sys.exit(2)

with open(rows_path, "w") as f:
    f.write(f"# exe {ENGINE}\n# exe_sha256 {exe_sha}\n")
    for name, total, fen in rows:
        f.write(f"{name} {total} {fen}\n")
print(f"rows_written {len(rows)} exe_sha256 {exe_sha}")
