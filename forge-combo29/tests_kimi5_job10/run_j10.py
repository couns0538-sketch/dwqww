#!/usr/bin/env python3
"""kimi5 job10: fixed-depth searches over a position set, pure stdlib.
Job-8 runner (runner) with three changes: bestmove is recorded per position,
an existing output file STOPS the run (no overwrite). The flag build's one
QSTEPS counter line per search lands in {TAG}_full.txt with all other output.
One engine process per run. ucinewgame + isready before EVERY search.
Every command is mirrored into an input log. After the setoptions are sent, isready
is awaited and all lines are scanned: 'unknown option' or 'invalid value' stops the run.
Nodes come from the engine's last info line with 'nodes'.
A .meta beside every result file carries exe path, sha256, id name, UTC times, command.
Usage: run_j9.py <engine> <positions> <depth> <outdir> <tag> [npos] [threads] [options_file]
"""
import hashlib
import json
import os
import subprocess
import sys
import time

ENGINE = sys.argv[1]
FENS = sys.argv[2]
DEPTH = int(sys.argv[3])
OUTDIR = sys.argv[4]
TAG = sys.argv[5]
NPOS = int(sys.argv[6]) if len(sys.argv) > 6 else 10**9
THREADS = int(sys.argv[7]) if len(sys.argv) > 7 else 1
OPTFILE = sys.argv[8] if len(sys.argv) > 8 else None

os.makedirs(OUTDIR, exist_ok=True)
stamp = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

json_path = os.path.join(OUTDIR, f"{TAG}.json")
input_log = os.path.join(OUTDIR, f"{TAG}_input.log")
for path in (json_path, input_log, os.path.join(OUTDIR, f"{TAG}_full.txt")):
    if os.path.exists(path):
        raise SystemExit(f"REFUSING TO OVERWRITE existing output: {path}")

with open(ENGINE, "rb") as f:
    exe_sha = hashlib.sha256(f.read()).hexdigest()

extra_options = []
if OPTFILE:
    with open(OPTFILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                name, _, value = line.rpartition(" ")
                extra_options.append((name.strip(), value))

proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, bufsize=1)

il = open(input_log, "w")

def send(line):
    il.write(line + "\n")
    il.flush()
    proc.stdin.write(line + "\n")
    proc.stdin.flush()

def read_until(token):
    lines = []
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError(f"engine closed output while waiting for {token}")
        line = line.rstrip("\n")
        lines.append(line)
        if line.split(" ")[0] == token or line.startswith(token + " "):
            return lines

t0 = stamp()
full = open(os.path.join(OUTDIR, f"{TAG}_full.txt"), "w")
send("uci")
uci_lines = read_until("uciok")
id_name = next((l for l in uci_lines if l.startswith("id name")), "id name ?")
refusals = [l for l in uci_lines if "unknown option" in l or "invalid value" in l]
send(f"setoption name Threads value {THREADS}")
send("setoption name Hash value 16")
send("setoption name OwnBook value false")
for name, value in extra_options:
    send(f"setoption name {name} value {value}")
send("isready")
r = read_until("readyok")
refusals += [l for l in r if "unknown option" in l or "invalid value" in l]
if refusals:
    il.close()
    raise SystemExit(f"OPTION REFUSAL: {refusals}")

positions = []
with open(FENS) as f:
    for line in f:
        line = line.strip()
        if line:
            positions.append(line)
positions = positions[:NPOS]

per_pos = []
per_bm = []
for i, fen in enumerate(positions):
    send("ucinewgame")
    send("isready")
    r = read_until("readyok")
    refusals = [l for l in r if "unknown option" in l or "invalid value" in l]
    if refusals:
        il.close()
        raise SystemExit(f"OPTION REFUSAL mid-run: {refusals}")
    send(f"position fen {fen}")
    send(f"go depth {DEPTH}")
    out = read_until("bestmove")
    full.write("\n".join(out) + "\n")
    nodes = None
    bm = None
    for l in out:
        if l.startswith("info depth") and " nodes " in l:
            parts = l.split()
            nodes = int(parts[parts.index("nodes") + 1])
        if l.startswith("bestmove"):
            bm = l.split()[1] if len(l.split()) > 1 else "none"
    if nodes is None or bm is None:
        il.close()
        raise SystemExit(f"no nodes/bestmove line for position {i}: {out[-5:]}")
    per_pos.append(nodes)
    per_bm.append(bm)
    if i < 3 or (i + 1) % 50 == 0:
        print(f"{TAG} pos {i + 1}/{len(positions)} nodes {nodes}", flush=True)

send("quit")
il.close()
full.close()
t1 = stamp()

result = {
    "tag": TAG, "engine": ENGINE, "exe_sha256": exe_sha, "id_name": id_name,
    "depth": DEPTH, "threads": THREADS, "hash": 16, "ownbook": False, "fens": FENS,
    "options_file": OPTFILE, "extra_options": [f"{n}={v}" for n, v in extra_options],
    "n_positions": len(positions), "nodes_sum": sum(per_pos), "nodes_first3": per_pos[:3],
    "per_position": per_pos, "bestmove": per_bm, "start_utc": t0, "end_utc": t1,
}
with open(json_path, "w") as f:
    json.dump(result, f)
with open(json_path + ".meta", "w") as f:
    f.write(f"command: {' '.join(sys.argv)}\nexe: {ENGINE}\nexe_sha256: {exe_sha}\n"
            f"{id_name}\ndepth: {DEPTH}\nthreads: {THREADS}\nhash: 16\nownbook: false\n"
            f"options: {result['extra_options']}\n"
            f"start_utc: {t0}\nend_utc: {t1}\nnodes_sum: {result['nodes_sum']}\n")
with open(input_log + ".meta", "w") as f:
    f.write(f"command: {' '.join(sys.argv)}\nexe: {ENGINE}\nexe_sha256: {exe_sha}\n"
            f"start_utc: {t0}\nend_utc: {t1}\n")
print(f"DONE {TAG} n={len(positions)} sum={sum(per_pos)} first3={per_pos[:3]}")
