"""Fault-planting proof that the determinism harness can actually fail.

A harness that has never been shown to fail is not evidence. This file plants four
faults and requires the harness to catch each one. If any check prints PASS when it
should print CAUGHT, the harness is not usable and no number it produces counts.

F1  a FEN python-chess rejects must be refused before contact with the engine;
F2  a FEN the ENGINE rejects (python-chess accepts it) must be caught in the
    position reply -- tested both with and without an `isready` after `position`,
    because the diagnostic moves between the two streams;
F3  a search whose output is truncated by EOF (the piped-harness defect) must not
    be recorded as a measurement;
F4  two runs that genuinely differ must compare as DIFFERENT -- the comparison
    used for every determinism cell must be able to say "not identical".
"""

import sys

import chess

import ucih
from matrix import BASE_EXE, cell_key, run_cell

OPTIONS = [("Hash", 16), ("Threads", 1)]

results = []


def record(name, caught, detail):
    results.append((name, caught, detail))
    print("%-52s %s  %s" % (name, "CAUGHT" if caught else "NOT CAUGHT", detail))


def f1_python_chess_rejects():
    # A king missing from the board: python-chess refuses it outright.
    bad = "8/8/8/8/8/8/8/8 w - - 0 1"
    try:
        run_cell(BASE_EXE, bad, "go depth 2", OPTIONS)
    except Exception as exc:  # noqa: BLE001
        record("F1 python-chess rejects an empty-board FEN", True, type(exc).__name__)
    else:
        record("F1 python-chess rejects an empty-board FEN", False, "search ran anyway")


def f2_engine_rejects(with_isready):
    # python-chess accepts this board and calls it VALID; the engine refuses it because
    # it requires fullmove >= 1. This is the dangerous class: a FEN that passes the
    # validator and is still searched as the PREVIOUS position.
    fen = "4k3/8/8/8/8/8/8/R3K2R w K - 0 0"
    try:
        ok = chess.Board(fen)
    except Exception as exc:  # noqa: BLE001
        record("F2 python-chess accepts the trap FEN (setup)", False, str(exc))
        return
    if not ok.is_valid():
        record("F2 trap FEN must be python-chess VALID (setup)", False, str(ok.status()))
        return

    caught = False
    where = "no diagnostic seen"
    engine = ucih.Engine(BASE_EXE, timeout=60)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        if with_isready:
            # The diagnostic lands in the POSITION reply, before readyok.
            engine.send("position fen %s" % fen)
            try:
                reply = engine.sync("position")
            except ucih.EngineError as exc:
                caught = True
                where = "position reply (sync raised)"
                del exc
                reply = []
            if any("invalid FEN" in line for line in reply):
                caught = True
                where = "position reply"
        else:
            # No isready between position and go: the diagnostic lands in the go
            # output, ahead of the first `info depth`.
            engine.send("position fen %s" % fen)
            try:
                res = engine.go("go depth 2")
            except ucih.EngineError as exc:
                caught = "invalid FEN" in str(exc)
                where = "go output (go raised)"
                res = None
            if res is not None and any("invalid FEN" in line for line in res["lines"]):
                caught = True
                where = "go output"
    finally:
        engine.close()
    label = "F2 engine invalid FEN, isready after position" if with_isready \
        else "F2 engine invalid FEN, NO isready after position"
    record(label, caught, where)


def f3_piped_truncation():
    # The exact defect: close stdin during the search. The engine answers a
    # fabricated legal move with zero info lines.
    import subprocess
    out = subprocess.run(
        ["bash", "-c", "printf 'uci\\nisready\\nposition startpos\\ngo depth 8\\n' | '%s'" % BASE_EXE],
        capture_output=True, text=True, timeout=120).stdout
    info_lines = [l for l in out.splitlines() if l.startswith("info depth ")]
    best = [l for l in out.splitlines() if l.startswith("bestmove")]
    defect_seen = len(info_lines) == 0 and bool(best)
    # Now the driver, which keeps stdin open.
    good = run_cell(BASE_EXE, None, "go depth 8", OPTIONS)
    driver_fine = good["n_info"] > 0
    record("F3 piped-EOF defect reproduced (0 info lines)", defect_seen,
           "%d info lines, bestmove %s" % (len(info_lines), best[-1] if best else "none"))
    record("F3 driver immune to it (info lines present)", driver_fine,
           "%d info lines, bestmove %s" % (good["n_info"], good["bestmove"]))


def f4_comparison_can_differ():
    # Two different budgets on the same position must NOT compare equal.
    a = run_cell(BASE_EXE, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                 "go depth 4", OPTIONS)
    b = run_cell(BASE_EXE, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                 "go depth 8", OPTIONS)
    diff = cell_key(a) != cell_key(b)
    record("F4 differing cell keys compare as DIFFERENT", diff,
           "%s vs %s" % (cell_key(a)[:2], cell_key(b)[:2]))
    c = run_cell(BASE_EXE, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                 "go depth 4", OPTIONS)
    same = cell_key(a) == cell_key(c)
    record("F4 identical cells compare as IDENTICAL (control)", same, str(cell_key(a)[:2]))


def main():
    print("exe:", BASE_EXE)
    f1_python_chess_rejects()
    f2_engine_rejects(with_isready=True)
    f2_engine_rejects(with_isready=False)
    f3_piped_truncation()
    f4_comparison_can_differ()
    bad = [name for name, caught, _ in results if not caught]
    print("\n%d checks, %d not caught" % (len(results), len(bad)))
    if bad:
        for name in bad:
            print("  FAILED:", name)
        return 1
    print("ALL CHECKS CAUGHT THEIR FAULT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
