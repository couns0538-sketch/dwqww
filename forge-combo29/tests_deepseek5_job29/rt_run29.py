#!/usr/bin/env python3
"""job22 A1: the repaired runner. One diff loop over all five depth classes; stops on any refusal
line; writes the .meta itself in the same process; output goes to job 22's folder."""
import hashlib
import json
import os
import queue
import subprocess
import sys
import time

exe, setfile, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
opts = sys.argv[4:]
tag = os.environ.get("DS5_LABEL") or ("+".join(opts).replace(" ", "+") if opts else "none")
OUTDIR = "/agent/repos/dwqww/forge-combo29/tests_deepseek5_job29"
os.makedirs(OUTDIR, exist_ok=True)
UTC0 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
_pred = os.path.join(OUTDIR, "prediction.txt")
if not os.path.exists(_pred):
    print(f"STOP: no prediction.txt in {OUTDIR} - write the prediction before the first run")
    raise SystemExit(1)

p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
_q = queue.Queue()
def _reader():
    try:
        for line in p.stdout:
            _q.put(line)
    except Exception:
        pass
    _q.put(None)
import threading
threading.Thread(target=_reader, daemon=True).start()
def send(s):
    try:
        p.stdin.write(s + "\n"); p.stdin.flush()
    except Exception:
        pass
def rl():
    try:
        return _q.get(timeout=2.0)
    except queue.Empty:
        return ""
    except Exception:
        return ""
send("uci")
refusal = None
idname = ""
_t0 = time.monotonic()
while True:
    l = rl()
    if not l:
        if time.monotonic() - _t0 > 30:
            refusal = "uciok never arrived"
            break
        continue
    l = l.strip()
    if l.startswith("id name "):
        idname = l
    if l.startswith("uciok"):
        break
    if "unknown option" in l or "invalid value" in l:
        refusal = l
all_opts = ["Threads", "1", "Hash", "16", "OwnBook", "false"] + opts
for i in range(0, len(all_opts), 2):
    if refusal:
        break
    send(f"setoption name {all_opts[i]} value {all_opts[i+1]}")
    _t0 = time.monotonic()
    while True:
        l = rl()
        if not l:
            if time.monotonic() - _t0 > 30:
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
    if l.strip().startswith("readyok") or not l:
        break
rows = []
prev = None
total_nodes = 0
t_start = time.monotonic()
CUT = float(os.environ.get("RT_CUT_S", "0"))
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
    stopped = False
    _t0 = time.monotonic()
    while True:
        l = rl()
        if not l:
            if time.monotonic() - _t0 > 30:
                refusal = "no readyok"
                stopped = True
            break
        if l.strip().startswith("readyok"):
            break
        if "unknown option" in l or "invalid value" in l:
            refusal = l
            stopped = True
            break
    if stopped:
        break
    send(f"position fen {fen}")
    send(f"go depth {depth}")
    best = None
    nodes = None
    jc = None
    t0 = time.monotonic()
    while time.monotonic() - t0 < 900:
        l = rl()
        if not l:
            if p.poll() is not None:
                refusal = f"ENGINE EXITED during search at position {i} (rc={p.returncode})"
                break
            if time.monotonic() - t0 > 900:
                break
            continue
        l = l.strip()
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
        if l.startswith("info string RT "):
            jc = l[len("info string RT "):]
        if "unknown option" in l or "invalid value" in l:
            refusal = l
            break
        if l.startswith("info") and " nodes " in l:
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except Exception:
                pass
    if refusal:
        break
    def _zero_like(x):
        if isinstance(x, list):
            return [_zero_like(y) for y in x]
        return 0
    cur = None
    if jc:
        cur = json.loads(jc)
    if prev is None:
        diff = json.loads(json.dumps(cur)) if cur else {}
    else:
        diff = {}
        for k in cur:
            if k in ("n", "r1", "r2"):
                diff[k] = [[[cur[k][s][d][k2] - prev[k][s][d][k2] for k2 in range(4)] for d in range(len(cur[k][s]))] for s in range(len(cur[k]))]
            elif isinstance(cur[k], list):
                def _sub(a, b):
                    if isinstance(a, list):
                        return [_sub(x, y) for x, y in zip(a, b if isinstance(b, list) else [b] * len(a))]
                    return a - b
                diff[k] = _sub(cur[k], prev.get(k, _zero_like(cur[k])))
            else:
                diff[k] = cur[k] - prev.get(k, 0)
    prev = cur
    rows.append(f"{i}|{best}|{nodes}|{json.dumps(diff, separators=(',', ':'))}")
    total_nodes += nodes or 0
try:
    send("quit")
except Exception:
    pass
p.wait(timeout=60)
UTC1 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
if cut_at:
    rows.append(f"CUT at position {cut_at}")
base = f"{OUTDIR}/{tag}_{os.path.basename(setfile)}_d{depth}"
if os.path.exists(base + ".rows"):
    print(f"STOP: output file exists: {base}.rows")
    raise SystemExit(1)
if refusal and "ENGINE EXITED" in refusal:
    rows.append(f"CRASHED: {refusal}")
    open(base + ".rows", "w").write("\n".join(rows) + "\n")
    print(f"CRASHED: {refusal}; rows saved: {len(rows)}")
    raise SystemExit(2)
open(base + ".rows", "w").write("\n".join(rows) + "\n")
sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
open(base + ".meta", "w").write(
    f"exe={exe}\nsha256={sha}\n{idname}\noptions={all_opts}\nutc_start={UTC0}\nutc_end={UTC1}\n")
print(f"SET={setfile} DEPTH={depth} OPTS={tag} SUM={total_nodes} N={len([r for r in rows if '|' in r])}" + (f" CUT_AT={cut_at}" if cut_at else ""))
