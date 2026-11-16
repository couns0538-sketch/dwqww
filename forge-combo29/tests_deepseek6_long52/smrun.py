#!/usr/bin/env python3
"""smrun.py -- rows for the searchmoves variant: per position, position fen X, then
go depth N searchmoves <all legal moves>. One process per position."""
import sys
import chess

exe, setfile, out, depth, opts = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
L1 = "/tmp/ds6_work/forge-combo29/tests_deepseek6_long1"
import importlib.util
spec = importlib.util.spec_from_file_location("rows_mod", L1 + "/rows.py")
# rows.py is a script; replicate its protocol inline instead
import subprocess, threading, queue, time, hashlib

p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
q = queue.Queue()
def rd():
    try:
        for l in p.stdout:
            q.put(l)
    except Exception:
        pass
    q.put(None)
threading.Thread(target=rd, daemon=True).start()
def send(s):
    p.stdin.write(s + "\n"); p.stdin.flush()
def rl(tmo=2.0):
    try:
        return q.get(timeout=tmo)
    except queue.Empty:
        return ""
send("uci")
idname = ""
while True:
    l = rl()
    if not l:
        break
    l = l.strip()
    if l.startswith("id name "):
        idname = l
    if l.startswith("uciok"):
        break
for o in [x for x in opts.split(";") if x.strip()]:
    send(f"setoption name {o.replace('=', ' value ')}")
send("isready")
while True:
    l = rl()
    if not l or l.strip() == "readyok":
        break
rows = []
for i, line in enumerate(open(setfile, encoding="utf-8", errors="replace")):
    fen, moves = line.strip().split(" | ", 1)
    send("ucinewgame"); send("isready")
    while True:
        l = rl()
        if not l or l.strip() == "readyok":
            break
    send(f"position fen {fen}")
    send(f"go depth {depth} searchmoves {moves}")
    best = None; nodes = None
    t0 = time.monotonic()
    while time.monotonic() - t0 < 300:
        l = rl()
        if not l:
            if time.monotonic() - t0 > 300:
                break
            continue
        l = l.strip()
        if l.startswith("bestmove"):
            best = l.split()[1]; break
        if l.startswith("info") and " nodes " in l:
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except Exception:
                pass
    rows.append(f"{i} | {nodes} | {best}")
send("quit"); p.wait(timeout=30)
open(out, "w").write("\n".join(rows) + "\n")
sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
open(out + ".meta", "w").write(f"exe={exe}\nsha256={sha}\n{idname}\n" +
    "".join(f"setoption name {o.replace('=', ' value ')}\n" for o in opts.split(";") if o.strip()) +
    f"depth={depth}\nsearchmoves=all legal moves per position\n")
print(f"rows: {len(rows)} -> {out}")
