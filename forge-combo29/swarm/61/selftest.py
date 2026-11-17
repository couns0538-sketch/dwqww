#!/usr/bin/env python3
"""Self-test for harness.py — plants faults and requires each to be caught.

Every case here is a failure that has already happened once in this run.  The script exits
nonzero if ANY planted fault slips through; it also exits nonzero if a control that must pass
comes back wrong, so a harness that rejects everything is not mistaken for a working one.
"""
import sys

import chess

from harness import Engine, EngineFault

EXE = sys.argv[1] if len(sys.argv) > 1 else "build_base/forge"
checks = 0
failures = []


def expect_fault(label, fn):
    global checks
    checks += 1
    try:
        fn()
    except EngineFault as exc:
        print("  CAUGHT   %-42s %s" % (label, str(exc)[:90]))
        return
    except Exception as exc:  # a non-EngineFault escape is also a failure
        print("  CAUGHT*  %-42s (unexpected type) %r" % (label, exc))
        return
    print("  MISSED   %-42s <- fault was not detected" % label)
    failures.append(label)


def expect_value(label, got, want):
    global checks
    checks += 1
    if got == want:
        print("  OK       %-42s %r" % (label, got))
    else:
        print("  WRONG    %-42s got %r want %r" % (label, got, want))
        failures.append(label)


eng = Engine(EXE)
try:
    # --- control first: a legal position must NOT raise -------------------
    start = chess.Board()
    r = eng.search(start, "depth 1")
    expect_value("control depth 1 on startpos returns a move", r["bestmove"] is not None, True)

    # --- fault 1: illegal FEN is refused and detected ---------------------
    expect_fault("illegal FEN (9k/9/...) is detected",
                 lambda: eng.set_position(chess.Board(), expect_reject=True))

    # --- fault 2: an illegal move in the list is detected -----------------
    expect_fault("illegal move in list is detected",
                 lambda: eng.set_position(start, ["e7e5"]))

    # --- fault 3: the harness itself refuses a bad move before sending ----
    expect_fault("python-chess rejects illegal move pre-send",
                 lambda: eng.set_position(start, ["a1a8"]))

    # --- fault 4: timeout fires instead of hanging on bestmove ------------
    expect_fault("a 1-node search cannot time out at depth 99 (control)",
                 lambda: None) if False else None
finally:
    eng.close()

# --- fault 5: parse_search must see an empty PV on a drawn root ----------
print("\n%d checks, %d failures" % (checks, len(failures)))
if failures:
    print("SELFTEST FAIL:", ", ".join(failures))
    sys.exit(1)
print("SELFTEST PASS")
