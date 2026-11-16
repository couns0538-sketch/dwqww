#!/usr/bin/env python3
"""job17 Part B: run a set on a DB2 build; per search record the JSON counter diffs."""
import json
import os
import subprocess
import sys
import time

exe, setfile, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
opts = sys.argv[4:]
tag = "+".join(opts).replace(" ", "+") if opts else "none"

p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
def send(s):
    p.stdin.write(s + "\n"); p.stdin.flush()
def rl():
    return p.stdout.readline()
send("uci")
while True:
    if rl().startswith("uciok"):
        break
send("setoption name Threads value 1")
send("setoption name Hash value 16")
send("setoption name OwnBook value false")
for i in range(0, len(opts), 2):
    send(f"setoption name {opts[i]} value {opts[i+1]}")
    send("isready")
    while True:
        if rl().startswith("readyok"):
            break
KEYS = ["n", "ba", "rf", "rs", "bb", "n0", "n1"]
rows = []
prev = None
total_nodes = 0
for i, fen in enumerate(open(setfile, encoding="utf-8", errors="replace"), 1):
    fen = fen.strip()
    if not fen:
        continue
    send("ucinewgame")
    send("isready")
    while True:
        if rl().startswith("readyok"):
            break
    send(f"position fen {fen}")
    send(f"go depth {depth}")
    best = None
    nodes = None
    jc = None
    t0 = time.monotonic()
    while time.monotonic() - t0 < 120:
        try:
            l = p.stdout.readline()
        except Exception:
            break
        if not l:
            break
        l = l.strip()
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
        if l.startswith("info string DB2 "):
            jc = l[len("info string DB2 "):]
        if l.startswith("info") and " nodes " in l:
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except Exception:
                pass
    cur = {k: [[0] * 6 for _ in range(5)] for k in KEYS}
    if jc:
        d = json.loads(jc)
        for k in KEYS:
            cur[k] = d[k]
    if prev is None:
        diff = {k: [[cur[k][e][dd] for dd in range(6)] for e in range(5)] for k in KEYS}
    else:
        diff = {k: [[cur[k][e][dd] - prev[k][e][dd] for dd in range(6)] for e in range(5)] for k in KEYS}
    prev = cur
    rows.append(f"{i}|{best}|{nodes}|" + json.dumps(diff, separators=(",", ":")))
    total_nodes += nodes or 0
send("quit")
p.wait(timeout=30)
outdir = "/tmp/glmflash/ds5j17"
os.makedirs(outdir, exist_ok=True)
base = f"{outdir}/{tag}_{os.path.basename(setfile)}_d{depth}"
open(base + ".db2rows", "w").write("\n".join(rows) + "\n")
print(f"SET={setfile} DEPTH={depth} OPTS={tag} SUM={total_nodes} N={len(rows)}")
