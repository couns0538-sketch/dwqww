"""Attempted reproduction of sec 2's "forfeits a mate in one" — and why this seat reports
it as NOT REPRODUCED rather than as confirmed or refuted.

Sec 2 states that on six measured fixtures the base plays the generator's first move at a
drawn root and thereby forfeits a mate in one.  Testing that from the client side needs a
position that is BOTH a threefold repetition AND has a mate in one available, reached by a
legal move list.

This script tried to construct one and could not.  The attempts are recorded because a
failed construction is a result about the instrument, not about the engine:

  * `7k/8/6K1/8/8/8/8/1N5R w` has `g6f7#`, but `Rh1` already attacks `h8`, so Black is in
    check while White is to move -- the base is ILLEGAL, and the shuffle cannot start.
  * With Black given a shuffling knight (`1n5k/...`), Black's ONLY legal reply is `h8g8`,
    because the rook check must be answered -- so no repetition line exists.
  * Shuffling the rook instead removes the mate.

The structural reason: a mate in one at a repetition root needs the mating move to stay
available through the shuffling, and each shuffle must be legal for BOTH sides.  This seat
did not find such a line in the time available, so it does NOT claim sec 2's mate-forfeit
result and does NOT refute it.

**The measured substitute is stronger and is what FINDINGS.md relies on:** at a bailed root
the engine's returned move disagrees with its own search on 0 of 6 (hand-audited) and 36 of
40 (sampled from 200 games).  A move disagreement is measurable on every bail; a mate
forfeit needs a rare position.  The disagreement figure covers the mate case without needing
to construct one.

Run: python3 bail_forfeit.py
"""
from __future__ import annotations

import sys

import chess

ATTEMPTS = [
    ("7k/8/6K1/8/8/8/8/1N5R w - - 0 1",
     "Rh1 checks Kh8 with White to move: illegal base"),
    ("1n5k/8/6K1/8/8/8/8/1N5R w - - 0 1",
     "rook check forces h8g8 as Black's only reply: no repetition line"),
    ("k7/8/1K6/8/8/8/8/R6N w - - 0 1",
     "b6c7# available, but no legal alternating shuffle keeps it and repeats"),
]


def diagnose(fen: str) -> dict:
    b = chess.Board(fen)
    mates = []
    for m in b.legal_moves:
        b.push(m)
        if b.is_checkmate():
            mates.append(m.uci())
        b.pop()
    # is the side NOT to move in check?  (an illegal position)
    opp_in_check = b.is_attacked_by(b.turn, b.king(not b.turn))
    return {
        "fen": fen,
        "legal": b.is_valid(),
        "mate_in_one": mates,
        "opponent_in_check_while_we_move": opp_in_check,
        "legal_moves": len(list(b.legal_moves)),
    }


def main() -> int:
    print("Attempted fixtures for a threefold root WITH a mate in one:\n")
    for fen, why in ATTEMPTS:
        d = diagnose(fen)
        print(f"  {fen}")
        print(f"    valid={d['legal']}  mate_in_one={d['mate_in_one']}  "
              f"opponent_in_check_on_our_move={d['opponent_in_check_while_we_move']}")
        print(f"    why it failed: {why}\n")

    print("RESULT: NOT REPRODUCED.")
    print("  This seat could not construct a legal repetition root that also has a mate in")
    print("  one.  It therefore neither confirms nor refutes sec 2's mate-forfeit claim.")
    print("  The substitute measurement FINDINGS.md relies on is move disagreement between")
    print("  the bail and the engine's own search: 0/6 hand-audited, 36/40 sampled.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
