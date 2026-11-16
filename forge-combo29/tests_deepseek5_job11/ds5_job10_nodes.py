#!/usr/bin/env python3
"""Node sums over a position set at a fixed depth with optional switch(es). One raw row per search.
Options are sent AFTER the uci handshake and confirmed with isready/readyok."""
import sys, time
sys.path.insert(0, "/tmp/glmflash")
from ds5_job5_meas import Eng

exe, setfile, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
opts = sys.argv[4:]
tag = "+".join(opts) if opts else "none"
e = Eng()
for i in range(0, len(opts), 2):
    e.send(f"setoption name {opts[i]} value {opts[i+1]}")
e.send("isready")
e.expect("readyok", 10)
rows = []
total = 0
for i, fen in enumerate(open(setfile, encoding="utf-8", errors="replace"), 1):
    fen = fen.strip()
    if not fen:
        continue
    e.newgame()
    e.send(f"position fen {fen}")
    e.send(f"go depth {depth}")
    best = None
    nodes = None
    score = None
    t0 = time.monotonic()
    while time.monotonic() - t0 < 30:
        l = e.rl(timeout=1.0)
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
        if l.startswith("info") and " score " in l and " nodes " in l:
            t = l.split()
            try:
                i_s = t.index("score")
                score = t[i_s + 1] + t[i_s + 2]
                nodes = int(t[t.index("nodes") + 1])
            except Exception:
                pass
    rows.append(f"{i}|{best}|{nodes}|{score}")
    total += nodes or 0
e.send("quit")
import os
os.makedirs("/tmp/glmflash/ds5j10", exist_ok=True)
open(f"/tmp/glmflash/ds5j10/{tag.replace(' ', '_').replace('=','_')}_{os.path.basename(setfile)}_d{depth}.rows",
     "w").write("\n".join(rows) + "\n")
print(f"SET={setfile} DEPTH={depth} OPTS={tag} SUM={total} N={len(rows)}")
