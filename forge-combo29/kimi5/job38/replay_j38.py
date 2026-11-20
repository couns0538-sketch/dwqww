#!/usr/bin/env python3
"""kimi5 job 38: the job 27 replay (sol's first 20 games, 1,200 searches) on the plain or
the counting build. Same protocol as replay_j34.py: per game one process, Threads 1 + Hash 16 +
the options file once, ucinewgame + isready once per game; per ply of 60:
'position fen <start> moves <first p moves>', then go softnodes <budget>; WAIT for bestmove.
Every 'info string PRC ...' line is written to <tag>.prc.log, prefixed with the search index
((game-1)*60 + ply + 1). Any refusal line stops the run.
Output: <tag>.jsonl (index game ply depth nodes bestmove), <tag>_input.log, <tag>.prc.log, <tag>.meta
Usage: replay_j38.py <engine> <games.txt> <ngames> <budget> <outdir> <tag> <options_file>
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
for path in (jsonl_path, input_log, prc_path):
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
n_prc = 0
with open(jsonl_path, "w") as out_f, open(input_log, "w") as il, open(prc_path, "w") as prc:
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
            prc_fields = None
            idx = (gi - 1) * 60 + ply + 1
            for l in out:
                if l.startswith("info depth") and " nodes " in l:
                    parts = l.split()
                    nodes = int(parts[parts.index("nodes") + 1])
                    depth = int(parts[2])
                elif l.startswith("info string PRC "):
                    prc_fields = l.split()[3:]
                    prc.write(f"{idx} {l}\n")
                    n_prc += 1
                elif l.startswith("bestmove"):
                    bm = l.split()[1] if len(l.split()) > 1 else "none"
            if nodes is None or bm is None:
                raise SystemExit(f"missing nodes/bm at game {gi} ply {ply}: {out[-6:]}")
            if prc_fields is not None and len(prc_fields) != 36:
                raise SystemExit(f"bad PRC field count at game {gi} ply {ply}: {len(prc_fields)}")
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
            f"games: {GAMES} first {NGAMES}\nPRC_lines: {n_prc}\nstart_utc: {t0}\nend_utc: {t1}\n")
print(f"DONE {TAG} searches={n_done} PRC={n_prc} {t0} -> {t1}")
