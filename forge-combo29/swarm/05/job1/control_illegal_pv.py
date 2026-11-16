#!/usr/bin/env python3
"""control_illegal_pv.py -- THE CONTROL: proves the pv checker both ACCEPTS real pv lines and CATCHES an
illegal last move, and is deterministic.

The pv lines are not typed by hand: they are READ from out/rows.jsonl (real engine output). For each sampled
position the tampered line replaces the last move with the first uci string, scanned in a fixed order, that is
NOT a legal move in the position at that ply -- so the tampered move is guaranteed illegal by construction.
"""
import itertools
import json

import chess

FILES = "abcdefgh"


def first_illegal_move(board):
    """deterministically find a uci string that is not legal in board"""
    for a, b in itertools.product(FILES, "12345678"):
        for c, d in itertools.product(FILES, "12345678"):
            u = a + b + c + d
            try:
                m = chess.Move.from_uci(u)
            except Exception:
                continue
            if m not in board.legal_moves:
                return u
    return None


def replay(fen, moves):
    b = chess.Board(fen)
    for i, u in enumerate(moves):
        try:
            m = chess.Move.from_uci(u)
        except Exception as e:
            return ("ILLEGAL", i, u, f"unparsable: {e}")
        if m not in b.legal_moves:
            return ("ILLEGAL", i, u, "not legal in position")
        b.push(m)
    return ("LEGAL", len(moves), None, f"final checkmate={b.is_checkmate()}")


rows = [json.loads(l) for l in open("out/rows.jsonl")]
sample = [r for r in rows if r.get("last_pv") and len(r["last_pv"]["moves"]) >= 2][:5]
# a mate position as well, so the control covers a pv that ends in checkmate
sample.append(next(r for r in rows if r.get("last_pv") and r["last_pv"].get("score", ("",))[0] == "mate"
                   and r["last_pv"]["score"][1] > 0))

print("CONTROL: does the pv checker accept real pv lines and catch an illegal last move?")
allok = True
for r in sample:
    fen = r["fen"]
    pv = list(r["last_pv"]["moves"])
    a = replay(fen, pv)
    a2 = replay(fen, pv)
    # build the tampered line: true prefix, then a move guaranteed illegal
    b = chess.Board(fen)
    for u in pv[:-1]:
        b.push(chess.Move.from_uci(u))
    bad = first_illegal_move(b)
    pv_bad = pv[:-1] + [bad]
    c = replay(fen, pv_bad)
    ok = (a[0] == "LEGAL") and (c[0] == "ILLEGAL") and (a == a2)
    allok = allok and ok
    sc = r["last_pv"]["score"]
    print(f"{'OK  ' if ok else 'FAIL'} set={r['set']} pos={r['pos']:3d} score={sc[0]} {sc[1]:+d} "
          f"pv_plies={len(pv)}")
    print(f"      fen      : {fen}")
    print(f"      real pv  : {a[0]} at ply {a[1]}  ({a[3]})   repeat identical: {a == a2}")
    print(f"      tampered : {c[0]} at ply {c[1]} move {c[2]} ({c[3]})")
print("CONTROL", "PASS" if allok else "FAIL")
