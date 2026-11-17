"""Self-test for the material judge used by q3_book_vs_search.py.

A material judge that is wrong in a sign or a ply produces a confident list of
"losses" that is entirely its own error. That happened twice while this audit was
built:

  * one reply ply with no recapture  -> 45 phantom losses, all exactly 100/300/800
  * negamax recurred on `-side` where `side` is a python-chess Color (a bool),
    so `-True == -1` was never a colour  -> 27 more, all exactly 100 or 300

HOW THE FIXTURES ARE BUILT: every position here is reached by LEGAL PLAY from
startpos, never hand-written as a FEN. Four hand-written FENs in earlier drafts
were illegal (adjacent kings, a side already in check, a castling right that
cannot exist) and each one made a test pass or fail for a reason unrelated to the
judge. Deriving the position from moves makes legality structural: if the move
sequence is legal the position is legal, and python-chess asserts that for us.

Each case pins the SIGN and the exact centipawn value.
"""

from __future__ import annotations

import sys

import chess

from q3_book_vs_search import settled_material


def position(moves: str) -> chess.Board:
    board = chess.Board()
    for m in moves.split():
        board.push_uci(m)
    return board


# (name, moves to reach the position, move to play, expected delta, why)
CASES = [
    ("free pawn, nothing recaptures",
     "e2e4 d7d5", "e4d5", 0,
     "exd5 and Black's queen recaptures on d5 -- pawn for pawn, net 0. The name "
     "of the first draft of this case claimed +100; the RECAPTURE is why it is 0, "
     "and that is exactly what the judge must not miss."),

    ("quiet opening move, nothing hanging",
     "", "e2e4", 0,
     "no captures available to either side"),

    ("Italian Nxe5 loses a piece for a pawn",
     "e2e4 e7e5 g1f3 b8c6 f1c4 g8f6", "f3e5", -200,
     "knight (300) takes pawn (100) and Nc6xe5 recaptures: 100 - 300 = -200"),

    ("capture of a pawn that is not recaptured",
     "e2e4 d7d5 e4d5 d8d5 b1c3 d5d8", "c3b5", 0,
     "Nb5 is a quiet developing move and no capture follows either way; the point "
     "is that the judge does not invent a loss in a normal position"),

    ("opponent's capture is visible after a quiet move",
     "e2e4 e7e5", "g1f3", 0,
     "Nf3 attacks e5 but Black simply defends; no immediate material change"),

    ("capturing promotion adds the captured piece",
     "a2a4 b7b5 a4b5 g7g5 b5b6 g5g4 b6b7 g4g3 h2g3 a7a6", "b7a8q", 1300,
     "the b7 pawn promotes AND takes the rook on a8: 800 + 500 = 1300. A "
     "non-capturing promotion is not reachable from startpos by legal play in a "
     "few plies, so it is not asserted here rather than being asserted from a "
     "hand-built FEN -- which was where three fixture errors came from."),
]


def main() -> int:
    failures = []
    for name, reach, uci, expected, why in CASES:
        board = position(reach)
        if not board.is_valid():
            failures.append((name, "fixture not legal", reach))
            print(f"FAIL  {name:44s} fixture not a legal position")
            continue
        mv = chess.Move.from_uci(uci)
        if not board.is_legal(mv):
            failures.append((name, "move illegal", uci))
            print(f"FAIL  {name:44s} move {uci} illegal in fixture")
            continue
        got, err = settled_material(None, board, mv, 8, 1.0)   # engine unused
        ok = err is None and got == expected
        print(f"{'PASS' if ok else 'FAIL'}  {name:44s} {expected:+5d} got "
              f"{got if got is not None else err}")
        print(f"        why: {why}")
        if not ok:
            failures.append((name, expected, got, err))

    # a negative control: the same judge MUST disagree when the value is wrong,
    # so a green run above cannot be green for a reason unrelated to the judge
    board = position("e2e4 d7d5")
    got, _ = settled_material(None, board, chess.Move.from_uci("e4d5"), 8, 1.0)
    if got == 100:
        print("FAIL  negative control: judge reported +100 for the Scandinavian "
              "exchange, so it is not resolving the recapture")
        failures.append(("negative control", 0, got))
    else:
        print(f"PASS  negative control: judge reports {got:+d}, not the naive +100")

    print()
    if failures:
        print(f"{len(failures)} FAILURE(S) -- the material judge is not trustworthy, so "
              "no Q3 number from it may be reported:")
        for f in failures:
            print("   ", f)
        return 1
    print(f"all {len(CASES)} material-judge cases pass, plus the negative control")
    return 0


if __name__ == "__main__":
    sys.exit(main())
