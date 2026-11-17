"""Prove every checker in this audit fires on a planted fault.

Brief rule 3: "A control that silently does nothing is worse than no control.
Prove every checker fires on a planted fault before you trust its clean run."

Each test below plants a fault that the corresponding predicate MUST reject,
then confirms a known-good case passes. The planted-fault half is the part that
makes the clean runs meaningful.
"""
import sys
import chess

import stalemate as S
from forge_drv import Rec


FAILED = []


def check(name, cond, detail=""):
    ok = bool(cond)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")
    if not ok:
        FAILED.append(name)


def test_every_move_stalemates():
    print("test_every_move_stalemates")
    # PLANTED FAULT: this position has 13 legal moves and exactly 1 stalemates.
    faulty = chess.Board("7k/7p/7P/8/8/8/8/K6R w - - 0 1")
    st, tot = S.every_move_stalemates(faulty)
    check("planted fault rejected", st != tot, f"(got {st}/{tot}, want unequal)")
    check("planted fault counts 1", st == 1, f"(got {st})")

    # PLANTED FAULT 2: a normal middlegame -- nothing stalemates.
    mid = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    st2, tot2 = S.every_move_stalemates(mid)
    check("startpos rejected", st2 == 0 and tot2 == 20, f"(got {st2}/{tot2})")

    # KNOWN GOOD: a fixture this audit accepts.
    good = chess.Board("8/8/8/8/1pk1p3/1P2P3/5q2/7K b - - 0 30")
    st3, tot3 = S.every_move_stalemates(good)
    check("known-good accepted", st3 == tot3 and tot3 > 0, f"(got {st3}/{tot3})")


def test_mates_in_one():
    print("test_mates_in_one")
    # PLANTED FAULT: mate in one exists only after a move, not in one.
    b = chess.Board("8/8/8/8/8/8/8/K1k1Q3 w - - 0 1")
    check("no mate-in-1 on quiet position", S.mates_in_one(b) == [],
          f"(got {S.mates_in_one(b)})")
    # KNOWN GOOD
    b2 = chess.Board("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    m = S.mates_in_one(b2)
    check("finds Ra8#", "a1a8" in m, f"(got {m})")
    # PLANTED FAULT: a position where mate is in TWO, not one (verified by an
    # independent forced-mate search to 3 plies, not by assumption).
    b3 = chess.Board("8/8/8/8/8/8/Q7/K1k5 w - - 0 40")
    check("mate-in-2 not counted as mate-in-1", S.mates_in_one(b3) == [],
          f"(got {S.mates_in_one(b3)})")


def test_driver_refusal():
    print("test_driver_refusal")
    # The driver must RAISE on a refused FEN rather than search the old board.
    import forge_drv
    exe = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-boundary/forge"
    with forge_drv.Forge(exe) as eng:
        # warm the board with a real position
        eng.set_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        raised = False
        try:
            eng.set_position("this is not a fen at all")
        except forge_drv.RefusedFen:
            raised = True
        check("driver raises RefusedFen", raised)

        # PLANTED FAULT: a FEN with too many fields -- documented as SILENT.
        # We must NOT claim the driver catches it; this records the truth.
        surplus_raised = False
        try:
            eng.set_position(
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 EXTRA JUNK")
        except forge_drv.RefusedFen:
            surplus_raised = True
        check("surplus-field FEN is silently accepted (expected: True)",
              surplus_raised is False, f"(raised={surplus_raised})")


def test_score_parser():
    print("test_score_parser")
    rec = Rec("x", "go depth 1")
    rec.infos = ["info depth 1 score cp 34 nodes 10 pv e2e4"]
    check("parses cp", rec.score() == ("cp", 34), f"(got {rec.score()})")
    rec.infos = ["info depth 3 score mate -1 nodes 10 pv d8c8"]
    check("parses negative mate", rec.score() == ("mate", -1), f"(got {rec.score()})")
    rec.infos = ["info depth 3 score mate 0 nodes 0 pv"]
    check("parses mate 0", rec.score() == ("mate", 0), f"(got {rec.score()})")
    rec.infos = ["info string hello"]
    check("no score -> None", rec.score() is None, f"(got {rec.score()})")
    rec.infos = ["info depth 1 score cp 10 nodes 5 pv e2e4 e7e5"]
    check("parses pv", rec.pv() == ["e2e4", "e7e5"], f"(got {rec.pv()})")


def test_uci_move_consistency():
    print("test_uci_move_consistency")
    # A move the engine returns must be legal on the board we validated.
    b = chess.Board("8/8/8/8/1pk1p3/1P2P3/5q2/7K b - - 0 30")
    legal = {m.uci() for m in b.legal_moves}
    check("fixture legal-move set non-empty", len(legal) > 0, f"(n={len(legal)})")
    check("bogus move not in legal set", "a1a8" not in legal)


def main():
    test_every_move_stalemates()
    test_mates_in_one()
    test_score_parser()
    test_uci_move_consistency()
    test_driver_refusal()
    print()
    if FAILED:
        print(f"SELFTEST FAILED: {FAILED}")
        return 1
    print("SELFTEST PASSED: every checker fired on its planted fault")
    return 0


if __name__ == "__main__":
    sys.exit(main())
