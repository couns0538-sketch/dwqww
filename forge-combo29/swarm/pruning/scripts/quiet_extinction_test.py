#!/usr/bin/env python3
"""Does QuietExtinction lose a forced mate?

`QuietExtinction` is OFF by default, like `SoundMatePruning`, so it is tested by
ENABLING it. Its mechanism is narrower and more mate-relevant than the rest of
the pruning set:

  After TWO quiet moves miss alpha by >= QuietWideGap, `close_quiet_tail()` drops
  every remaining non-checking quiet move at that node. A late QUIET mating move
  is therefore never searched. Before that, one wide miss halves the futility
  slack for later ordinary quiets (`futility_tight`), which is a second chance to
  drop the same move.

That is the sharpest mate-safety question in the prune set, because a mating move
that is neither a check nor a capture is exactly the move ordering tends to put
late and exactly the move this rule discards.

Three measurements here:
  1. the counter evidence that the rule FIRES (quiet_tail_closed > 0), without
     which a clean result would be vacuous;
  2. corpus rate: fixtures x depths, four states, per depth;
  3. dedicated fixtures where the mating move is UNIQUE and QUIET, including a
     verified mate in 7 searched to depth 20.
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, "scripts")
from ucidrv import Engine, check_fen  # noqa: E402

DEPTHS = [6, 7, 8, 9, 10, 11, 12, 13, 14, 16]

# Fixtures whose mating move is unique and verified by three solvers.
# (fen, true mate in moves, the unique mating move)
DEDICATED = [
    ("8/8/8/8/8/8/6KQ/4k3 w - - 0 1", 3, "g2f3"),      # quiet K move
    ("8/8/8/8/8/K7/3R4/1k6 w - - 0 1", 3, "a3b3"),     # quiet K move
    ("K7/8/8/8/8/8/7k/Q7 w - - 0 1", 7, "a1g7"),       # mate in 7, QUIET queen move
]


def run(engine: Engine, fen: str, depth: int, quiet_extinction: bool) -> tuple[str, int | None, int | None]:
    engine.newgame()
    engine.setoption("QuietExtinction", "true" if quiet_extinction else "false")
    check_fen(engine, fen)
    r = engine.go(f"depth {depth}")
    last = r.last
    return (r.bestmove,
            last.score_mate if last else None,
            last.score_cp if last else None)


def stats(engine: Engine) -> dict:
    engine.send("probestats")
    line = engine._read_until(lambda l: l.startswith("probestats"))[-1]
    return json.loads(line[len("probestats"):])


def main() -> int:
    with open("corpus/mates.json") as fh:
        entries = json.load(fh)["entries"]

    engine = Engine("build/probe/forge", {"Threads": "1", "Hash": "64",
                                          "OwnBook": "false", "QuietExtinction": "false"})
    out = {"corpus": [], "dedicated": [], "counters": {}}

    try:
        # ---- 1. counters fire ----
        # Measured on the DEDICATED deep fixtures, not on corpus entries[:8].
        # The first eight corpus entries are mates in one, where the search
        # resolves the position and the quiet tail never closes; sampling those
        # gave quiet_tail_closed = 0 and would have supported a vacuous
        # "the rule never fires" claim. This is the kill-condition check, so it
        # must run on positions where the rule is reachable.
        maxc = {}
        for fen, _want, _only in DEDICATED:
            for d in (8, 10, 12):
                engine.newgame()
                engine.setoption("QuietExtinction", "true")
                check_fen(engine, fen)
                engine.go(f"depth {d}")
                s = stats(engine)
                for k in ("quiet_tail_closed", "futility_tight_set", "extinguish_futility_skip"):
                    maxc[k] = max(maxc.get(k, 0), s.get(k, 0))
        out["counters"] = maxc

        # ---- 2. corpus rate ----
        for e in entries:
            fen, want = e["fen"], e["moves_to_mate"]
            mating = {m["uci"] for m in e["mating_moves"]}
            for d in DEPTHS:
                a = run(engine, fen, d, False)
                b = run(engine, fen, d, True)
                ok = lambda t: t[0] in mating and t[1] == want
                state = ("HARM" if ok(a) and not ok(b) else
                         "help" if ok(b) and not ok(a) else
                         "both-right" if ok(a) and ok(b) else "both-wrong")
                out["corpus"].append({"fen": fen, "depth": d, "true_moves": want,
                                      "off": a, "on": b, "state": state})

        # ---- 3. dedicated unique-quiet-mating fixtures ----
        for fen, want, only in DEDICATED:
            row = {"fen": fen, "true_moves": want, "only_mating_move": only, "cells": {}}
            for d in DEPTHS:
                a = run(engine, fen, d, False)
                b = run(engine, fen, d, True)
                # Move-level correctness: with a UNIQUE mating move, the move is
                # either right or wrong regardless of what score is reported.
                move_harm = (a[0] == only) and (b[0] != only)
                row["cells"][str(d)] = {"off": a, "on": b, "move_harm": move_harm}
            out["dedicated"].append(row)
            print(f"{fen[:38]:40s} " + " ".join(
                f"d{d}:{'HARM' if row['cells'][str(d)]['move_harm'] else 'ok'}" for d in DEPTHS),
                flush=True)
    finally:
        engine.close()

    with open("evidence/quiet_extinction.json", "w") as fh:
        json.dump(out, fh, indent=1)

    from collections import Counter
    states = Counter(r["state"] for r in out["corpus"])
    harm_depths = sorted({r["depth"] for r in out["corpus"] if r["state"] == "HARM"})
    move_harm_cells = [(r["fen"], d) for r in out["dedicated"]
                       for d, c in r["cells"].items() if c["move_harm"]]
    print(json.dumps({
        "counters_max": out["counters"],
        "corpus_cells": len(out["corpus"]),
        "states": dict(states),
        "harm_depths": harm_depths,
        "dedicated_move_harm_cells": move_harm_cells,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
