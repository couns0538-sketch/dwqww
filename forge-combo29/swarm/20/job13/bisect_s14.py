#!/usr/bin/env python3
"""bisect_s14.py — seat 20 job 13: which S14 option causes the mate -12 / 18-ply PV at depth 12?

For each option: apply it ALONE (everything else default), search depth 12 on the target board, and judge the PV
with python-chess. The default answer is mate -7 with a 14-ply verified PV; anything else is attributable to that
one option.

usage: bisect_s14.py <exe> <outdir>
"""
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
S14 = [
    ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
    ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
    ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
    ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
]


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
    pre = ["uci", "setoption name OwnBook value false"] + [f"setoption name {k} value {v}" for k, v in opts] + \
          ["isready", "ucinewgame", "isready", f"position fen {FEN}", "isready"]
    for c in pre:
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
        lines = list(out)
    refusals = [x for x in lines if "unknown option" in x or "invalid value" in x]
    depths = [x for x in lines if x.startswith("info depth")]
    return (depths[-1] if depths else ""), refusals


def judge(info):
    if not info:
        return {"verdict": "no answer"}
    m = re.search(r"score (mate|cp) (-?\d+)", info)
    if not m:
        return {"verdict": "no score"}
    kind, val = m.group(1), int(m.group(2))
    pv = info.split(" pv ", 1)[1].split() if " pv " in info else []
    b = chess.Board(FEN)
    played = 0
    legal = True
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
    return {"verdict": v, "score": f"mate {val}", "pv": len(pv), "played": played, "need": need,
            "ends_in_mate": b.is_checkmate()}


rows = []
print(f"exe {EXE}")
print(f"position {FEN}   (depth 12)")
print()
print(f"{'applied option':30s} {'score':9s} {'pv':>4s} {'verdict'}")
# baseline, twice, to prove determinism
for i in (1, 2):
    info, ref = search([])
    j = judge(info)
    rows.append({"opts": "DEFAULT run %d" % i, "info": info, "refusals": ref, **j})
    print(f"{'DEFAULT run ' + str(i):30s} {j.get('score','-'):9s} {j.get('pv',0):4d} {j['verdict']}")
print()
for k, v in S14:
    info, ref = search([(k, v)])
    j = judge(info)
    rows.append({"opts": f"{k}={v}", "info": info, "refusals": ref, **j})
    print(f"{k + '=' + str(v):30s} {j.get('score','-'):9s} {j.get('pv',0):4d} {j['verdict']}"
          + ("   !! REFUSED" if ref else ""))
print()
print("all 14 together, for reference:")
info, ref = search(S14)
j = judge(info)
rows.append({"opts": "ALL S14", "info": info, "refusals": ref, **j})
print(f"{'ALL S14':30s} {j.get('score','-'):9s} {j.get('pv',0):4d} {j['verdict']}")

with open(os.path.join(OUT, "bisect_s14.json"), "w") as f:
    json.dump({"fen": FEN, "depth": 12, "rows": rows}, f, indent=1)
print("\nwrote bisect_s14.json")
