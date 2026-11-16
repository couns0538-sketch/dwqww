#!/usr/bin/env python3
"""job18 Part B: run a set on the Part-C build (DB + SB counters) and diff BOTH per position."""
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

DB_K = ["n", "ba", "rf", "rs", "bb"]
SB_K = ["sbn", "sba", "srf", "srs", "sbb"]
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
    while time.monotonic() - t0 < 180:
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
        if l.startswith("info string DB "):
            jc = l
        if l.startswith("info") and " nodes " in l:
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except Exception:
                pass
    cur = {"db": {k: [0, 0, 0, 0] for k in DB_K}, "sb": {k: [0, 0, 0, 0] for k in SB_K},
           "dbn0": 0, "dbn1": 0, "sbn0": 0, "sbn1": 0}
    if jc:
        parts = jc.split()
        def four(label):
            k = parts.index(label)
            return [int(parts[k + 1 + j]) for j in range(4)]
        cur["db"] = {"n": four("n"), "ba": four("both_above"), "rf": four("refuted"),
                     "rs": four("rescued"), "bb": four("both_below")}
        k = parts.index("nodes0")
        cur["dbn0"] = int(parts[k + 1]); cur["dbn1"] = int(parts[k + 3])
        if "SB" in parts:
            cur["sb"] = {"sbn": [int(parts[parts.index("SB") + 2 + j]) for j in range(4)],
                         "sba": four("sboth_above"), "srf": four("srefuted"),
                         "srs": four("srescued"), "sbb": four("sboth_below")}
            k = parts.index("snodes0")
            cur["sbn0"] = int(parts[k + 1]); cur["sbn1"] = int(parts[k + 3])
    if prev is None:
        diff = json.dumps(cur, separators=(",", ":"))
    else:
        d = {"db": {k: [cur["db"][k][j] - prev["db"][k][j] for j in range(4)] for k in DB_K},
             "sb": {k: [cur["sb"][k][j] - prev["sb"][k][j] for j in range(4)] for k in SB_K},
             "dbn0": cur["dbn0"] - prev["dbn0"], "dbn1": cur["dbn1"] - prev["dbn1"],
             "sbn0": cur["sbn0"] - prev["sbn0"], "sbn1": cur["sbn1"] - prev["sbn1"]}
        diff = json.dumps(d, separators=(",", ":"))
    prev = cur
    rows.append(f"{i}|{best}|{nodes}|{diff}")
    total_nodes += nodes or 0
send("quit")
p.wait(timeout=30)
outdir = "/tmp/glmflash/ds5j18"
os.makedirs(outdir, exist_ok=True)
base = f"{outdir}/{tag}_{os.path.basename(setfile)}_d{depth}"
open(base + ".sbrows", "w").write("\n".join(rows) + "\n")
print(f"SET={setfile} DEPTH={depth} OPTS={tag} SUM={total_nodes} N={len(rows)}")
