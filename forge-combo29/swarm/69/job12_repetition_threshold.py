"""JOB 12: at what repetition count does the answer change, and how large is the harm?

Job 11b showed `position fen` and `position startpos moves` diverge once the move list
contains a threefold. That leaves the exposure question open, and exposure is what matters
to the other seats: a harness that replays a real game only sees this if its games contain
the repetition count that triggers it.

So this job finds the THRESHOLD. It builds move lists reaching the same board with exactly
1, 2 and 3 prior occurrences of that position (asserted with python-chess, not assumed) and
compares all three against the FEN form, on both builds.

  * If 2 occurrences is enough, the exposure is much wider than "threefold" suggests,
    because a 2-fold is common in any game where a piece shuffles once.
  * If 3 is required, exposure is limited to genuinely drawn shuffling games.

It also measures the HARM rather than just the divergence: the base build's answer on a
repetition root is compared against an engine-independent value for the position, so the
size of the error is stated in centipawns and not just "it differs".

The engine-independent reference is a deep search of the SAME board from the FEN form, which
carries no history — that is the position's value absent any draw claim. A large gap between
that and the move-list answer is the measurement error a replaying harness inherits.
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


def run(exe, moves, fen, budget=BUDGET):
    engine = ucih.Engine(exe, timeout=600)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        if moves is not None:
            engine.position_startpos(moves)
        else:
            engine.position_fen(fen)
        return key(engine.go(budget))
    finally:
        engine.close()


def occurrences(board, target_key):
    """How many times the target position occurs in the game history, this one included."""
    count = 0
    seen = []
    probe = board.copy()
    while True:
        seen.append(probe._transposition_key())
        if not probe.move_stack:
            break
        probe.pop()
    return sum(1 for k in seen if k == target_key)


def build(reps):
    """A move list whose final position has occurred `reps` times in total."""
    board = chess.Board()
    moves = []
    for _ in range(reps - 1):
        for uci in CYCLE:
            board.push(chess.Move.from_uci(uci))
            moves.append(uci)
    target_key = board._transposition_key()
    got = occurrences(board, target_key)
    assert got == reps, "built %d occurrences, wanted %d" % (got, reps)
    return moves, board.fen(), reps


def main():
    print("=== JOB 12: repetition THRESHOLD for the fen/moves divergence ===")
    print("budget %s, Threads 1, Hash 16\n" % BUDGET)

    rows = []
    for reps in (1, 2, 3):
        moves, fen, n = build(reps)
        board = chess.Board(fen)
        threefold = board.is_repetition(3)
        twofold = board.is_repetition(2)
        print("occurrences in history: %d   (python-chess: 2-fold %s, 3-fold %s)"
              % (n, twofold, threefold))
        print("   board: %s" % fen)
        for exe, name in ((BASE_EXE, "base"), (PC_EXE, "pc")):
            via_moves = run(exe, moves, None)
            via_fen = run(exe, None, fen)
            print("   %-4s moves %-36s fen %-36s %s"
                  % (name, via_moves, via_fen, "same" if via_moves == via_fen else "DIFFERS"))
            rows.append({"occurrences": n, "build": name, "fen": fen,
                         "twofold": twofold, "threefold": threefold,
                         "via_moves": list(via_moves), "via_fen": list(via_fen),
                         "same": via_moves == via_fen})
        print()

    # The threshold: smallest occurrence count at which either build diverges.
    diverging = sorted({r["occurrences"] for r in rows if not r["same"]})
    print("smallest occurrence count that diverges: %s"
          % (diverging[0] if diverging else "none in 1..3"))

    # The harm, stated in centipawns.
    print("\n-- size of the harm on the base build --")
    harm = []
    for r in rows:
        if r["build"] != "base":
            continue
        via = r["via_moves"]
        ref = r["via_fen"]
        try:
            delta = int(via[2].split()[1]) - int(ref[2].split()[1])
        except (IndexError, ValueError):
            delta = None
        harm.append({"occurrences": r["occurrences"], "moves_score": via[2],
                     "fen_score": ref[2], "delta_cp": delta,
                     "moves_best": via[1], "fen_best": ref[1]})
        print("   occurrences %d: moves %-8s (%s) vs fen %-8s (%s)  delta %s cp, bestmove %s vs %s"
              % (r["occurrences"], via[2], via[1], ref[2], ref[1], delta, via[1], ref[1]))

    # Is the base's zero-node answer the drawn-root bail? Report nodes as the tell.
    print("\n-- the tell: node count --")
    for r in rows:
        if r["build"] == "base" and not r["same"]:
            print("   occurrences %d: base via moves reports %d nodes (0 = the drawn-root bail "
                  "that publishes root_candidates.front() without scoring)" % (r["occurrences"], r["via_moves"][0]))

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job12/repetition_threshold.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as handle:
        json.dump({"budget": BUDGET, "rows": rows, "harm": harm,
                   "smallest_diverging": diverging[0] if diverging else None},
                  handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
