#!/usr/bin/env python3
"""verify_sf20.py — seat 20 job 16: does the S-F19/S-F20 board really have a forced mate?

S-F20 says `LmpBase=8` replaces a proven mate with cp on `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`. That claim needs
the mate to be REAL and FORCED. After withdrawing S-F21 for exactly this mistake, I verify before keeping S-F20.

The engine reports mate -N: BLACK is the side that gets mated, white is to move. So the question is:
does WHITE force a mate? python-chess's own `is_checkmate` plus an exhaustive defender-reply enumeration decides it,
using the engine's own PV line as the claim to test.

usage: verify_sf20.py <exe> <outdir>
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
FEN = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"

# the PV the engine printed for mate -7 at default settings, depth 10/12 (job12, job13)
PV = "c2b1 d2d1q b1b2 e4e3 b2a2 d1b3 a2a1 b3a3 a1b1 a3b4 b1a2".split()


def search(depth, opts=(), timeout=180.0):
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
    p.stdin.write(f"go depth {depth}\n")
    p.stdin.flush()
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("bestmove") for x in out):
                break
        time.sleep(0.005)
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=15)
    except Exception:
        p.kill()
    with lock:
        d = [x for x in out if x.startswith("info depth")]
    return d[-1] if d else ""


def forced_mate_within(board, plies):
    """board: WHITE to move. True iff white forces mate within `plies` plies against every defence."""
    if plies < 1:
        return False
    for wm in board.legal_moves:
        b1 = board.copy()
        b1.push(wm)
        if b1.is_checkmate():
            return True
        if plies < 3 or b1.is_game_over():
            continue
        ok = True
        for bm in b1.legal_moves:
            b2 = b1.copy()
            b2.push(bm)
            if b2.is_checkmate():
                ok = False
                break
            if not forced_mate_within(b2, plies - 2):
                ok = False
                break
        if ok:
            return True
    return False


print(f"exe {EXE}")
print(f"position {FEN}")
b0 = chess.Board(FEN)
print(f"python-chess: is_valid {b0.is_valid()}, legal moves {b0.legal_moves.count()}, turn {'white' if b0.turn else 'black'}")
print()

print("== 1. replay the engine's own mate -7 PV (from job12/job13) with python-chess:")
b = chess.Board(FEN)
for mv in PV:
    b.push_uci(mv)
print(f"   {len(PV)} plies played; final position checkmate: {b.is_checkmate()}")
print(f"   final FEN: {b.fen()}")
print()

print("== 2. is the mate FORCED (white to move, mate against every black defence)?")
for p in (1, 3, 7, 9):
    t0 = time.monotonic()
    r = forced_mate_within(chess.Board(FEN), p)
    print(f"   forced mate within {p:2d} plies: {str(r):5s}  ({time.monotonic()-t0:.1f}s)")
print()

print("== 3. the engine, default settings vs LmpBase=8 (the S-F20 claim):")
rows = []
for opts, lab in (((), "default"), ((("LmpBase", 8),), "LmpBase=8")):
    for d in (10, 12, 14, 16):
        info = search(d, opts)
        sc = info.split("score ")[1].split(" nodes")[0] if "score " in info else "?"
        rows.append({"opts": lab, "depth": d, "score": sc, "info": info})
        print(f"   {lab:10s} depth {d:2d}: {sc}")

with open(os.path.join(OUT, "verify_sf20.json"), "w") as f:
    json.dump({"fen": FEN, "pv": PV, "pv_final_is_mate": b.is_checkmate(),
               "forced_1": forced_mate_within(chess.Board(FEN), 1),
               "forced_3": forced_mate_within(chess.Board(FEN), 3),
               "forced_7": forced_mate_within(chess.Board(FEN), 7),
               "forced_9": forced_mate_within(chess.Board(FEN), 9),
               "engine": rows}, f, indent=1)
print("\nwrote verify_sf20.json")
