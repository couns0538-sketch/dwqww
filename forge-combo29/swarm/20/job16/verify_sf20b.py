#!/usr/bin/env python3
"""verify_sf20b.py — seat 20 job 16, corrected: the score is `mate -N`, i.e. WHITE (the side to move) IS MATED,
so BLACK must force the mate. My first script tested whether WHITE forces a mate, which was the wrong question.

It also replays the engine's FULL PV (my first script replayed a 140-character truncation of it and got a false
"not checkmate").

usage: verify_sf20b.py <exe> <outdir>
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


def black_forces_mate(board, plies):
    """board: WHITE to move, BLACK is the mater. True iff black mates within `plies` plies against EVERY white
    defence. i.e. for every white move, black has a mate in plies-1 that survives every white reply."""
    if plies < 1:
        return False
    # white to move: black must mate whatever white does
    for wm in board.legal_moves:
        b1 = board.copy()
        b1.push(wm)
        if b1.is_checkmate():          # WHITE mated itself? then black's job is done
            continue
        if not black_mates_in(b1, plies - 1):
            return False
    return True


def black_mates_in(board, plies):
    """board: BLACK to move. True iff black has a move after which mate is forced within plies."""
    if plies < 1:
        return False
    for bm in board.legal_moves:
        b1 = board.copy()
        b1.push(bm)
        if b1.is_checkmate():
            return True
        if plies < 3 or b1.is_game_over():
            continue
        # white replies, then black again
        ok = all(black_mates_in(b2, plies - 2)
                 for b2 in [ _push(b1, wm) for wm in b1.legal_moves ])
        if ok:
            return True
    return False


def _push(board, mv):
    b = board.copy()
    b.push(mv)
    return b


print(f"exe {EXE}")
print(f"position {FEN}   (white to move; `mate -N` means WHITE is mated)")
b0 = chess.Board(FEN)
print(f"python-chess: valid {b0.is_valid()}, white legal moves {b0.legal_moves.count()}")
print()

print("== 1. the engine's FULL mate PV, replayed ply by ply (no truncation this time):")
info = search(12)
pv = info.split(" pv ", 1)[1].split() if " pv " in info else []
print(f"   score: {info.split('score ')[1].split(' nodes')[0]}   pv length: {len(pv)} plies")
b = chess.Board(FEN)
legal_all = True
for i, mv in enumerate(pv, 1):
    try:
        m = chess.Move.from_uci(mv)
    except ValueError:
        legal_all = False
        break
    if m not in b.legal_moves:
        legal_all = False
        break
    b.push(m)
print(f"   all moves legal: {legal_all}; final is checkmate: {b.is_checkmate()}; final FEN {b.fen()}")
print()

print("== 2. does BLACK force a mate? (the question `mate -N` actually asserts)")
rows = {}
for p in (3, 5, 7):
    t0 = time.monotonic()
    r = black_forces_mate(chess.Board(FEN), p)
    rows[p] = r
    print(f"   black forces mate within {p:2d} plies: {str(r):5s}  ({time.monotonic()-t0:.1f}s)")
print()

print("== 3. S-F20 claim, rechecked: default vs LmpBase=8")
eng = []
for opts, lab in (((), "default"), ((("LmpBase", 8),), "LmpBase=8")):
    for d in (10, 12, 14, 16):
        i2 = search(d, opts)
        sc = i2.split("score ")[1].split(" nodes")[0] if "score " in i2 else "?"
        eng.append({"opts": lab, "depth": d, "score": sc})
        print(f"   {lab:10s} depth {d:2d}: {sc}")

with open(os.path.join(OUT, "verify_sf20b.json"), "w") as f:
    json.dump({"fen": FEN, "full_pv": pv, "pv_legal": legal_all, "pv_final_is_mate": b.is_checkmate(),
               "black_forces": rows, "engine": eng}, f, indent=1)
print("\nwrote verify_sf20b.json")
