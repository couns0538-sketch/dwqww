#!/usr/bin/env python3
"""job13: run a position set on the COUNTER build; per search record the JC counter diffs."""
import chess
import queue as _q
import sys
import time

def rdline(e, timeout):
    try:
        return e._q.get(timeout=timeout)
    except _q.Empty:
        return ""
    except Exception:
        return "" 

sys.path.insert(0, "/tmp/glmflash")
from ds5_job12_nodes import Eng

exe, setfile, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
opts = sys.argv[4:]
tag = "+".join(opts).replace(" ", "+") if opts else "none"
e = Eng(exe)
for i in range(0, len(opts), 2):
    e.send(f"setoption name {opts[i]} value {opts[i+1]}")
e.send("isready")
e.expect("readyok", 30)
rows = []
prev = [0] * 25
names = ([f"cand{k}" for k in range(5)] + [f"deeper{k}" for k in range(5)] +
         [f"sfire{k}" for k in range(5)] + [f"sreran{k}" for k in range(5)] +
         [f"sskip{k}" for k in range(5)])
total_nodes = 0
for i, fen in enumerate(open(setfile, encoding="utf-8", errors="replace"), 1):
    fen = fen.strip()
    if not fen:
        continue
    e.newgame()
    e.send(f"position fen {fen}")
    e.send(f"go depth {depth}")
    best = None; nodes = None; jc = None
    t0 = time.monotonic()
    while time.monotonic() - t0 < 60:
        l = rdline(e, 1.0)
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
        if l.startswith("info string JC"):
            jc = l.strip()
        if l.startswith("info") and " nodes " in l:
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except Exception:
                pass
    cur = [0] * 25
    if jc:
        parts = jc.split()
        vals = []
        for label in ("cand", "deeper", "sfire", "sreran", "sskip"):
            k = parts.index(label)
            for j in range(5):
                vals.append(int(parts[k + 1 + j]))
        cur = vals
    diff = [cur[k] - prev[k] for k in range(25)]
    prev = cur
    rows.append(f"{i}|{best}|{nodes}|" + ",".join(str(d) for d in diff))
    total_nodes += nodes or 0
e.send("quit")
import os
os.makedirs("/tmp/glmflash/ds5j13", exist_ok=True)
open(f"/tmp/glmflash/ds5j13/{tag}_{setfile.split('/')[-1]}_d{depth}.cnt", "w").write(
    "position|bestmove|nodes|" + ",".join(names) + "\n" + "\n".join(rows) + "\n")
print(f"SET={setfile} DEPTH={depth} OPTS={tag} SUM={total_nodes} N={len(rows)}")
