#!/usr/bin/env python3
"""kimi5 job 32: fixed-limit searches over a position set, pure stdlib.
Job-18 runner (unchanged protocol) plus: the go command is a free string ("depth 12",
"nodes 20000"), and the per-search RAN / RANC / HPMOVMAX lines of the class build are
stored per position in the JSON (as printed before bestmove). One engine process per
run; ucinewgame + isready before EVERY search; every command mirrored into an input
log; an existing output file STOPS the run; 'unknown option' / 'invalid value' stops it.
Usage: runner_j32.py <engine> <positions> <go-string> <outdir> <tag> [npos] [threads] [options_file]
"""
import hashlib
import json
import os
import subprocess
import sys
import time

ENGINE = sys.argv[1]
FENS = sys.argv[2]
GO = sys.argv[3]
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
per_iter = []
per_ran = []
per_ranc = []
per_movmax = []
for i, fen in enumerate(positions):
    send("ucinewgame")
    send("isready")
    r = read_until("readyok")
    refusals = [l for l in r if "unknown option" in l or "invalid value" in l]
    if refusals:
        il.close()
        raise SystemExit(f"OPTION REFUSAL mid-run: {refusals}")
    send(f"position fen {fen}")
    send(f"go {GO}")
    out = read_until("bestmove")
    full.write("\n".join(out) + "\n")
    nodes = None
    bm = None
    last_iter = 0
    ran = {}
    ranc = []
    movmax = None
    for l in out:
        if l.startswith("info depth") and " pv " in l:
            parts = l.split()
            last_iter = max(last_iter, int(parts[2]))
            if " nodes " in l:
                nodes = int(parts[parts.index("nodes") + 1])
        elif l.startswith("info string RAN "):
            _, _, _, cid, reached, fired = l.split()
            ran[cid] = [int(reached), int(fired)]
        elif l.startswith("info string RANC "):
            _, _, _, cls, reached, fired = l.split()
            ranc.append([int(cls), int(reached), int(fired)])
        elif l.startswith("info string HPMOVMAX "):
            movmax = [int(x) for x in l.split()[3:6]]
        elif l.startswith("bestmove"):
            bm = l.split()[1] if len(l.split()) > 1 else "none"
    if nodes is None or bm is None:
        il.close()
        raise SystemExit(f"no nodes/bestmove line for position {i}: {out[-5:]}")
    per_pos.append(nodes)
    per_bm.append(bm)
    per_iter.append(last_iter)
    per_ran.append(ran)
    per_ranc.append(ranc)
    per_movmax.append(movmax)
    if i < 3 or (i + 1) % 50 == 0:
        print(f"{TAG} pos {i + 1}/{len(positions)} nodes {nodes}", flush=True)

send("quit")
il.close()
full.close()
t1 = stamp()

result = {
    "tag": TAG, "engine": ENGINE, "exe_sha256": exe_sha, "id_name": id_name,
    "go": GO, "threads": THREADS, "hash": 16, "ownbook": False, "fens": FENS,
    "options_file": OPTFILE, "extra_options": [f"{n}={v}" for n, v in extra_options],
    "n_positions": len(positions), "nodes_sum": sum(per_pos), "nodes_first3": per_pos[:3],
    "per_position": per_pos, "bestmove": per_bm, "last_iter": per_iter,
    "ran": per_ran, "ranc": per_ranc, "hpmovmax": per_movmax,
    "start_utc": t0, "end_utc": t1,
}
with open(json_path, "w") as f:
    json.dump(result, f)
with open(json_path + ".meta", "w") as f:
    f.write(f"command: {' '.join(sys.argv)}\nexe: {ENGINE}\nexe_sha256: {exe_sha}\n"
            f"{id_name}\ngo: {GO}\nthreads: {THREADS}\nhash: 16\nownbook: false\n"
            f"options: {result['extra_options']}\n"
            f"start_utc: {t0}\nend_utc: {t1}\nnodes_sum: {result['nodes_sum']}\n")
with open(input_log + ".meta", "w") as f:
    f.write(f"command: {' '.join(sys.argv)}\nexe: {ENGINE}\nexe_sha256: {exe_sha}\n"
            f"start_utc: {t0}\nend_utc: {t1}\n")
print(f"DONE {TAG} n={len(positions)} sum={sum(per_pos)} first3={per_pos[:3]}")
