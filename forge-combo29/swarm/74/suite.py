"""Standard perft suite from the Chess Programming Wiki, engine vs published counts.

Published values are the CPW perft-results page:
  https://www.chessprogramming.org/Perft_Results

Reference discipline: the PUBLISHED count is the reference for every cell, so a
depth-6 cell costs the engine one run rather than billions of Python nodes.
python-chess is used for the two cheap jobs it is good at: validating each FEN,
and independently re-deriving the counts at the shallow depths (<= CROSS_MAX,
with a node budget) so the published table itself is not taken on faith.

Every cell is gated by uci_perft.check_position: FEN validated by python-chess,
position reply scanned for the engine's invalid-FEN diagnostic, and board
identity proved by perft 1 and perft 2 against python-chess before the deep run.

Usage: python3 suite.py <engine-binary> [--json out.json]
"""

from __future__ import annotations

import json
import sys
import time

from uci_perft import Engine, EngineError, FenRejected, check_position, py_divide, py_perft

POSITIONS: list[tuple[str, str, dict[int, int]]] = [
    (
        "startpos",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        {1: 20, 2: 400, 3: 8902, 4: 197281, 5: 4865609, 6: 119060324},
    ),
    (
        "kiwipete",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        {1: 48, 2: 2039, 3: 97862, 4: 4085603, 5: 193690690, 6: 8031647685},
    ),
    (
        "position3",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        {1: 14, 2: 191, 3: 2812, 4: 43238, 5: 674624, 6: 11030083, 7: 178633661},
    ),
    (
        "position4",
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
        {1: 6, 2: 264, 3: 9467, 4: 422333, 5: 15833292, 6: 706045033},
    ),
    (
        "position4-mirror",
        "r2q1rk1/pP1p2pp/Q4n2/bbp1p3/Np6/1B3NBn/pPPP1PPP/R3K2R b KQ - 0 1",
        {1: 6, 2: 264, 3: 9467, 4: 422333, 5: 15833292, 6: 706045033},
    ),
    (
        "position5",
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
        {1: 44, 2: 1486, 3: 62379, 4: 2103487, 5: 89941194},
    ),
    (
        "position6",
        "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
        {1: 46, 2: 2079, 3: 89890, 4: 3894594, 5: 164075551, 6: 6923051137},
    ),
]

# python-chess re-derives counts only up to this depth and node budget.
CROSS_MAX_DEPTH = 4
CROSS_MAX_NODES = 5_000_000


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "build-swarm74/forge"
    out_json = None
    if "--json" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json") + 1]

    engine = Engine(binary)
    rows: list[dict] = []
    mismatches = 0
    refused = 0
    crosschecked = 0
    try:
        for name, fen, depths in POSITIONS:
            for depth, published in sorted(depths.items()):
                t0 = time.time()
                cheap = depth <= CROSS_MAX_DEPTH and published <= CROSS_MAX_NODES
                try:
                    cell = check_position(
                        engine, name, fen, depth, expect=published, py_reference=cheap
                    )
                except (FenRejected, EngineError) as exc:
                    print(f"{name:16s} d{depth}: HARNESS REFUSED -- {exc}")
                    rows.append(
                        {
                            "position": name,
                            "depth": depth,
                            "published": published,
                            "measured": None,
                            "ok": False,
                            "refused": str(exc),
                        }
                    )
                    refused += 1
                    continue
                dt = time.time() - t0
                status = "ok" if cell.ok else "MISMATCH"
                if not cell.ok:
                    mismatches += 1

                # Independent re-derivation of the published number, where cheap.
                cross = "not-run"
                if cheap:
                    import chess

                    indep = py_perft(chess.Board(fen), depth)
                    crosschecked += 1
                    cross = "agrees" if indep == published else f"DISAGREES({indep})"
                    if indep != published:
                        status += " PUBLISHED-UNSOUND"

                print(
                    f"{name:16s} d{depth}: published {published:>12d} "
                    f"measured {cell.engine:>12d}  {status:9s} {dt:6.2f}s  py[{cross}]"
                )
                rows.append(
                    {
                        "position": name,
                        "depth": depth,
                        "published": published,
                        "measured": cell.engine,
                        "ok": cell.ok,
                        "python_crosscheck": cross,
                        "seconds": round(dt, 3),
                    }
                )
    finally:
        engine.close()

    print(
        f"cells compared: {len(rows)} | mismatches: {mismatches} | "
        f"harness-refused: {refused} | python-crosschecked: {crosschecked}"
    )
    if out_json:
        with open(out_json, "w") as handle:
            json.dump(rows, handle, indent=2)
    return 1 if (mismatches or refused) else 0


if __name__ == "__main__":
    sys.exit(main())
