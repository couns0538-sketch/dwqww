#!/usr/bin/env python3
"""shared_process_effect.py — seat 20 job 20: does searching P and its mirror in ONE process inflate the
search-asymmetry rate? Seat 06 reported 28.6 % bestmove asymmetry; I measured 10.0 % with a FRESH PROCESS per
search (job19). This tests hypothesis (b): a shared TT/history between the two searches.

Design: the same 20 positions, three ways, all through AUDIT/hardened.py:
  A. fresh process for each search                      (my job19 method)
  B. ONE process for the whole run, P then M back to back  (shared TT + history)
  C. ONE process for the whole run with `ucinewgame` between P and M (cold-ish, per seat 10)

Predictions:
1. B shows MORE asymmetry than A: the shared TT/history lets the first search steer the second. I predict B's
   bestmove asymmetry exceeds A's (10 %).
   KILLED IF: B's rate is equal to or lower than A's.

2. C sits between A and B, closer to A, because `ucinewgame` clears the searcher state (seat 10: it restores cold).
   KILLED IF: C equals B exactly, or C is higher than B.

3. Scores stay asymmetric in all three arms (the score difference is not what a shared TT creates).
   KILLED IF: any arm shows fewer than 10 of 20 score differences.

4. If B is much larger than A, then seat 06's 28.6 % can be explained by the harness rather than by their position
   set, which is worth telling the swarm.
   KILLED IF: B is close to A (then the position set is the likely explanation, as I leaned in job19).
"""
import json
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

EXE, OUT = sys.argv[1], sys.argv[2]
N = 20
os.makedirs(OUT, exist_ok=True)
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]


def mirror_move(u):
    if not u or u == "0000":
        return u
    return u[0] + str(9 - int(u[1])) + u[2] + str(9 - int(u[3])) + u[4:]


import random
rng = random.Random(2001)
fens = []
b = chess.Board()
while len(fens) < N:
    mv = list(b.legal_moves)
    if not mv or b.is_game_over():
        b = chess.Board()
        continue
    b.push(rng.choice(mv))
    if b.ply() % 5 == 0 and not b.is_checkmate():
        fens.append(b.fen())


def fresh_search(fen):
    e = Engine(EXE, opts=S14)
    try:
        e.position(fen)
        return e.search("go depth 10", timeout=240)
    finally:
        e.close()


def run_arm(mode):
    rows = []
    if mode == "A":
        for fen in fens:
            P, M = chess.Board(fen), chess.Board(fen).mirror()
            rp, rm = fresh_search(P.fen()), fresh_search(M.fen())
            rows.append({"p": rp["bestmove"], "m": rm["bestmove"], "want": mirror_move(rp["bestmove"]),
                         "ps": rp["score"], "ms": rm["score"]})
    else:
        e = Engine(EXE, opts=S14)
        try:
            for fen in fens:
                P, M = chess.Board(fen), chess.Board(fen).mirror()
                if mode == "C":
                    e.send("ucinewgame")
                    e.isready()
                e.position(P.fen())
                rp = e.search("go depth 10", timeout=240)
                if mode == "C":
                    e.send("ucinewgame")
                    e.isready()
                e.position(M.fen())
                rm = e.search("go depth 10", timeout=240)
                rows.append({"p": rp["bestmove"], "m": rm["bestmove"], "want": mirror_move(rp["bestmove"]),
                             "ps": rp["score"], "ms": rm["score"]})
        finally:
            e.close()
    return rows


print(f"exe {EXE}   positions {len(fens)}   depth 10   S14")
print(f"{'arm':4s} {'bestmove asym':>14s} {'score asym':>11s}   description")
out = {}
for mode, desc in (("A", "fresh process per search (job19 method)"),
                   ("B", "ONE process, P then M back to back (shared TT+history)"),
                   ("C", "ONE process, ucinewgame between P and M")):
    rows = run_arm(mode)
    bm = sum(1 for r in rows if r["want"] != r["m"])
    sc = sum(1 for r in rows if r["ps"] != r["ms"])
    out[mode] = {"bm_asym": bm, "sc_asym": sc, "n": len(rows), "rows": rows}
    print(f"{mode:4s} {bm:8d}/{len(rows):<4d} {sc:8d}/{len(rows):<4d}   {desc}")

with open(os.path.join(OUT, "shared_process_effect.json"), "w") as f:
    json.dump({"exe": EXE, "arms": out}, f, indent=1)
print("\nwrote shared_process_effect.json")
