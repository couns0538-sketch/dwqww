#!/usr/bin/env python3
"""pairwise_s14.py — seat 20 job 13, part 2: no SINGLE option reproduces mate -12, so test PAIRS of the three
culprits found by bisect_s14.py: NullMoveBase=5, LmpBase=8, IirDepth=2.

The default answer at depth 12 on the target board is mate -7 with a 14-ply verified PV. The all-S14 answer is
mate -12 with 18 plies (truncated). Question: which pair (or triple) reaches mate -12?

usage: pairwise_s14.py <exe> <outdir>
"""
import itertools
import json
import os
import re
import subprocess
import sys
import threading
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
FEN = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
os.makedirs(OUT, exist_ok=True)
CAND = [("NullMoveBase", 5), ("LmpBase", 8), ("IirDepth", 2)]


def search(opts, depth=12, timeout=180.0):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    out, lock = [], threading.Lock()

    def rd():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass
    threading.Thread(target=rd, daemon=True).start()
    for c in (["uci", "setoption name OwnBook value false"] +
              [f"setoption name {k} value {v}" for k, v in opts] +
              ["isready", "ucinewgame", "isready", f"position fen {FEN}", "isready"]):
        p.stdin.write(c + "\n")
        p.stdin.flush()
    t0 = time.monotonic()
    p.stdin.write(f"go depth {depth}\n")
    p.stdin.flush()
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("bestmove") for x in out):
                break
        time.sleep(0.003)
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=15)
    except Exception:
        p.kill()
    with lock:
        d = [x for x in out if x.startswith("info depth")]
    return d[-1] if d else ""


def judge(info):
    m = re.search(r"score (mate|cp) (-?\d+)", info)
    if not m:
        return {"verdict": "no score", "score": "-", "pv": 0}
    kind, val = m.group(1), int(m.group(2))
    pv = info.split(" pv ", 1)[1].split() if " pv " in info else []
    b = chess.Board(FEN)
    played, legal = 0, True
    for mv in pv:
        try:
            mm = chess.Move.from_uci(mv)
        except ValueError:
            legal = False
            break
        if mm not in b.legal_moves:
            legal = False
            break
        b.push(mm)
        played += 1
    if kind == "cp":
        return {"verdict": "cp score", "score": f"cp {val}", "pv": len(pv), "played": played}
    need = (2 * val - 1) if val > 0 else 2 * abs(val)
    if not legal:
        v = "PV ILLEGAL"
    elif b.is_checkmate() and played == need:
        v = "CONSISTENT"
    elif played < need:
        v = f"TRUNCATED ({played}/{need})"
    else:
        v = f"WRONG ({played} plies, not mate)"
    return {"verdict": v, "score": f"mate {val}", "pv": len(pv), "played": played, "need": need}


rows = []
print(f"exe {EXE}   depth 12   position {FEN}")
print()
print(f"{'options applied':52s} {'score':9s} {'pv':>4s} verdict")
tests = []
for r in (1, 2, 3):
    for combo in itertools.combinations(CAND, r):
        tests.append(list(combo))
tests.append([])
for combo in tests:
    info = search(combo)
    j = judge(info)
    label = " + ".join(f"{k}={v}" for k, v in combo) if combo else "DEFAULT (no options)"
    rows.append({"options": label, "info": info, **j})
    print(f"{label:52s} {j.get('score','-'):9s} {j.get('pv',0):4d} {j['verdict']}")

with open(os.path.join(OUT, "pairwise_s14.json"), "w") as f:
    json.dump({"fen": FEN, "depth": 12, "rows": rows}, f, indent=1)
print("\nwrote pairwise_s14.json")
