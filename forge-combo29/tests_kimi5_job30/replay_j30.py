#!/usr/bin/env python3
"""kimi5 job 30 (verbatim copy of the job 27 v2 replay; the split options ride in the options file, no [keep] arg is passed): warm replay (adds depth + verbatim last info line) of sol's games (job3 games.txt) on a forge build.
Per game: one engine process, PC20 options once, ucinewgame + isready once.
Per ply p of 60: 'position fen <start> moves <first p moves>', then the search.
Recorded per search: nodes (last 'info depth' line), bestmove, HP27 taken/nodes
(the counting build's 'info string HP27 <taken> <nodes>' line).
Refusal scan ('unknown option' / 'invalid value') after every isready; a refusal
stops the run. Output: <tag>.jsonl (one JSON per search), <tag>_input.log,
<tag>.meta (exe, sha256, id name, settings, UTC stamps, command).
Usage: replay_j30.py <engine> <games.txt> <ngames> <soft|hard> <budget> <outdir> <tag> <options_file> [keep]
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
MODE = sys.argv[4]
BUDGET = int(sys.argv[5])
OUTDIR = sys.argv[6]
TAG = sys.argv[7]
OPTFILE = sys.argv[8]
KEEP = sys.argv[9] if len(sys.argv) > 9 else None

os.makedirs(OUTDIR, exist_ok=True)
stamp = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

jsonl_path = os.path.join(OUTDIR, f"{TAG}.jsonl")
input_log = os.path.join(OUTDIR, f"{TAG}_input.log")
for path in (jsonl_path, input_log):
    if os.path.exists(path):
        raise SystemExit(f"REFUSING TO OVERWRITE existing output: {path}")

extra_options = []
with open(OPTFILE) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            name, _, value = line.rpartition(" ")
            extra_options.append((name.strip(), value))
if KEEP is not None:
    extra_options.append(("HistoryAgeKeep", KEEP))

games = []
with open(GAMES) as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3:
            games.append((parts[1], parts[2].split()))
games = games[:NGAMES]

with open(ENGINE, "rb") as f:
    exe_sha = hashlib.sha256(f.read()).hexdigest()

go = f"go softnodes {BUDGET}" if MODE == "soft" else f"go nodes {BUDGET}"
t0 = stamp()
n_done = 0
with open(jsonl_path, "w") as out_f, open(input_log, "w") as il:
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
        r = read_until("readyok")
        refusals = [l for l in uci_lines + r if "unknown option" in l or "invalid value" in l]
        if refusals:
            raise SystemExit(f"OPTION REFUSAL game {gi}: {refusals}")
        send("ucinewgame")
        send("isready")
        read_until("readyok")
        for ply in range(60):
            prefix = " ".join(moves[:ply])
            send(f"position fen {fen}" + (f" moves {prefix}" if prefix else ""))
            send(go)
            out = read_until("bestmove")
            nodes = bm = hp = hp_nodes = depth = info = None
            for l in out:
                if l.startswith("info depth") and " nodes " in l:
                    parts = l.split()
                    nodes = int(parts[parts.index("nodes") + 1])
                    depth = int(parts[2])
                    info = l
                elif l.startswith("info string HP27 "):
                    parts = l.split()
                    hp = int(parts[3])
                    hp_nodes = int(parts[4])
                elif l.startswith("bestmove"):
                    bm = parts[1] if len(parts := l.split()) > 1 else "none"
            if nodes is None or bm is None or hp is None:
                raise SystemExit(f"missing nodes/bm/HP27 at game {gi} ply {ply}: {out[-6:]}")
            out_f.write(json.dumps({"index": (gi - 1) * 60 + ply + 1, "game": gi, "ply": ply,
                                    "depth": depth, "nodes": nodes, "bestmove": bm, "hp27": hp,
                                    "hp27_nodes": hp_nodes, "info": info}) + "\n")
            n_done += 1
            if n_done % 200 == 0:
                print(f"{TAG} {n_done} searches done {stamp()}", flush=True)
        send("quit")
        proc.stdin.close()
        proc.wait(timeout=30)

t1 = stamp()
with open(os.path.join(OUTDIR, f"{TAG}.meta"), "w") as m:
    m.write(f"command: {' '.join(sys.argv)}\nexe: {ENGINE}\nexe_sha256: {exe_sha}\n{id_name}\n"
            f"mode: {MODE}\nbudget: {BUDGET}\nthreads: 1\nhash: 16\n"
            f"options: {[f'{n}={v}' for n, v in extra_options]}\n"
            f"games: {GAMES} first {NGAMES}\nstart_utc: {t0}\nend_utc: {t1}\n")
print(f"DONE {TAG} searches={n_done} {t0} -> {t1}")
