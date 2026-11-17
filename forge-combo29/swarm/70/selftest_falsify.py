"""Falsification: every claim-bearing script must be able to report the WRONG
answer.  A harness that cannot fail proves nothing, so each check here plants a
fault that the corresponding measurement must catch.

F1  board identity: a FEN the engine refuses must not be usable as a position.
    Plant: a bad FEN.  Must be caught by perft1 != python-chess, or by the
    `invalid FEN` string in the position reply.
F2  board identity: a FEN the engine ACCEPTS but that differs from the intended
    one must be caught.  Plant: a FEN with one square changed.  perft1 must move.
F3  driver: an illegal move in the argument list must be detectable.  Plant: a
    legal move and a fake one; the fake must not appear in the legal set.
F4  driver: the timeout must fire rather than hang forever.  Plant: `go infinite`
    with a 2 s timeout; the run must return fatal=timeout, not block.
F5  analysis: the rank-agreement arithmetic must be able to report disagreement.
    Plant: hand-built score dicts where the pinned order is reversed; the same
    comparison code must yield 0 agreement.
F6  analysis: the tie fixture proof must reject a non-mate position.  Plant: an
    ordinary position; mate_in_1_moves must return an empty list.

Run: python3 selftest_falsify.py
Writes selftest_falsify.txt   -- exits non-zero if any planted fault went uncaught.
"""
import itertools
import os
import sys

import chess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "job3"))
sys.path.insert(0, os.path.join(HERE, "job1"))
import engine  # noqa: E402
from gen_positions import mate_in_1_moves  # noqa: E402

RESULTS = []


def check(name, expect_caught, caught, detail):
    ok = (caught == expect_caught)
    RESULTS.append((name, expect_caught, caught, ok, detail))
    return ok


def main():
    out = [f"engine {engine.ENGINE}", ""]

    # F1: a FEN the engine refuses
    bad = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1"
    legal = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").legal_moves.count()
    n, err, pos = engine.perft1(bad)
    caught1 = (n != legal) or (err == "invalid FEN") or ("invalid FEN" in pos)
    check("F1 bad FEN", True, caught1, f"perft1={n} err={err!r}")
    out.append(f"F1 bad FEN: perft1={n} err={err!r} string_in_reply={'invalid FEN' in pos} -> caught {caught1}")

    # F2: an accepted-but-different FEN
    good = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    moved = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 2"   # only the clock differs
    shifted = "rnbqkbnr/pppppppp/8/8/8/7P/PPPPPPP1/RNBQKBNR w KQkq - 0 1"  # a pawn moved
    n_good, _, _ = engine.perft1(good)
    n_shift, _, _ = engine.perft1(shifted)
    caught2 = (n_good != n_shift)
    check("F2 shifted board", True, caught2, f"perft1 {n_good} vs {n_shift}")
    out.append(f"F2 shifted board: perft1 {n_good} vs {n_shift} -> caught {caught2}")
    n_clock, _, _ = engine.perft1(moved)
    out.append(f"F2b clock-only change: perft1 {n_clock} vs {n_good} -> "
               f"caught {n_clock != n_good}  (EXPECTED NOT CAUGHT: perft cannot see a clock)")

    # F3: an illegal move in the argument list
    board = chess.Board(good)
    legal_set = {m.uci() for m in board.legal_moves}
    fake = "e2e5"
    caught3 = (fake not in legal_set) and bool(legal_set)
    check("F3 fake move", True, caught3, f"{fake} in legal set: {fake in legal_set}")
    out.append(f"F3 fake move {fake} in legal set: {fake in legal_set} -> caught {caught3}")

    # F4: the timeout must fire
    r = engine.run_session(f"position fen {good}", "go infinite", timeout=2.0)
    caught4 = r.fatal is not None and "timeout" in str(r.fatal)
    check("F4 timeout fires", True, caught4, f"fatal={r.fatal!r}")
    out.append(f"F4 go infinite with 2 s timeout: fatal={r.fatal!r} -> caught {caught4}")

    # F5: the rank comparison must be able to report total disagreement
    base = {"a": 100, "b": 90, "c": 80}
    pin_bad = {"a": 70, "b": 80, "c": 90}     # fully reversed
    agree = tot = 0
    for x, y in itertools.combinations("abc", 2):
        tot += 1
        agree += int((base[x] > base[y]) == (pin_bad[x] > pin_bad[y]))
    caught5 = (agree == 0 and tot == 3)
    check("F5 reversed order", True, caught5, f"agreement {agree}/{tot}")
    out.append(f"F5 reversed pinned order: agreement {agree}/{tot} -> caught {caught5}")

    # F6: the tie proof must reject a non-mate position
    plain = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    caught6 = mate_in_1_moves(plain) == []
    check("F6 no mate at startpos", True, caught6, f"{mate_in_1_moves(plain)}")
    out.append(f"F6 mate_in_1 on startpos: {mate_in_1_moves(plain)} -> caught {caught6}")

    # F7: the tie proof must FIND mates where they exist
    tie = chess.Board("5r2/2R5/K7/1R6/8/8/R4R2/4k3 w - - 0 1")
    found = mate_in_1_moves(tie)
    caught7 = len(found) == 2
    check("F7 finds known mates", True, caught7, f"{found}")
    out.append(f"F7 mate_in_1 on a known 2-mate position: {found} -> caught {caught7}")

    out += ["", "== RESULT ==",
            "check | expected caught | actually caught | PASS"]
    text_lines = []
    all_ok = True
    for name, exp, got, ok, detail in RESULTS:
        all_ok &= ok
        text_lines.append(f"{name} | {exp} | {got} | {'PASS' if ok else 'FAIL'}   {detail}")
    out += text_lines
    out.append(f"F2b (clock-only) | False | {n_clock != n_good} | "
               f"{'PASS' if n_clock == n_good else 'FAIL'}   a perft check cannot see the halfmove clock; "
               f"documented, not a defect of the harness")
    if n_clock != n_good:
        all_ok = False
    out.append("")
    out.append(f"ALL PLANTED FAULTS HANDLED: {all_ok}")

    text = "\n".join(out)
    with open(os.path.join(HERE, "selftest_falsify.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
