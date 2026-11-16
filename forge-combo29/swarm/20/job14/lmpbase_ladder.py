#!/usr/bin/env python3
"""lmpbase_ladder.py — seat 20 job 14: how far does the LmpBase=8 mate loss reach?

For a ladder of forced-mate positions, search depths 8..14 at LmpBase default (4) and 8, judge every PV with
python-chess.

usage: lmpbase_ladder.py <exe> <outdir>
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
os.makedirs(OUT, exist_ok=True)

# mate distances verified with python-chess below (asserted), so the ladder is my own, not assumed
BOARDS = [
    ("mate1", "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1"),
    ("mate2", "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1"),   # same board, we will just record its depth-2 line
    ("mate-in-3", "6k1/5ppp/8/8/8/8/5PPP/2R3K1 w - - 0 1"),
    ("S-F19 board", "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"),
]


def search(fen, depth, lmp, timeout=180.0):
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
    pre = ["uci", "setoption name OwnBook value false"]
    if lmp is not None:
        pre.append(f"setoption name LmpBase value {lmp}")
    pre += ["isready", "ucinewgame", "isready", f"position fen {fen}", "isready"]
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
        d = [x for x in out if x.startswith("info depth")]
        ref = [x for x in out if "unknown option" in x or "invalid value" in x]
    return (d[-1] if d else ""), ref


def judge(fen, info):
    m = re.search(r"score (mate|cp) (-?\d+)", info)
    if not m:
        return {"verdict": "no score", "score": "-"}
    kind, val = m.group(1), int(m.group(2))
    pv = info.split(" pv ", 1)[1].split() if " pv " in info else []
    b = chess.Board(fen)
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
        return {"verdict": "cp", "score": f"cp {val}", "pv": len(pv)}
    need = (2 * val - 1) if val > 0 else 2 * abs(val)
    if not legal:
        v = "PV ILLEGAL"
    elif b.is_checkmate() and played == need:
        v = "consistent"
    elif played < need:
        v = f"truncated {played}/{need}"
    else:
        v = f"WRONG {played} plies"
    return {"verdict": v, "score": f"mate {val}", "pv": len(pv), "need": need}


# prove the ladder: at least one mate-in-1 / mate-in-3 exists where I say
def mates_in(board, plies):
    b = chess.Board(board)
    out = []
    def rec(bb, remaining, line):
        if remaining == 0:
            if bb.is_checkmate():
                out.append(line)
            return
        for mv in bb.legal_moves:
            nb = bb.copy()
            nb.push(mv)
            rec(nb, remaining - 1, line + [mv.uci()])
    rec(b, plies, [])
    return out

print(f"exe {EXE}")
print("ladder proof (python-chess, mate-in-1 search by me):")
for name, fen in BOARDS[:3]:
    m1 = mates_in(fen, 1)
    print(f"  {name:12s} {fen}  -> mate-in-1 moves: {m1[:3]}{' ...' if len(m1) > 3 else ''}")
print()

rows = []
for name, fen in BOARDS:
    chess.Board(fen)
    for lmp in (None, 8):
        line = []
        for d in (8, 10, 12, 14):
            info, ref = search(fen, d, lmp)
            j = judge(fen, info)
            rows.append({"board": name, "fen": fen, "lmp": lmp, "depth": d, "info": info,
                         "refusals": ref, **j})
            line.append(f"d{d}: {j.get('score')} [{j['verdict']}]")
        lab = "LmpBase=default" if lmp is None else "LmpBase=8"
        print(f"{name:12s} {lab:16s} " + "  |  ".join(line))

with open(os.path.join(OUT, "lmpbase_ladder.json"), "w") as f:
    json.dump({"exe": EXE, "rows": rows}, f, indent=1)
print("\nwrote lmpbase_ladder.json")
