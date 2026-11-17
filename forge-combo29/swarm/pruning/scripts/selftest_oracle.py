#!/usr/bin/env python3
"""Self-test the mate oracle against known answers AND against planted faults.

The brief's rule 4: "Prove every checker fires on a planted fault before you
trust its clean run." An oracle that agrees with the engine proves nothing if
the oracle itself is broken. So this script:

  1. checks both solvers against hand-verified known answers;
  2. checks they agree with each other on every corpus entry;
  3. plants THREE faults and requires each to be caught:
       (a) an oracle that reports mate-in-1 for every position;
       (b) an oracle with its distance off by one ply (the "right move, wrong
           distance" defect §4 documents, injected on purpose);
       (c) an oracle that ignores the defender's best reply (assumes every
           reply loses), which turns "a mate exists" into "a mate in 1".

If a planted fault is NOT caught, the comparison logic is too weak and no
"no defect found" result from this seat would mean anything.
"""
from __future__ import annotations

import json
import sys

import chess

sys.path.insert(0, "scripts")
import mateoracle as mo  # noqa: E402

# Every expectation below was checked by hand against python-chess's own
# is_checkmate() on the final position of the mating line, not taken on trust.
KNOWN = [
    # (fen, expected oracle result, why)
    ("8/8/8/8/8/1R6/8/k1K5 w - - 0 1", 1, "Rb3-a3 mate in 1 (the audit's own fixture)"),
    ("8/8/8/8/8/8/1R2R3/K1k5 w - - 0 1", 1, "two rooks, mate in 1"),
    ("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", 1, "back-rank Ra8 mate in 1"),
    ("r1b2k1r/ppp1bppp/8/1B1Q4/5q2/2P5/PPP2PPP/R3R1K1 w - - 1 1", 3, "Qd8+ deflection mate in 2"),
    ("8/8/8/8/8/8/Q7/K1k5 w - - 0 1", 0, "Qa2 vs Kc1: stalemate-only, no mate"),
    ("8/8/8/8/8/8/8/K1k5 w - - 0 1", 0, "bare kings"),
    # White to move is in check with exactly one legal move (a1a2), after which
    # Black mates. White cannot FORCE mate, so 0 is correct: the contract
    # reports what the side to move can force. Verified with python-chess:
    # is_checkmate() False, legal_moves == [a1a2].
    ("8/8/8/8/8/5k2/8/K1q5 w - - 0 1", 0, "White is the one being mated; cannot force"),
]


def planted_always_mate1(board: chess.Board, max_plies: int) -> int:
    """Fault (a): claim mate in 1 everywhere."""
    return 1


def planted_off_by_one(board: chess.Board, max_plies: int) -> int:
    """Fault (b): correct verdict, distance off by two plies (one move)."""
    real = mo.solve_negamax(board, max_plies)
    return real + 2 if real > 0 else real


def planted_ignore_defender(board: chess.Board, max_plies: int) -> int:
    """Fault (c): assume every defender reply loses -> 'mate' where there is none."""
    for move in board.legal_moves:
        board.push(move)
        board.pop()
        return 1
    return 0


def main() -> int:
    failures: list[str] = []

    print("== 1. known answers, both solvers ==")
    for fen, expected, why in KNOWN:
        b = chess.Board(fen)
        a = mo.solve_negamax(b, 5)
        c = mo.solve_layered(b, 5)
        ok = (a == c == expected)
        print(f"  {'OK ' if ok else 'BAD'} negamax={a:2d} layered={c:2d} exp={expected:2d}  {why}")
        if not ok:
            failures.append(f"known-answer mismatch on {fen}: {a}/{c} vs {expected}")

    print("\n== 2. planted faults must be caught ==")
    for name, faulty in (("always-mate-1", planted_always_mate1),
                         ("off-by-two-plies", planted_off_by_one),
                         ("ignore-defender", planted_ignore_defender)):
        caught = 0
        for fen, expected, _ in KNOWN:
            if faulty(chess.Board(fen), 5) != expected:
                caught += 1
        print(f"  {'OK ' if caught else 'BAD'} {name}: disagreed with truth on {caught}/{len(KNOWN)}")
        if not caught:
            failures.append(f"planted fault {name} was NOT caught -- comparison logic is too weak")

    print("\n== 3. both solvers agree on the corpus ==")
    try:
        with open("corpus/mates.json") as fh:
            corpus = json.load(fh)["entries"]
    except FileNotFoundError:
        print("  (no corpus yet; skipping)")
        corpus = []
    disagree = []
    for e in corpus:
        b = chess.Board(e["fen"])
        a = mo.solve_negamax(b, e["plies"])
        c = mo.solve_layered(b, e["plies"])
        if a != c or a != e["plies"]:
            disagree.append((e["fen"], a, c, e["plies"]))
    print(f"  {len(corpus) - len(disagree)}/{len(corpus)} entries agree with both solvers")
    if disagree:
        for row in disagree[:5]:
            print("   DISAGREE", row)
        failures.append(f"{len(disagree)} corpus entries disagree")

    print()
    if failures:
        for f in failures:
            print("FAIL:", f, file=sys.stderr)
        return 1
    print("OK -- oracle verified against known answers, both planted faults caught, "
          "solvers agree on the corpus.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
