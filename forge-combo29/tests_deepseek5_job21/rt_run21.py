#!/usr/bin/env python3
"""job19: run a set on the RegretTop build; per search record the RT counter diffs."""
import json
import os
import queue
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
def rl(timeout=1.0):
    try:
        return p.stdout.readline()
    except Exception:
        return ""
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
rows = []
prev = None
total_nodes = 0
t_start = time.monotonic()
CUT = float(os.environ.get("RT_CUT_S", "0"))  # 0 = no cut
cut_at = None
for i, fen in enumerate(open(setfile, encoding="utf-8", errors="replace"), 1):
    fen = fen.strip()
    if not fen:
        continue
    if CUT and time.monotonic() - t_start > CUT:
        cut_at = i
        break
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
    while time.monotonic() - t0 < 900:
        l = rl(1.0)
        if not l:
            if time.monotonic() - t0 > 900:
                break
            continue
        l = l.strip()
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
        if l.startswith("info string RT "):
            jc = l[len("info string RT "):]
        if l.startswith("info") and " nodes " in l:
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except Exception:
                pass
    cur = {"n": None, "r1": None, "r2": None, "pn": 0}
    if jc:
        cur = json.loads(jc)
    if prev is None:
        diff = dict(cur)
    else:
        diff = {}
        for k in cur:
            if k in ("n", "r1", "r2"):
                diff[k] = [[[cur[k][s][d][k2] - prev[k][s][d][k2] for k2 in range(4)] for d in range(5)] for s in range(5)]
            elif isinstance(cur[k], list):
                diff[k] = [cur[k][i] - prev.get(k, [0]*len(cur[k]))[i] for i in range(len(cur[k]))]
            else:
                diff[k] = cur[k] - prev.get(k, 0)
        for k in ("n", "r1", "r2"):
            diff[k] = [[[cur[k][s][d][k2] - prev[k][s][d][k2] for k2 in range(4)] for d in range(4)] for s in range(5)]
    prev = cur
    rows.append(f"{i}|{best}|{nodes}|{json.dumps(diff, separators=(',', ':'))}")
    total_nodes += nodes or 0
send("quit")
p.wait(timeout=60)
outdir = "/tmp/glmflash/ds5j19"
os.makedirs(outdir, exist_ok=True)
base = f"{outdir}/{tag}_{os.path.basename(setfile)}_d{depth}"
open(base + ".rtrows", "w").write("\n".join(rows) + "\n")
print(f"SET={setfile} DEPTH={depth} OPTS={tag} SUM={total_nodes} N={len([r for r in rows if '|' in r])}" + (f" CUT_AT={cut_at}" if cut_at else ""))
