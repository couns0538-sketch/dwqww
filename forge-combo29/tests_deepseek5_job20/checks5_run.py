#!/usr/bin/env python3
"""job20 Part A: run a set on the Checks5 build; record the CHECK totals and every CHECKBREACH."""
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
def rl():
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
total_nodes = 0
last_checks = {}
breaches = {}
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
    checks = {}
    t0 = time.monotonic()
    while time.monotonic() - t0 < 300:
        l = rl()
        if not l:
            if time.monotonic() - t0 > 300:
                break
            continue
        l = l.strip()
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
        if l.startswith("info string CHECK "):
            rest = l[len("info string CHECK "):].split()
            if len(rest) >= 3:
                checks["|".join(rest[:-2])] = (int(rest[-2]), int(rest[-1]))
        if l.startswith("info string CHECKBREACH "):
            breaches.setdefault(l[len("info string CHECKBREACH "):], i)
        if l.startswith("info") and " nodes " in l:
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except Exception:
                pass
    rows.append(f"{i}|{best}|{nodes}")
    total_nodes += nodes or 0
    last_checks = checks
send("quit")
p.wait(timeout=60)
outdir = "/tmp/glmflash/ds5j20"
os.makedirs(outdir, exist_ok=True)
base = f"{outdir}/{tag}_{os.path.basename(setfile)}_d{depth}"
open(base + ".rows", "w").write("\n".join(rows) + "\n")
with open(base + ".checks.txt", "w") as f:
    for k in sorted(last_checks):
        made, br = last_checks[k]
        f.write(f"CHECK {k} {made} {br}\n")
    for text, pos in breaches.items():
        f.write(f"CHECKBREACH (first at position {pos}) {text}\n")
print(f"SET={setfile} DEPTH={depth} OPTS={tag} SUM={total_nodes} N={len(rows)} SITES={len(last_checks)} BREACHLINES={len(breaches)}")
