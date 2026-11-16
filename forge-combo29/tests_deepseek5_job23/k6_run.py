#!/usr/bin/env python3
"""job23 Step0 S3 + Part C: run a set on kimi5's check build; sum every search's CHECK blocks.
Prints 'blocks summed: N' with N = the number of searches."""
import json
import os
import queue
import subprocess
import sys
import threading
import time

exe, setfile, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
opts = sys.argv[4:]
tag = "+".join(opts).replace(" ", "+") if opts else "none"
OUTDIR = "/agent/repos/dwqww/forge-combo29/tests_deepseek5_job23"
os.makedirs(OUTDIR, exist_ok=True)

p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
q = queue.Queue()
def reader():
    try:
        for line in p.stdout:
            q.put(line)
    except Exception:
        pass
    q.put(None)
threading.Thread(target=reader, daemon=True).start()
def send(s):
    p.stdin.write(s + "\n"); p.stdin.flush()
def rl():
    try:
        return q.get(timeout=2.0)
    except queue.Empty:
        return ""
    except Exception:
        return ""

send("uci")
refusal = None
idname = ""
t0 = time.monotonic()
while True:
    l = rl()
    if not l:
        if time.monotonic() - t0 > 30:
            refusal = "uciok never arrived"
            break
        continue
    l = l.strip()
    if l.startswith("id name "):
        idname = l
    if l.startswith("uciok"):
        break
for i in range(0, len(opts), 2):
    if refusal:
        break
    send(f"setoption name {opts[i]} value {opts[i+1]}")
    t0 = time.monotonic()
    while True:
        l = rl()
        if not l:
            if time.monotonic() - t0 > 30:
                refusal = "no answer to setoption"
            break
        l = l.strip()
        if l.startswith("readyok"):
            break
        if "unknown option" in l or "invalid value" in l:
            refusal = l
            break
if refusal:
    print(f"REFUSED: {refusal}")
    send("quit")
    p.wait(timeout=10)
    raise SystemExit(1)
send("isready")
while True:
    l = rl()
    if not l or l.strip().startswith("readyok"):
        break

totals = {}
blocks = 0
total_nodes = 0
rows = []
for i, fen in enumerate(open(setfile, encoding="utf-8", errors="replace"), 1):
    fen = fen.strip()
    if not fen:
        continue
    send("ucinewgame")
    send("isready")
    while True:
        l = rl()
        if not l or l.strip().startswith("readyok"):
            break
    send(f"position fen {fen}")
    send(f"go depth {depth}")
    best = None
    nodes = None
    block = {}
    t0 = time.monotonic()
    while time.monotonic() - t0 < 900:
        l = rl()
        if not l:
            if time.monotonic() - t0 > 900:
                break
            continue
        l = l.strip()
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
        if l.startswith("info string CHECK ") and " CHECKX " not in l:
            parts = l.split()
            if len(parts) >= 5:
                name = " ".join(parts[3:-2])
                try:
                    block[name] = (int(parts[-2]), int(parts[-1]))
                except ValueError:
                    pass
        if l.startswith("info string CHECK "):
            parts = l.split()
            if len(parts) >= 5:
                name = " ".join(parts[3:-2])
                try:
                    block[name] = (int(parts[-2]), int(parts[-1]))
                except ValueError:
                    pass
        if l.startswith("info") and " nodes " in l:
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except Exception:
                pass
    for name, (made, br) in block.items():
        a = totals.get(name, (0, 0))
        totals[name] = (a[0] + made, a[1] + br)
    blocks += 1
    rows.append(f"{i}|{best}|{nodes}")
    total_nodes += nodes or 0
send("quit")
p.wait(timeout=60)
base = f"{OUTDIR}/{tag}_k6_{os.path.basename(setfile)}_d{depth}"
open(base + ".rows", "w").write("\n".join(rows) + "\n")
with open(base + ".summed.txt", "w") as f:
    f.write(f"blocks summed: {blocks}\n")
    for name in sorted(totals):
        made, br = totals[name]
        f.write(f"CHECK {name} {made} {br}\n")
import hashlib
sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
open(base + ".meta", "w").write(f"exe={exe}\nsha256={sha}\n{idname}\noptions={opts}\nutc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
print(f"SET={setfile} DEPTH={depth} OPTS={tag} SUM={total_nodes} N={blocks} blocks summed: {blocks}")
