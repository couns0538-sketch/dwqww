"""63-F12: a threefold repetition root that ALSO has a mate available.

This is the strongest adversarial case: the root is claimable drawn (so the base
adjudicates) but the side to move has a mating move (so the mate outranks the claim).

The fixture is built by a legal move list, not by hand-typed FEN, so the engine's own
key history really holds the repetitions:

    start  7n/8/8/8/8/1R6/2K5/k6N w - - 0 1
    moves  h1g3 h8g6 g3h1 g6h8   (x2)      -> same position a third time, white to move
    mate   b3a3

Asserts: the root is a threefold for python-chess, the mate exists, and then compares
base vs patched on the wire.
"""
import sys

import chess

sys.path.insert(0, "/home/ubuntu/job")
from ucih import Engine  # noqa: E402

START = "7n/8/8/8/8/1R6/2K5/k6N w - - 0 1"
MOVES = ["h1g3", "h8g6", "g3h1", "g6h8"] * 2
BASE = "/home/ubuntu/b_base/forge"
PATCHED = "/home/ubuntu/b_patched/forge"


def build_root():
    b = chess.Board(START)
    assert b.is_valid(), "start FEN illegal"
    for mv in MOVES:
        m = chess.Move.from_uci(mv)
        assert m in b.legal_moves, "move %r illegal at %r" % (mv, b.fen())
        b.push(m)
    assert b.is_valid(), "root illegal"
    assert b.is_repetition(3), "root is not a threefold"
    mates = []
    for m in b.legal_moves:
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            mates.append(m.uci())
    assert mates, "root has no mate; the fixture is pointless"
    return b, mates


def main():
    b, mates = build_root()
    print("root fen        :", b.fen())
    print("threefold       :", b.is_repetition(3))
    print("legal moves     :", b.legal_moves.count())
    print("mating moves    :", mates)

    results = {}
    for tag, exe in (("base", BASE), ("patched", PATCHED)):
        e = Engine(exe)
        try:
            e.send("ucinewgame")
            e.position(START, moves=MOVES)
            lines, bm, info = e.go("go depth 8", timeout=300)
        finally:
            e.quit()
        results[tag] = (bm, info)
        print("%-8s bestmove=%-6s is_mate=%-5s info_lines=%d last=%s" % (
            tag, bm, bm in mates, len(info), info[-1] if info else "NONE"))

    bbm, binfo = results["base"]
    pbm, pinfo = results["patched"]
    assert bbm not in mates, "base unexpectedly found the mate"
    assert pbm in mates, "patched did not find the mate"
    assert "mate 1" in (pinfo[-1] if pinfo else ""), "patched did not report a mate score"
    print("\nVERDICT: base plays a non-mating move, patched reports 'mate 1' and plays the mate")


if __name__ == "__main__":
    main()
