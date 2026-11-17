"""JOB 8: is a piped-harness fabrication DETECTABLE by its move?

Job 1 found that closing stdin during a search makes the engine print zero `info depth`
lines and answer a legal but fabricated `bestmove`. The question the coordinator asks is
whether that move is:

  H1 always the same move (the generator's head, `root_candidates.front()`), so one
     glance at the output catches it; or
  H2 a per-position move, so the output looks like a plausible search result and a
     harness that only checks `bestmove` legality would accept it.

Method: for N positions, run the same `go depth 8` twice —
  (a) PIPED: `printf ... | forge`, stdin closed -> the fabrication;
  (b) DRIVER: the interactive driver -> the real answer.
Record both moves, whether they differ, and what the fabrication actually is relative to
python-chess's own legal move list in generation order (a proxy for "the head").

The decisive number is: of the positions where the real answer is NOT the first legal
move, how many fabrications still differ from the real answer, and how many fabrications
are the same single move across all positions.
"""

import json
import os
import subprocess
import sys

import chess

import ucih
from matrix import BASE_EXE

BUDGET = "go depth 8"
N_POS = 60
OPTIONS = [("Threads", 1), ("Hash", 16)]


def piped(fen):
    """The defect: commands on stdin, closed while the search runs."""
    script = "printf 'uci\\nisready\\nposition fen %s\\ngo depth 8\\n' | '%s'" % (fen, BASE_EXE)
    out = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=300)
    lines = out.stdout.splitlines()
    info = [l for l in lines if l.startswith("info depth ")]
    best = None
    for line in lines:
        if line.startswith("bestmove"):
            parts = line.split()
            if len(parts) >= 2:
                best = parts[1]
    return best, len(info)


def driven(fen):
    engine = ucih.Engine(BASE_EXE, timeout=300)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        engine.position_fen(fen)
        res = engine.go(BUDGET)
        return res["bestmove"], res["n_info"], res["nodes"]
    finally:
        engine.close()


def first_legal_move(fen):
    """python-chess's first legal move in its own order, not the engine's."""
    board = chess.Board(fen)
    for move in board.legal_moves:
        return move.uci()
    return None


def main():
    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid
    fens = valid[:N_POS]

    print("=== JOB 8: is the piped-EOF fabricated bestmove detectable? ===")
    print("budget %s, %d positions, Threads 1, Hash 16\n" % (BUDGET, len(fens)))

    rows = []
    for fen in fens:
        fab, fab_info = piped(fen)
        real, real_info, real_nodes = driven(fen)
        rows.append({
            "fen": fen,
            "fabricated": fab,
            "fabricated_info_lines": fab_info,
            "real": real,
            "real_info_lines": real_info,
            "real_nodes": real_nodes,
            "pc_first_legal": first_legal_move(fen),
            "matches_real": fab == real,
            "is_pc_first": fab == first_legal_move(fen),
        })

    fab_set = sorted({r["fabricated"] for r in rows})
    real_set = sorted({r["real"] for r in rows})
    same_as_real = [r for r in rows if r["matches_real"]]
    zero_info = [r for r in rows if r["fabricated_info_lines"] == 0]

    print("positions:                                   %d" % len(rows))
    print("fabrications with 0 `info depth` lines:      %d / %d" % (len(zero_info), len(rows)))
    print("distinct fabricated moves across positions:  %d  %s" % (len(fab_set), fab_set[:8]))
    print("distinct REAL moves across positions:        %d  %s" % (len(real_set), real_set[:8]))
    print("fabrication equals the real answer:          %d / %d" % (len(same_as_real), len(rows)))
    print("fabrication equals python-chess first legal: %d / %d"
          % (sum(1 for r in rows if r["is_pc_first"]), len(rows)))

    if len(fab_set) == 1:
        print("\n=> H1 CONFIRMED: the fabrication is the SAME move on every position (%s)."
              % fab_set[0])
        print("   A piped run is therefore detectable by its move alone.")
    else:
        print("\n=> H2: the fabrication VARIES by position (%d distinct). A harness that"
              % len(fab_set))
        print("   checks only that bestmove is legal would accept it.")

    # How often would a legality-only check have passed the fabrication?
    illegal = 0
    for r in rows:
        board = chess.Board(r["fen"])
        try:
            move = chess.Move.from_uci(r["fabricated"]) if r["fabricated"] else None
        except ValueError:
            move = None
        if move is None or move not in board.legal_moves:
            illegal += 1
    print("\nfabrications that a legality check would REJECT: %d / %d" % (illegal, len(rows)))
    print("fabrications that a legality check would ACCEPT: %d / %d"
          % (len(rows) - illegal, len(rows)))

    # The only reliable detector: the info line count.
    print("\nthe ONLY reliable detector is `info depth` line count == 0: %d / %d"
          % (len(zero_info), len(rows)))

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job8/piped_fabrication.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as handle:
        json.dump({"budget": BUDGET, "n": len(rows), "rows": rows}, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
