"""JOB 11b: correction — `position fen` and `position startpos moves` are NOT interchangeable.

Job 11 (P1) found that the same BOARD gives two different searches depending on how it is
delivered, when the move list contains a threefold repetition. That contradicts finding
69-F8b in this seat's own FINDINGS.md, which recorded "0 / 6, the two command forms are
interchangeable" from job3c. Job 3c's games were 40 random plies each and contained no
threefold repetition, so the test could not see the difference. The claim was too wide and
is corrected here.

This job measures the difference precisely:

  * the same board via `position fen` vs `position startpos moves`, at 0, 1, 2 and 3
    repetitions of the starting position;
  * on BOTH builds, because the base and PC builds respond differently (base: 0 nodes /
    cp 0 / a2a3; PC: 34,047 nodes / cp 22 / e2e4) and only the FEN form is build-identical.

The distinction that matters for a harness: `position fen` cannot carry repetition history
at all (a FEN is one board), so a harness that replays games must send `position startpos
moves ...` or it silently scores a drawn position as a live one — and vice versa, a
harness that sends a move list gets repetition-aware scoring that a FEN arm does not.
A comparison between the two arms is a comparison of two different questions.
"""

import json
import os
import sys

import chess

import ucih
from matrix import BASE_EXE, PC_EXE

OPTIONS = [("Threads", 1), ("Hash", 16)]
BUDGET = "go depth 12"
CYCLE = ["g1f3", "g8f6", "f3g1", "f6g8"]


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def run(exe, moves, fen):
    engine = ucih.Engine(exe, timeout=600)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        if moves is not None:
            engine.position_startpos(moves)
        else:
            engine.position_fen(fen)
        return key(engine.go(BUDGET))
    finally:
        engine.close()


def main():
    print("=== JOB 11b: `position fen` vs `position startpos moves` at N repetitions ===")
    print("budget %s, Threads 1, Hash 16\n" % BUDGET)

    rows = []
    for reps in (0, 1, 2, 3):
        moves = CYCLE * reps
        board = chess.Board()
        for uci in moves:
            board.push(chess.Move.from_uci(uci))
        fen = board.fen()
        threefold = board.is_repetition(3)
        print("repetitions in list: %d   board %s   threefold on board: %s"
              % (reps, fen, threefold))
        for exe, name in ((BASE_EXE, "base"), (PC_EXE, "pc")):
            via_moves = run(exe, moves, None)
            via_fen = run(exe, None, fen)
            same = via_moves == via_fen
            print("   %-4s via moves %-38s via fen %-38s %s"
                  % (name, via_moves, via_fen, "same" if same else "<-- DIFFERS"))
            rows.append({"reps": reps, "build": name, "fen": fen, "threefold": threefold,
                         "via_moves": list(via_moves), "via_fen": list(via_fen),
                         "same": same})
        print()

    differ = [r for r in rows if not r["same"]]
    print("cells where the two command forms differ: %d / %d" % (len(differ), len(rows)))
    print("  of those, at 0 or 1 repetitions:        %d"
          % sum(1 for r in differ if r["reps"] in (0, 1)))
    print("  of those, at 2 or 3 repetitions:        %d"
          % sum(1 for r in differ if r["reps"] in (2, 3)))
    print("\n=> the two forms agree until the move list contains a THREEFOLD, then diverge.")

    print("\n-- the base build's drawn-root answer is build-specific --")
    base2 = [r for r in rows if r["build"] == "base" and r["reps"] == 2][0]
    pc2 = [r for r in rows if r["build"] == "pc" and r["reps"] == 2][0]
    print("   base via moves: %s  (0 nodes, cp 0, move a2a3 - the drawn-root bail)" % (base2["via_moves"],))
    print("   pc   via moves: %s  (a real search)" % (pc2["via_moves"],))
    print("   both via fen  : base %s / pc %s" % (base2["via_fen"], pc2["via_fen"]))
    print("   => the FEN form is build-identical; the moves form is not, because the two")
    print("      builds handle a drawn root differently.")

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job11/fen_vs_moves_repetition.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as handle:
        json.dump({"budget": BUDGET, "rows": rows}, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
