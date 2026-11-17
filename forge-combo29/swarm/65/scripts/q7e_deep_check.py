#!/usr/bin/env python3
"""Deep re-check of the book moves with the largest measured gap.

The depth-10 sweep flags one move above 100 cp and ten above 75 cp, but the
same measurement has a noise floor of a few cp (q7d_noise_floor.py) and the
forced-move score is itself a different search from the unrestricted one. So the
worst offenders are re-checked at several depths, with Clear Hash before every
search, and both the raw gap and the identity of the engine's preferred move are
recorded.

A move is only called unsound here if the gap survives at increasing depth. A gap
that collapses as depth grows is a horizon artifact, not a book defect.

Usage: q7e_deep_check.py [--depth 14] [--top 10]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402
from q7c_exhaustive_gap import search  # noqa: E402
from q7_soundness import parse_probe  # noqa: E402

# The offenders from the depth-10 sweep (fen, book move), worst first.
CANDIDATES = [
    ("r1bqk2r/pppnbppp/3p1n2/4p3/3PPP2/2N2N2/PPP1B1PP/R1BQK2R b KQkq - 4 6", "e8g8"),
    ("rnbqkbnr/ppp2ppp/3p4/4p3/4P3/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 3", "d2d4"),
    ("rnbqkbnr/pp2pppp/8/2pp4/3P4/2P2N2/PP2PPPP/RNBQKB1R b KQkq - 0 3", "b8c6"),
    ("rnbqkb1r/pp1p1ppp/4pn2/2P5/5B2/8/PPP1PPPP/RN1QKBNR w KQkq - 0 4", "g1f3"),
    ("rnbqkbnr/pppp1ppp/8/8/3pP3/2P5/PP3PPP/RNBQKBNR b KQkq - 0 3", "c7c5"),
    ("rnbqkb1r/1p2pppp/p4n2/2Pp4/5B2/2N1P3/PPP2PPP/R2QKBNR b KQkq - 0 5", "d8a5"),
    ("rnbqkb1r/pp1p1ppp/2p2n2/4p3/2P5/2N3P1/PP1PPP1P/R1BQKBNR w KQkq - 0 4", "d2d4"),
    ("rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq c3 0 2", "g8f6"),
    ("rnbqkbnr/pp2pppp/8/2pp4/3P4/2P2N2/PP2PPPP/RNBQKB1R b KQkq - 0 3", "g8f6"),
    ("r1bqkbnr/pppp1ppp/2n5/8/3NP3/8/PPP2PPP/RNBQKB1R b KQkq - 0 4", "f8c5"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", default="/tmp/build65/forge")
    ap.add_argument("--depths", default="10,14,18")
    ap.add_argument("--top", type=int, default=len(CANDIDATES))
    args = ap.parse_args()
    depths = [int(d) for d in args.depths.split(",")]

    eng = Engine(args.binary)
    eng.handshake()
    eng.newgame()
    eng.setoption("OwnBook", "false")

    print("| fen | book move | depth | score best | engine best | score forced | gap |")
    print("| --- | --- | ---: | ---: | --- | ---: | ---: |")
    try:
        for fen, move in CANDIDATES[: args.top]:
            for depth in depths:
                eng.setoption("Clear Hash", "")
                eng.position_checked(f"fen {fen}")
                reply = eng.go_and_wait(f"depth {depth}", timeout=120.0)
                lines = reply.info_depth_lines()
                best_lines = reply.bestmove_lines()
                if not lines or not best_lines or reply.timed_out:
                    print(f"| {fen} | {move} | {depth} | - | TIMEOUT | - | - |")
                    continue
                from q7b_verify import score_of
                best_score = score_of(lines[-1])
                engine_best = best_lines[0].split()[1]
                eng.setoption("Clear Hash", "")
                forced = search(eng, fen, depth, move)
                gap = best_score - forced if forced is not None else None
                print(f"| {fen} | {move} | {depth} | {best_score} | {engine_best} | {forced} | {gap} |")
    finally:
        eng.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
