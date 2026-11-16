#!/usr/bin/env python3
"""job25 part B: run a set on the LmrCalib build; capture every LMR info line per search into the rows."""
import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
import time

exe, setfile, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
opts = sys.argv[4:]
tag = os.environ.get("DS5_LABEL") or ("+".join(opts).replace(" ", "+") if opts else "none")
OUTDIR = "/agent/repos/dwqww/forge-combo29/tests_deepseek5_job27"
os.makedirs(OUTDIR, exist_ok=True)
UTC0 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

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
    try:
        p.stdin.write(s + "\n"); p.stdin.flush()
    except Exception:
        pass
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
all_opts = ["Threads", "1", "Hash", "16", "OwnBook", "false"] + opts
for i in range(0, len(all_opts), 2):
    if refusal:
        break
    send(f"setoption name {all_opts[i]} value {all_opts[i+1]}")
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
rows = []
total_nodes = 0
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
    lmr = []
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
        if l.startswith("info string LMR"):
            lmr.append(l)
        if l.startswith("info") and " nodes " in l:
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except Exception:
                pass
    rows.append(f"{i}|{best}|{nodes}|" + " || ".join(lmr))
    total_nodes += nodes or 0
send("quit")
dump = []
t0 = time.monotonic()
while time.monotonic() - t0 < 30:
    l = rl()
    if not l:
        break
    l = l.strip()
    if l.startswith("info string LMR"):
        dump.append(l)
p.wait(timeout=60)
UTC1 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
base = f"{OUTDIR}/{tag}_calib_{os.path.basename(setfile)}_d{depth}"
if os.path.exists(base + ".rows"):
    print(f"STOP: output file exists: {base}.rows")
    raise SystemExit(1)
open(base + ".rows", "w").write("\n".join(rows) + "\n")
open(base + ".dump.txt", "w").write("\n".join(dump) + "\n")
sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
open(base + ".meta", "w").write(f"exe={exe}\nsha256={sha}\n{idname}\noptions={all_opts}\nutc_start={UTC0}\nutc_end={UTC1}\n")
print(f"SET={setfile} DEPTH={depth} OPTS={tag} SUM={total_nodes} N={len(rows)}")
