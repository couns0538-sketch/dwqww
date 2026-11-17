"""Insufficient material: engine verdict vs the FIDE rule.

FIDE 5.2.2: the game is drawn when a position has arisen in which neither
player can checkmate the opponent's king with ANY series of legal moves.
The engine's predicate is a conservative material-only test, which is correct
for the six cases the brief names but is not a general mate-possibility oracle.

Also checks the special case FIDE does NOT draw but naive tests call a draw:
KB vs KB with bishops on the SAME colour is a dead draw; KB vs KB with
OPPOSITE-coloured bishops is a theoretical draw but NOT a forced one -- mate
is possible in principle, so FIDE does not declare it drawn.
"""

import chess

from engine import Probe

CASES = [
    # (fen, label, fide_is_dead_draw, note)
    ("8/8/8/4k3/8/8/8/4K3 w - - 0 1", "K vs K", True,
     "no mating material at all"),
    ("8/8/8/4k3/8/8/8/4KN2 w - - 0 1", "KN vs K", True,
     "knight cannot mate a lone king"),
    ("8/8/8/4k3/8/8/8/4KB2 w - - 0 1", "KB vs K", True,
     "single bishop cannot mate"),
    ("8/8/8/4k3/8/8/8/3NKN2 w - - 0 1", "KNN vs K", False,
     "two knights CAN mate with help; FIDE calls this NOT a dead position"),
    # same colour: c1 and f8 are both (file+rank) even -> no mate possible
    ("5b2/8/8/4k3/8/8/8/2B1K3 w - - 0 1", "KB vs KB same colour", True,
     "both bishops on the same colour complex: no mate possible"),
    # opposite colour: c1 (even) and h1 (odd) -> mate IS possible in principle
    ("8/8/8/4k3/8/8/8/2B1K2b w - - 0 1", "KB vs KB opposite colour", False,
     "mate possible in principle; FIDE does not call this a dead position"),
]


def square_colour(sq):
    return (chess.square_file(sq) + chess.square_rank(sq)) % 2


def main():
    print("=" * 96)
    print("INSUFFICIENT MATERIAL: engine vs FIDE 5.2.2")
    print("=" * 96)
    print("%-24s %-10s %-10s %-8s %s" % ("case", "engine", "fide", "agree", "note"))
    fails = []
    for fen, label, fide_dead, note in CASES:
        board = chess.Board(fen)
        assert board.is_valid(), "python-chess rejected %s" % fen
        oracle = board.is_insufficient_material()
        # engine verdict through the probe binary, which calls the same
        # predicate the search uses
        import subprocess
        out = subprocess.run(["build/probe", "fen", fen], capture_output=True,
                             text=True, timeout=30)
        if out.returncode != 0:
            raise RuntimeError("probe refused %s: %s" % (fen, out.stdout.strip()))
        engine_draw = int([t for t in out.stdout.split() if t.startswith("insufficient=")][0].split("=")[1])
        agree = bool(engine_draw) == fide_dead
        if not agree:
            fails.append((label, engine_draw, fide_dead))
        print("%-24s %-10s %-10s %-8s %s" % (
            label, "draw" if engine_draw else "not draw",
            "draw" if fide_dead else "not draw",
            "OK" if agree else "DISAGREE", note))
        # Cross-check the oracle against our own FIDE reading.
        if oracle != fide_dead:
            print("    note: python-chess says %s where FIDE reading says %s"
                  % (oracle, fide_dead))

    print()
    print("Fails: %d" % len(fails))
    for label, e, f in fails:
        print("  - %s: engine=%s fide=%s" % (label, bool(e), f))
    return fails


if __name__ == "__main__":
    main()
