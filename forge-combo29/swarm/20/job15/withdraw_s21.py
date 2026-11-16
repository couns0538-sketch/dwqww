#!/usr/bin/env python3
"""withdraw_s21.py — seat 20 job 15: is a mate in 3 really invisible at depth 14?

My own S-F21 claimed the engine misses a mate in 3 on `6k1/6pp/8/8/8/8/5PPP/R5K1 w - - 0 1` because python-chess
found 18 "mate-in-3" move triples. This script tests whether a FORCED mate exists at all, which is the only thing
that could make the engine wrong.

Definition used (stated before running): white forces mate within N plies iff there is a white move such that for
EVERY black reply, white can mate within N-2 plies. Counting one white line while black has defences is NOT a
forced mate.

usage: withdraw_s21.py <exe> <outdir>
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
FEN = "6k1/6pp/8/8/8/8/5PPP/R5K1 w - - 0 1"
LINE = ["g1h1", "g8h8", "a1a8"]


def forced_mate_within(board, plies):
    """board: side to move is the MATER (white). True iff mate can be forced within `plies` plies."""
    if plies < 1:
        return False
    for wm in board.legal_moves:
        b1 = board.copy()
        b1.push(wm)
        if b1.is_checkmate():
            return True
        if plies < 3 or b1.is_game_over():
            continue
        all_replies_lose = True
        for bm in b1.legal_moves:
            b2 = b1.copy()
            b2.push(bm)
            if b2.is_checkmate():          # black mates white: this white move fails
                all_replies_lose = False
                break
            if not forced_mate_within(b2, plies - 2):
                all_replies_lose = False
                break
        if all_replies_lose:
            return True
    return False


def search(depth, timeout=180.0):
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
    for c in ("uci", "setoption name OwnBook value false", "isready", "ucinewgame", "isready",
              f"position fen {FEN}", "isready"):
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


b = chess.Board(FEN)
print(f"exe {EXE}")
print(f"position {FEN}")
print()
print("== 1. my claimed mate-in-3 line, replayed:")
bb = chess.Board(FEN)
for mv in LINE:
    bb.push_uci(mv)
print(f"   {' '.join(LINE)} -> is_checkmate: {bb.is_checkmate()}   (so the LINE is a mate)")
print()
print("== 2. is that mate FORCED? black's replies after the first move:")
bb = chess.Board(FEN)
bb.push_uci(LINE[0])
for bm in bb.legal_moves:
    nb = bb.copy()
    nb.push(bm)
    mates = [mv.uci() for mv in nb.legal_moves if (lambda x: (x.push(mv), x.is_checkmate())[1])(nb.copy())]
    print(f"   black {bm.uci():6s} -> immediate mates for white: {mates if mates else 'NONE'}")
print()
print("== 3. forced-mate existence (the test that matters):")
for p in (1, 3, 5):
    print(f"   forced mate within {p} plies: {forced_mate_within(chess.Board(FEN), p)}")
print()
print("== 4. what the engine says (for the record):")
rows = []
for d in (8, 10, 12, 14, 16, 20):
    info = search(d)
    m = re.search(r"score (mate|cp) (-?\d+)", info)
    sc = f"{m.group(1)} {m.group(2)}" if m else "?"
    print(f"   depth {d:2d}: {sc:10s} pv {info.split(' pv ')[-1].split()[:6]}")
    rows.append({"depth": d, "info": info, "score": sc})

with open(os.path.join(OUT, "withdraw_s21.json"), "w") as f:
    json.dump({"fen": FEN, "line": LINE, "line_is_mate": bb.is_checkmate(),
               "forced_1": forced_mate_within(chess.Board(FEN), 1),
               "forced_3": forced_mate_within(chess.Board(FEN), 3),
               "forced_5": forced_mate_within(chess.Board(FEN), 5),
               "engine": rows}, f, indent=1)
print("\nwrote withdraw_s21.json")
