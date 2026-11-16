#!/usr/bin/env python3
"""check_mate_pv_s14.py — seat 20, area 10 job 12, the DECISIVE run.

My first run used DEFAULT settings and found every mate PV consistent (mate -7/-6/-4, all ending in checkmate in
exactly the claimed 2|N| plies). So I re-ran with the project's S14 tunables, which is what area 5's jobs use.
This script also judges the PV strictly.

usage: check_mate_pv_s14.py <exe> <outdir>
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


def search(fen, depth, timeout=300.0, s14=True):
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
    if s14:
        pre += [f"setoption name {k} value {v}" for k, v in S14]
    pre += ["isready", "ucinewgame", "isready", f"position fen {fen}", "isready"]
    for c in pre:
        p.stdin.write(c + "\n")
        p.stdin.flush()
    refusals = []
    t0 = time.monotonic()
    p.stdin.write(f"go depth {depth}\n")
    p.stdin.flush()
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("bestmove") for x in out):
                break
        time.sleep(0.003)
    wall = time.monotonic() - t0
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=20)
    except Exception:
        p.kill()
    with lock:
        lines = list(out)
    refusals = [x for x in lines if "unknown option" in x or "invalid value" in x]
    depths = [x for x in lines if x.startswith("info depth")]
    best = [x for x in lines if x.startswith("bestmove")]
    return {"lines": depths, "bestmove": best[-1].split()[1] if best else None,
            "wall": wall, "refusals": refusals}


def judge(fen, info_line):
    m = re.search(r"score (mate|cp) (-?\d+)", info_line)
    if not m:
        return {"ok": None, "why": "no score"}
    kind, val = m.group(1), int(m.group(2))
    pv = info_line.split(" pv ", 1)[1].split() if " pv " in info_line else []
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
    r = {"score": f"{kind} {val}", "pv_len": len(pv), "played": played, "all_legal": legal,
         "ends_in_mate": b.is_checkmate(), "moves_after": 0 if b.is_game_over() else b.legal_moves.count(),
         "fen_after": b.fen()}
    if kind == "cp":
        r.update({"ok": True, "why": "cp score, no mate distance claimed"})
        return r
    need = (2 * val - 1) if val > 0 else 2 * abs(val)
    r["plies_claimed"] = need
    if not legal:
        r.update({"ok": False, "why": "PV contains an ILLEGAL move"})
    elif b.is_checkmate() and played == need:
        r.update({"ok": True, "why": f"checkmate in exactly {need} plies: CONSISTENT"})
    elif b.is_checkmate():
        r.update({"ok": False, "why": f"mate but in {played} plies, claimed {need}"})
    elif played < need:
        r.update({"ok": None, "why": f"TRUNCATED: {played} of {need} plies, not mate"})
    else:
        r.update({"ok": False, "why": f"{played} plies (>= {need}) and NOT mate"})
    return r


rows = []
print(f"exe {EXE}")
print(f"position {FEN}")
print(f"S14 applied: {len(S14)} setoptions")
print()
for s14 in (False, True):
    print(f"===== {'S14 settings' if s14 else 'DEFAULT settings'}")
    for d in (10, 12, 14, 16, 20):
        r = search(FEN, d, s14=s14)
        last = r["lines"][-1] if r["lines"] else ""
        j = judge(FEN, last)
        rows.append({"s14": s14, "depth": d, "last_info": last, "refusals": r["refusals"], **j})
        print(f"  depth {d:2d}  {j.get('score'):9s} pv {j.get('pv_len'):2d} plies  "
              f"played {j.get('played'):2d}/{j.get('plies_claimed')}  mate {str(j.get('ends_in_mate')):5s} "
              f"legal {str(j.get('all_legal')):5s}  -> {j.get('why')}")
        if r["refusals"]:
            print(f"          !! refusals: {r['refusals'][:3]}")

with open(os.path.join(OUT, "check_mate_pv_s14.json"), "w") as f:
    json.dump({"fen": FEN, "exe": EXE, "s14": S14, "rows": rows}, f, indent=1)
print("\nwrote check_mate_pv_s14.json")
