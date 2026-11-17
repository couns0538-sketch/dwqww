"""Test 2b: symmetry at scale, on pseudo-random legal positions.

Twenty hand-picked positions is too small to conclude that the evaluation is
symmetric. This test generates positions from random legal play out of several
openings, so the corpus is not chosen by hand and cannot be biased toward
positions the evaluator happens to like.

Deterministic: the seed is fixed and printed, so the exact corpus is
reproducible.
"""

from __future__ import annotations

import json
import random
import sys

import chess

from harness import Forge, mirror_board, verify_mirror

SEED = 7502
COUNT = 400
OPENINGS = [
    chess.STARTING_FEN,
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    "rnbqkb1r/pp2pppp/3p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "rnbqkbnr/ppp2ppp/8/3pp3/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 4",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
]


def random_positions(rng: random.Random, count: int) -> list[chess.Board]:
    out: list[chess.Board] = []
    guard = 0
    while len(out) < count and guard < count * 200:
        guard += 1
        board = chess.Board(rng.choice(OPENINGS))
        plies = rng.randint(0, 40)
        for _ in range(plies):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        # Only positions where both sides still have a king and the board is
        # legal are usable; the mirror of an illegal board is meaningless.
        if not board.is_valid():
            continue
        if board.is_game_over():
            continue
        out.append(board.copy())
    return out


def main() -> int:
    rng = random.Random(SEED)
    boards = random_positions(rng, COUNT)
    rows: list[dict] = []
    asymmetric: list[dict] = []
    skipped = 0

    with Forge() as f:
        for board in boards:
            try:
                verify_mirror(board)
            except Exception:  # noqa: BLE001
                skipped += 1
                continue
            mirrored = mirror_board(board)
            ev = f.evaluate(board)
            ev_m = f.evaluate(mirrored)
            row = {
                "fen": board.fen(), "mirror_fen": mirrored.fen(),
                "total": ev["total"], "mirror_total": ev_m["total"],
                "hce": ev["hce"], "mirror_hce": ev_m["hce"],
                "nnue": ev["nnue"], "mirror_nnue": ev_m["nnue"],
            }
            rows.append(row)
            if ev["total"] != ev_m["total"]:
                asymmetric.append(row)

    print(f"seed={SEED} generated={len(boards)} compared={len(rows)} skipped={skipped}")
    print(f"ASYM_PAIRS {len(asymmetric)} / {len(rows)}")
    for row in asymmetric[:10]:
        print(f"  ASYM {row['fen']}")
        print(f"       {row['mirror_fen']}")
        print(f"       total {row['total']} vs {row['mirror_total']} "
              f"(hce {row['hce']}/{row['mirror_hce']} nnue {row['nnue']}/{row['mirror_nnue']})")

    with open("out_symmetry_scale.json", "w") as fh:
        json.dump({"seed": SEED, "generated": len(boards), "compared": len(rows),
                   "skipped": skipped, "asymmetric_count": len(asymmetric),
                   "asymmetric": asymmetric}, fh, indent=2)
    return 0 if not asymmetric else 1


if __name__ == "__main__":
    sys.exit(main())
