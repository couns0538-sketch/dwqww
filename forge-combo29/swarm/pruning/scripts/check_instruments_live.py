#!/usr/bin/env python3
"""Prove each ablation switch and each counter is LIVE, not a dead control.

Brief rule 3: "A control that silently does nothing is worse than no control.
Prove every checker fires on a planted fault before you trust its clean run."

Four checks, all of which must pass before any mate result is trusted:

1. The corpus is actually being searched. Distinct FENs must give distinct node
   counts. This is the guard that caught a real harness bug: `ucinewgame`
   resets the board to startpos, so a `position fen` sent before it was
   silently discarded and four different positions all returned 13,102 nodes.
   A corpus of one repeated position would satisfy a naive counter check.

2. Every COUNTER fires. A counter stuck at 0 could be unwired rather than
   unreached, and "the path never ran" is exactly the kill condition.

3. Every ABLATION changes the search. If `ablate null_move` gave the same node
   count, the switch is a no-op and any "no mate lost under ablation" is
   vacuous. Checked per class on at least one position.

4. The CLEAN arm is reproducible at fixed depth on Threads 1. Without this, a
   difference in check 3 cannot be told from run-to-run noise.
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, "scripts")
from ucidrv import Engine, check_fen  # noqa: E402

# Chosen to exercise the whole prune set: tactical middlegames with captures,
# checks and quiets; a quiet endgame for singular/razor; a KQ-vs-K conversion
# where null move and razoring routinely fire.
POSITIONS = [
    ("tactical-middlegame", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"),
    ("sharp-sicilian", "r1bqkb1r/pp2pppp/2np1n2/8/2B1P3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 0 1"),
    ("quiet-endgame", "8/5pk1/6p1/7p/3P3P/5KP1/8/8 w - - 0 1"),
    ("krk-conversion", "8/8/8/4k3/8/4K3/8/R7 w - - 0 1"),
]

CLASSES = ["null_move", "razor", "rfp", "futility", "lmr", "singular"]
DEPTH = 10


def stats(engine: Engine) -> dict:
    engine.send("probestats")
    line = engine._read_until(lambda l: l.startswith("probestats"))[-1]
    return json.loads(line[len("probestats"):])


def search(engine: Engine, fen: str, ablate: str = "none") -> tuple[str, int, dict]:
    """newgame FIRST (it resets the board), then position, then go."""
    engine.newgame()
    check_fen(engine, fen)
    engine.send(f"ablate {ablate}")
    engine.isready()
    r = engine.go(f"depth {DEPTH}")
    s = stats(engine)
    return r.bestmove, r.nodes, s


def main() -> int:
    failures: list[str] = []
    report: dict = {"clean_nodes": {}, "counter_fires": {}, "ablation_effect": {}}

    engine = Engine("build/probe/forge", {"Threads": "1", "Hash": "64", "OwnBook": "false"})
    try:
        # ---- 1 + 2 + 4: corpus is live, counters fire, clean arm repeats ----
        seen: dict[str, int] = {}
        clean: dict[str, tuple[str, int]] = {}
        for name, fen in POSITIONS:
            m1, n1, s1 = search(engine, fen)
            m2, n2, _ = search(engine, fen)
            clean[name] = (m1, n1)
            report["clean_nodes"][name] = {"move": m1, "nodes": n1, "repeat_nodes": n2}
            if (m1, n1) != (m2, n2):
                failures.append(f"clean arm not reproducible on {name}: "
                                f"({m1},{n1}) vs ({m2},{n2})")
            for k, v in s1.items():
                if isinstance(v, int):
                    seen[k] = max(seen.get(k, 0), v)

        if len({n for _, n in clean.values()}) != len(POSITIONS):
            failures.append(f"positions are not distinct searches -- node counts "
                            f"{ {k: v[1] for k, v in clean.items()} }; the FEN is not "
                            f"reaching the board (ucinewgame resets it)")

        report["counter_fires"] = seen
        must_fire = ["null_try", "razor_entered", "rfp_cutoff", "block_skips",
                     "lmp_skipped_moves", "see_quiet_skip", "lmr_reduced",
                     "futility_quiet_skip", "see_noisy_skip", "singular_search", "nodes"]
        for k in must_fire:
            if seen.get(k, 0) == 0:
                failures.append(f"counter {k} never fired -- unwired, or the corpus "
                                f"cannot reach it")

        # ---- 3: every ablation changes the search ----
        for cls in CLASSES:
            changed: list[str] = []
            for name, fen in POSITIONS:
                base_move, base_nodes = clean[name]
                abl_move, abl_nodes, _ = search(engine, fen, cls)
                if (abl_move, abl_nodes) != (base_move, base_nodes):
                    changed.append(f"{name}: nodes {base_nodes}->{abl_nodes}, "
                                   f"move {base_move}->{abl_move}")
            report["ablation_effect"][cls] = changed
            if not changed:
                failures.append(f"ablate {cls} changed NOTHING on any position -- the "
                                f"switch is a no-op and any null under it is vacuous")
    finally:
        engine.close()

    report["failures"] = failures
    print(json.dumps(report, indent=2))
    if failures:
        print("\nFAIL", file=sys.stderr)
        return 1
    print("\nOK -- corpus live, every counter fired, every ablation moved the search.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
