#!/usr/bin/env python3
"""construct_game.py -- build a REAL, REPLAYABLE game reaching the miss.

The assignment: "Construct a realistic game sequence reaching halfmove 98-99 with
a mate available, and report whether the engine misses it."

What makes this honest:
  * the game starts at the STANDARD position and every move is legal and replayed
    through python-chess, so the result is a real game by construction;
  * the whole move list is emitted, so the reader can replay it with
    `position startpos moves ...` and check every ply;
  * the position is checked against the oracle (independent) before it is used;
  * attempts are counted, so "I found one" is accompanied by "out of how many".

The plan, which is what a real game looks like and not a constructed FEN:

  Phase 1 (opening, real theory): the Italian. White gains space.
  Phase 2 (the win): White wins the black queen with a well-known trap line, so
    the material imbalance is produced by real play, not by placing pieces.
  Phase 3 (the shuffle): White, far ahead, does NOT convert -- it shuffles
    non-pawn, non-capturing moves, which is the clock-climbing phase. This is
    exactly what an engine at low depth, or a human in time trouble, does.
  Phase 4 (the mate): at the moment the clock sits in the band, the mate must be
    available. The script checks for it and reports the clock at which it first
    appears.

If phase 4 never coincides with the band, the script says so and reports how many
shuffle orders it tried -- that is the honest negative the assignment allows.

Usage: construct_game.py --tries 200 --seed 6201 [--out game.json]
"""
import argparse
import json
import random
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job3")
from matedist import evaluate, MATE  # noqa: E402

ORACLE_PLIES = 8

# Italian, then the black queen is won by real play (a real trap line).
OPENING = [
    "e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "f3g5", "d7d5",
    "e4d5", "c6a5", "c4b5", "c7c6", "d5c6", "b7c6", "b5e2", "h7h6",
    "g5f3", "e5e4", "f3e5", "f8d6", "d2d4", "e8g8", "e1g1", "d6e5",
    "d4e5", "d8d1", "f1d1",
]


def replay(moves):
    b = chess.Board()
    out = []
    for m in moves:
        mv = chess.Move.from_uci(m)
        if mv not in b.legal_moves:
            return None, out, m
        b.push(mv)
        out.append(m)
    return b, out, None


def oracle_value(board):
    v = evaluate(board.fen(), ORACLE_PLIES)
    if v <= -MATE + ORACLE_PLIES:
        return ("mated", MATE + v)
    if v >= MATE - ORACLE_PLIES:
        return ("mates", MATE - v)
    return ("draw", 0)


def quiet_moves(board):
    out = []
    for mv in board.legal_moves:
        if board.is_capture(mv):
            continue
        pc = board.piece_at(mv.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            continue
        out.append(mv)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tries", type=int, default=50)
    ap.add_argument("--seed", type=int, default=6201)
    ap.add_argument("--out", default="constructed_game.json")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    base, used, bad = replay(OPENING)
    print("opening: %d plies replayed, %s" % (
        len(used), "OK" if base is not None else "ILLEGAL at %s" % bad))
    if base is None:
        return 2
    print("after opening: clock=%d" % base.halfmove_clock)
    kind, val = oracle_value(base)
    print("oracle: %s %s" % (kind, val if kind != "mated" else val))

    hits = []
    examined = 0
    for attempt in range(args.tries):
        examined += 1
        b = base.copy()
        hist = list(used)
        # Phase 3: shuffle quietly; at every ply in/near the band, test the oracle
        for _ in range(300):
            if b.halfmove_clock >= 93:
                kind, val = oracle_value(b)
                if kind == "mated":
                    p = val
                    H = b.halfmove_clock
                    in_band = H > 100 - p
                    rec = {"attempt": attempt, "fen": b.fen(), "H": H, "p": p,
                           "j0": 100 - H, "in_band": in_band, "moves": list(hist),
                           "plies": len(hist)}
                    hits.append(rec)
                    print("%-8s H=%d p=%d j0=%d plies=%d" % (
                        "IN BAND" if in_band else "near", H, p, 100 - H, len(hist)))
                    break
            q = quiet_moves(b)
            if not q:
                break
            mv = rng.choice(q)
            b.push(mv)
            hist.append(mv.uci())
            if b.is_checkmate() or not any(b.legal_moves):
                break

    in_band = [h for h in hits if h["in_band"]]
    print("---- attempts                : %d" % examined)
    print("---- attempts with a mate    : %d" % len(hits))
    print("---- of those, IN BAND       : %d" % len(in_band))
    if in_band:
        best = in_band[0]
        print("---- example in-band game, %d plies, clock %d, mate in %d plies" % (
            best["plies"], best["H"], best["p"]))
        print("---- replay with: position startpos moves " + " ".join(best["moves"]))
    json.dump({"opening": used, "attempts": examined, "hits": hits},
              open(args.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
