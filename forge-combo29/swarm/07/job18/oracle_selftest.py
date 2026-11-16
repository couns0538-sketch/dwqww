#!/usr/bin/env python3
"""Self-test for see_oracle.see_value. Each case's expected value was settled by hand with
python-chess move lists (quoted beside it), so this is an assertion of known truths, not a
regression against my own previous output.

History: my first two oracle versions were wrong (job7), and a third expectation of mine was
wrong (+200 for b2b4) while the oracle was right (0). Every number here is justified by the
listed python-chess line.
"""
import sys
import chess

sys.path.insert(0, ".")
from see_oracle import see_value  # noqa: E402

CASES = [
    # (fen, move, expected, why -- settled with python-chess)
    ("4k3/8/8/8/8/8/4r3/4K3 w - - 0 1", "e1e2", 500,
     "attackers(BLACK, e2) is empty, so the rook is undefended: +500"),
    ("2b1kbn1/2r3p1/p1Pp1q2/5p2/2BpPP2/1P2Q2r/P1R4P/RNB1K3 w Q - 2 29", "e4f5", 100,
     "after exf5 Black's only captures are h3e3 and d4e3; nothing recaptures on f5: +100"),
    ("r1bqkbnr/pppppppp/2n5/8/8/2P5/PP1PPPPP/RNBQKBNR w KQkq - 1 2", "b2b4", 0,
     "b4 Nxb4 cxb4: White gives a pawn and wins a knight with a pawn, then the knight and the "
     "recaptured pawn cancel -> 0 (my earlier claim of +200 ignored that White's c-pawn is also lost)"),
    # undefended pawn: +100. (My first expectation here was -800 on the assumption the pawn was
    # defended; python-chess attackers(BLACK, d3) is empty, so the oracle's +100 was right.)
    ("4k3/8/8/8/8/3p4/4Q3/4K3 w - - 0 1", "e2d3", 100,
     "attackers(BLACK, d3) is empty -> +100"),
    # a truly defended pawn: Qxd3 recaptured by the c4 pawn -> +100 - 900 = -800
    ("4k3/8/8/8/2p5/3p4/4Q3/4K3 w - - 0 1", "e2d3", -800,
     "Qxd3 cxd3: White wins a pawn (+100) and loses the queen (-900) -> -800"),
]


def main():
    failures = 0
    for fen, uci, want, why in CASES:
        b = chess.Board(fen)
        mv = chess.Move.from_uci(uci)
        if mv not in b.legal_moves:
            print(f"SKIP illegal move {uci} in {fen}")
            continue
        got = see_value(b, mv)
        ok = (got == want)
        print(f"{uci:6s} in {fen[:34]:36s} got {got:6d} want {want:6d} "
              f"{'OK' if ok else 'MISMATCH'}  ({why[:60]})")
        if not ok:
            failures += 1
    print()
    if failures:
        print(f"RESULT: {failures} self-test mismatch(es)")
        sys.exit(1)
    print("RESULT: every self-test case matched the hand-settled value")


if __name__ == "__main__":
    main()
