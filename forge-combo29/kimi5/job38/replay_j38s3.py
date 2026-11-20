#!/usr/bin/env python3
"""kimi5 job 38 Step 3: the R replay on the logging copy. Identical protocol to replay_j38.py;
additionally every 'info string Q38/S38/N38/W38 ...' line is written to <tag>.qsnw.log,
prefixed with the search index. PRC lines still go to <tag>.prc.log (the step-2 counters are
still present and must still sum to K2). Any refusal line stops the run.
Usage: replay_j38s3.py <engine> <games.txt> <ngames> <budget> <outdir> <tag> <options_file>
"""
import hashlib
import json
import os
import subprocess
import sys
import time

ENGINE = sys.argv[1]
GAMES = sys.argv[2]
NGAMES = int(sys.argv[3])
BUDGET = int(sys.argv[4])
OUTDIR = sys.argv[5]
TAG = sys.argv[6]
OPTFILE = sys.argv[7]

os.makedirs(OUTDIR, exist_ok=True)
stamp = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
REFUSALS = ("illegal move", "invalid FEN", "unknown option", "invalid value", "ERROR")

jsonl_path = os.path.join(OUTDIR, f"{TAG}.jsonl")
input_log = os.path.join(OUTDIR, f"{TAG}_input.log")
prc_path = os.path.join(OUTDIR, f"{TAG}.prc.log")
qsnw_path = os.path.join(OUTDIR, f"{TAG}.qsnw.log")
for path in (jsonl_path, input_log, prc_path, qsnw_path):
    if os.path.exists(path):
        raise SystemExit(f"REFUSING TO OVERWRITE existing output: {path}")

extra_options = []
with open(OPTFILE) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            name, _, value = line.rpartition(" ")
            extra_options.append((name.strip(), value.strip()))

games = []
with open(GAMES) as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3:
            games.append((parts[1], parts[2].split()))
games = games[:NGAMES]

with open(ENGINE, "rb") as f:
    exe_sha = hashlib.sha256(f.read()).hexdigest()

t0 = stamp()
n_done = 0
counts = {"Q38": 0, "S38": 0, "N38": 0, "W38": 0}
with open(jsonl_path, "w") as out_f, open(input_log, "w") as il, open(prc_path, "w") as prc, open(qsnw_path, "w") as qw:
    for gi, (fen, moves) in enumerate(games, start=1):
        proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)

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
                if any(r in line for r in REFUSALS):
                    raise SystemExit(f"REFUSED game {gi}: {line}")
                if line.split(" ")[0] == token or line.startswith(token + " "):
                    return lines

        send("uci")
        uci_lines = read_until("uciok")
        id_name = next((l for l in uci_lines if l.startswith("id name")), "id name ?")
        send("setoption name Threads value 1")
        send("setoption name Hash value 16")
        for name, value in extra_options:
            send(f"setoption name {name} value {value}")
        send("isready")
        read_until("readyok")
        send("ucinewgame")
        send("isready")
        read_until("readyok")
        for ply in range(60):
            prefix = " ".join(moves[:ply])
            send(f"position fen {fen}" + (f" moves {prefix}" if prefix else ""))
            send(f"go softnodes {BUDGET}")
            out = read_until("bestmove")
            nodes = bm = depth = None
            idx = (gi - 1) * 60 + ply + 1
            for l in out:
                if l.startswith("info depth") and " nodes " in l:
                    parts = l.split()
                    nodes = int(parts[parts.index("nodes") + 1])
                    depth = int(parts[2])
                elif l.startswith("info string PRC "):
                    prc.write(f"{idx} {l}\n")
                elif l.startswith(("info string Q38 ", "info string S38 ", "info string N38 ", "info string W38 ")):
                    counts[l.split()[2]] += 1
                    qw.write(f"{idx} {l}\n")
                elif l.startswith("bestmove"):
                    bm = l.split()[1] if len(l.split()) > 1 else "none"
            if nodes is None or bm is None:
                raise SystemExit(f"missing nodes/bm at game {gi} ply {ply}: {out[-6:]}")
            out_f.write(json.dumps({"index": idx, "game": gi, "ply": ply,
                                    "depth": depth, "nodes": nodes, "bestmove": bm}) + "\n")
            n_done += 1
            if n_done % 300 == 0:
                print(f"{TAG} {n_done} searches done {stamp()}", flush=True)
        send("quit")
        proc.stdin.close()
        proc.wait(timeout=30)

t1 = stamp()
with open(os.path.join(OUTDIR, f"{TAG}.meta"), "w") as m:
    m.write(f"command: {' '.join(sys.argv)}\nexe: {ENGINE}\nexe_sha256: {exe_sha}\n{id_name}\n"
            f"budget: softnodes {BUDGET}\nthreads: 1\nhash: 16\n"
            f"options: {[f'{n}={v}' for n, v in extra_options]}\n"
            f"games: {GAMES} first {NGAMES}\nrecord_counts: {counts}\nstart_utc: {t0}\nend_utc: {t1}\n")
print(f"DONE {TAG} searches={n_done} records={counts} {t0} -> {t1}")
