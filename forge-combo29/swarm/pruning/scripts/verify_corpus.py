#!/usr/bin/env python3
"""Validate every corpus fixture twice, per brief rule 4.

"Validate every fixture with python-chess AND check the engine did not refuse
it (`invalid FEN` is reported on the `position` command, not in the search
output)."

A refused FEN manufactures a pass: the engine searches startpos (or whatever it
last held) and every downstream comparison is between the wrong boards. This
script fails loudly instead.

Also re-derives each entry's distance and mating-move set from the oracles, so a
hand-edited corpus cannot drift from its stated ground truth.
"""

from __future__ import annotations

import json
import sys

import chess

sys.path.insert(0, "scripts")
import mateoracle as mo  # noqa: E402
from ucidrv import Engine, FenRefused, check_fen  # noqa: E402


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "corpus/mates.json"
    with open(path) as fh:
        data = json.load(fh)
    entries = data["entries"]

    failures: list[str] = []
    engine = Engine("build/clean/forge", {"Threads": "1", "Hash": "16", "OwnBook": "false"})
    try:
        for i, e in enumerate(entries):
            fen = e["fen"]
            tag = f"[{i}] {fen}"

            # 1. python-chess must parse it, and the round-trip must be stable.
            try:
                board = chess.Board(fen)
            except ValueError as exc:
                failures.append(f"{tag}: python-chess rejected it: {exc}")
                continue
            if board.status() != chess.STATUS_VALID:
                failures.append(f"{tag}: python-chess status {board.status()}")
                continue
            if not board.is_valid():
                failures.append(f"{tag}: board.is_valid() false")
                continue

            # 2. The ENGINE must not refuse it. This is the half a python-chess
            #    check alone would miss.
            try:
                check_fen(engine, fen)
            except FenRefused as exc:
                failures.append(f"{tag}: ENGINE REFUSED: {exc}")
                continue

            # 3. A cheap independent confirmation the engine holds the FEN we sent:
            #    re-send it and require isready to be reached with no complaint.
            #    (This engine has no `d` command; asking for one would hang the
            #    read, which is how a harness manufactures a timeout "result".)
            check_fen(engine, fen)

            # 4. Re-derive the distance; the stored value must match BOTH oracles.
            a = mo.solve_negamax(board, e["plies"])
            c = mo.solve_layered(board, e["plies"])
            if a != c:
                failures.append(f"{tag}: oracles disagree: negamax={a} layered={c}")
            elif a != e["plies"]:
                failures.append(f"{tag}: stored plies={e['plies']} but oracles say {a}")

            # 5. Every listed mating move must genuinely mate in that distance,
            #    and the set must be complete.
            live = {m.uci() for m in mo.mating_moves(board, e["plies"])}
            stored = {m["uci"] for m in e["mating_moves"]}
            if live != stored:
                failures.append(f"{tag}: mating-move set drifted: "
                                f"only-live={sorted(live - stored)} "
                                f"only-stored={sorted(stored - live)}")
    finally:
        engine.close()

    print(json.dumps({"checked": len(entries), "failures": failures[:40],
                      "failure_count": len(failures)}, indent=2))
    if failures:
        print("\nFAIL -- do not measure on this corpus until it is clean.", file=sys.stderr)
        return 1
    print(f"\nOK -- {len(entries)} fixtures parse in python-chess, are accepted by the "
          f"engine, and match both oracles on distance and mating moves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
