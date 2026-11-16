#!/usr/bin/env python3
"""check_mate_pv.py — seat 20, area 10 job 12: check seat 05's S-F1 / seat 25's S-F1.

Claim: `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` at `go depth 12` reports `score mate -12` with an 18-ply PV that is
not checkmate.

The criterion (committed in PREDICTION.txt before any run):
  mate N > 0 : the PV must end in checkmate in exactly 2N-1 plies
  mate N < 0 : the PV must end in checkmate in exactly 2|N| plies
A PV shorter than that is TRUNCATED; a full-length PV that does not end in mate is WRONG.

usage: check_mate_pv.py <exe> <outdir> [fen]
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
FEN = sys.argv[3] if len(sys.argv) > 3 else "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
os.makedirs(OUT, exist_ok=True)


def search(fen, depth, timeout=300.0):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []
    lock = threading.Lock()

    def rd():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass
    threading.Thread(target=rd, daemon=True).start()
    for c in ("uci", "setoption name OwnBook value false", "isready", "ucinewgame", "isready",
              f"position fen {fen}", "isready"):
        p.stdin.write(c + "\n")
        p.stdin.flush()
    t0 = time.monotonic()
    p.stdin.write(f"go depth {depth}\n")
    p.stdin.flush()
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("bestmove") for x in out):
                break
        time.sleep(0.005)
    wall = time.monotonic() - t0
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=20)
    except Exception:
        p.kill()
    with lock:
        lines = list(out)
    depths = [x for x in lines if x.startswith("info depth")]
    best = [x for x in lines if x.startswith("bestmove")]
    return {"lines": depths, "bestmove": best[-1].split()[1] if best else None, "wall": wall}


def judge(fen, info_line):
    """play the PV out with python-chess and compare with the claimed mate distance"""
    m = re.search(r"score (mate|cp) (-?\d+)", info_line)
    if not m:
        return {"ok": None, "why": "no score on the line"}
    kind, val = m.group(1), int(m.group(2))
    pv = info_line.split(" pv ", 1)[1].split() if " pv " in info_line else []
    b = chess.Board(fen)
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
    res = {"score_kind": kind, "score_value": val, "pv_len": len(pv), "pv_played": played,
           "pv_all_legal": legal, "ends_in_mate": b.is_checkmate(),
           "legal_moves_after": b.legal_moves.count() if not b.is_game_over() else 0,
           "fen_after": b.fen()}
    if kind == "cp":
        res.update({"ok": True, "why": "cp score: no mate distance claimed"})
        return res
    need = (2 * val - 1) if val > 0 else (2 * abs(val))
    res["plies_needed_for_this_mate"] = need
    if not legal:
        res.update({"ok": False, "why": "PV has an ILLEGAL move — a real defect"})
    elif b.is_checkmate() and played == need:
        res.update({"ok": True, "why": f"PV ends in checkmate in exactly {need} plies: consistent"})
    elif b.is_checkmate():
        res.update({"ok": False, "why": f"PV ends in mate but in {played} plies, claimed {need}: WRONG distance"})
    elif played < need:
        res.update({"ok": None, "why": f"PV TRUNCATED at {played} of {need} plies and does not end in mate"})
    else:
        res.update({"ok": False, "why": f"PV is {played} plies (>= {need}) and does NOT end in checkmate: WRONG"})
    return res


rows = []
print(f"exe {EXE}")
print(f"position {FEN}")
print(f"python-chess: valid={chess.Board(FEN).is_valid()}  legal moves={chess.Board(FEN).legal_moves.count()}")
print()
for d in (10, 12, 13, 14, 16, 18):
    r = search(FEN, d)
    last = r["lines"][-1] if r["lines"] else ""
    j = judge(FEN, last) if last else {"ok": None, "why": "no info line"}
    rows.append({"depth": d, "last_info": last, **j})
    print(f"depth {d:2d}: {last[:140]}")
    print(f"          -> pv {j.get('pv_len')} plies, played {j.get('pv_played')} legal, "
          f"ends_in_mate {j.get('ends_in_mate')}, moves after {j.get('legal_moves_after')}, "
          f"need {j.get('plies_needed_for_this_mate')}")
    print(f"          -> {j.get('ok')}: {j.get('why')}")

with open(os.path.join(OUT, "check_mate_pv.json"), "w") as f:
    json.dump({"fen": FEN, "exe": EXE, "rows": rows}, f, indent=1)
print("\nwrote check_mate_pv.json")
