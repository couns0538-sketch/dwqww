#!/usr/bin/env python3
"""Build every non-pawn table and cache it, with the checks that can fail.

Known values this must reproduce, none of them taken from the engine:
  KQK  max DTM 10 moves, KRK max DTM 16 moves
  KBK  drawn in every position (a bishop cannot mate a bare king)
  KNK  drawn in every position (a knight cannot mate a bare king)
  KNNK draws except where a mate is actually reachable
  KBNK max DTM 33 moves (the classical figure)
If any of those disagree the table is wrong and nothing downstream may use it.
"""
import json
import sys
import time

sys.path.insert(0, "/tmp/fx")
import chess
import solver

CACHE = "/tmp/fx/tables.json"

EXPECT = {
    "KQK": {"dtm_max_moves": 10},
    "KRK": {"dtm_max_moves": 16},
    "KBNK": {"dtm_max_moves": 33},
    "KBK": {"WIN": 0, "LOSS": 0},
    "KNK": {"WIN": 0, "LOSS": 0},
}


def build():
    t0 = time.time()
    tables, out = {}, {}
    order = [
        ([(chess.KING, True), (chess.KING, False)], "KK", solver.ALL_SYMS),
        ([(chess.KING, True), (chess.BISHOP, True), (chess.KING, False)], "KBK", solver.ALL_SYMS),
        ([(chess.KING, True), (chess.KNIGHT, True), (chess.KING, False)], "KNK", solver.ALL_SYMS),
        ([(chess.KING, True), (chess.ROOK, True), (chess.KING, False)], "KRK", solver.ALL_SYMS),
        ([(chess.KING, True), (chess.QUEEN, True), (chess.KING, False)], "KQK", solver.ALL_SYMS),
        ([(chess.KING, True), (chess.KNIGHT, True), (chess.KNIGHT, True), (chess.KING, False)],
         "KNNK", solver.ALL_SYMS),
        ([(chess.KING, True), (chess.BISHOP, True), (chess.KNIGHT, True), (chess.KING, False)],
         "KBNK", solver.ALL_SYMS),
    ]
    for pieces, label, syms in order:
        print(f"[{label}] start {time.time()-t0:.0f}s", flush=True)
        tab = solver.solve(pieces, syms, tables)
        tables[solver.sig_of(pieces)] = tab
        s = solver.summarise(tab, label)
        print("   ", s, flush=True)
        exp = EXPECT.get(label, {})
        for k, v in exp.items():
            got = s.get(k)
            print(f"    CHECK {label}.{k}: want {v} got {got} "
                  f"{'OK' if got == v else 'MISMATCH'}", flush=True)
        out[label] = {"summary": s,
                      "value": {json.dumps(k): v for k, v in tab["value"].items()},
                      "dtm": {json.dumps(k): v for k, v in tab["dtm"].items()}}
        json.dump(out, open(CACHE, "w"))
    json.dump({"tables": out, "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "expect": EXPECT}, open(CACHE, "w"), indent=1)
    print("wrote", CACHE, f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    build()
