#!/usr/bin/env python3
"""Search for the board the §1b/3aa figures were measured on (depth1=41, depth5=896).

Node counts are position-dependent, so a cross-check of the seat's absolute
numbers needs the same FEN, which the findings document does not record. Rather
than assume, this walks random legal lines from startpos (legal moves read from
the engine's own `go perft 1`, so no reference library is needed) and reports any
board whose depth-1 search visits 41 nodes.

A board that matches makes the seat's row reproducible; no match means the row's
absolute numbers stay unverifiable and the finding rests on the shape instead.
"""

from __future__ import annotations

import random
import sys

from go_probe import Engine, run_cell


def legal_moves(exe: str, position: str) -> list[str]:
    engine = Engine(exe)
    try:
        engine.send("uci")
        engine.wait_for(lambda t: t == "uciok", 10.0)
        engine.send("isready")
        engine.wait_for(lambda t: t == "readyok", 10.0)
        engine.send("position " + position)
        engine.send("go perft 1")
        engine.wait_for(lambda t: t.startswith("nodes "), 30.0)
        moves = []
        for text in engine.since(0):
            parts = text.split(":")
            if len(parts) == 2 and parts[0].strip() and not parts[0].startswith(("nodes", "info")):
                moves.append(parts[0].strip())
        return moves
    finally:
        engine.close()


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/base/forge"
    want_d1 = int(sys.argv[2]) if len(sys.argv) > 2 else 41
    games = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    plies = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    found = []
    rng = random.Random(20261117)
    for g in range(games):
        moves: list[str] = []
        for _ in range(plies):
            position = "startpos" if not moves else "startpos moves " + " ".join(moves)
            options = legal_moves(exe, position)
            if not options:
                break
            moves.append(rng.choice(options))
            position = "startpos moves " + " ".join(moves)
            cell = run_cell(exe, "go depth 1", position)
            if cell.last_nodes == want_d1:
                five = run_cell(exe, "go depth 5", position)
                found.append((position, five.last_nodes, five.bestmove))
                print(f"MATCH d1={cell.last_nodes} d5={five.last_nodes} bm={five.bestmove} {position}", flush=True)
        print(f"game {g}: {len(moves)} plies, {len(found)} matches", file=sys.stderr, flush=True)
    print(f"\n{len(found)} board(s) with depth-1 == {want_d1}")
    for position, d5, bm in found:
        print(f"  d5={d5} bm={bm}  {position}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
