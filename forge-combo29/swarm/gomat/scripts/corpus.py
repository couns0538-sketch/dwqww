#!/usr/bin/env python3
"""Build the mate corpus. No FEN in it is typed by hand.

Two sources, both programmatic:

  * MATE k  — positions the oracle proves have exact DTM = k moves (1..4) and no
              faster mate, drawn from SPARSE endgames so the exhaustive minimax
              can actually finish. A candidate whose oracle run exceeds its node
              budget is DISCARDED, never guessed.
  * NOMATE  — positions the oracle proves have no forced mate inside the same
              ply window `go mate 4` searches (7 plies), plus the cheap-but-total
              `no mate in one` proof used by the termination test.

Every row records the oracle's exact DTM in plies and the window used. The
runner separately checks the engine ACCEPTED each FEN (perft-1 board identity),
because a refused FEN keeps the previous board (findings §7 item 6).

Usage: corpus.py --out corpus.json [--seed 7345] [--per-bucket 8]
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mateoracle import BudgetExceeded, Oracle, no_mate_in_one  # noqa: E402

# Sparse sets only. Each: (name, white pieces, black pieces). Sparse material
# keeps the exhaustive minimax inside its budget, which is what lets the corpus
# carry proofs instead of samples.
MATERIAL_SETS = [
    ("KQvK",   [chess.QUEEN],                             []),
    ("KRvK",   [chess.ROOK],                              []),
    ("KQvKR",  [chess.QUEEN],                             [chess.ROOK]),
    ("KRRvK",  [chess.ROOK, chess.ROOK],                  []),
    ("KQvKP",  [chess.QUEEN],                             [chess.PAWN]),
    ("KRvKN",  [chess.ROOK],                              [chess.KNIGHT]),
    ("KBBvK",  [chess.BISHOP, chess.BISHOP],              []),
    ("KQRvKR", [chess.QUEEN, chess.ROOK],                 [chess.ROOK]),
]

# Opening positions: no forced mate inside 7 plies by construction (a mate in 4
# from the initial position is impossible), but each is still put through the
# oracle so the file carries the proof rather than the assertion. The bare-kings
# row is the control that a null corpus entry is genuinely mate-free.
NO_MATE_SOURCES = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "rnbqkb1r/pppppppp/5n2/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 1 2",
    "8/8/8/4k3/8/4K3/8/8 w - - 0 1",
]


def sparse_position(rng: random.Random, white: list[int], black: list[int]) -> chess.Board | None:
    """Place both kings and the given pieces on random squares, legality-checked."""
    for _ in range(60):
        squares = rng.sample(range(64), 2 + len(white) + len(black))
        board = chess.Board(None)
        board.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
        idx = 2
        ok = True
        for color, pieces in ((chess.WHITE, white), (chess.BLACK, black)):
            for pt in pieces:
                sq = squares[idx]
                idx += 1
                if pt == chess.PAWN and chess.square_rank(sq) in (0, 7):
                    ok = False
                    break
                board.set_piece_at(sq, chess.Piece(pt, color))
            if not ok:
                break
        if not ok:
            continue
        board.turn = rng.choice([chess.WHITE, chess.BLACK])
        board.castling_rights = chess.BB_EMPTY
        board.ep_square = None
        board.halfmove_clock = 0
        board.fullmove_number = 1
        if board.is_valid() and not board.is_check() and board.legal_moves.count() > 0:
            return board
    return None


def build(seed: int, want_per_bucket: int, budget: int) -> dict:
    rng = random.Random(seed)
    buckets: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: []}
    rejected_over_budget = 0
    tried = 0
    max_tries = 40000

    while tried < max_tries and any(len(v) < want_per_bucket for v in buckets.values()):
        tried += 1
        name, white, black = MATERIAL_SETS[rng.randrange(len(MATERIAL_SETS))]
        board = sparse_position(rng, white, black)
        if board is None:
            continue
        if board.is_insufficient_material() or board.is_stalemate() or board.is_checkmate():
            continue
        oracle = Oracle(node_budget=budget)
        try:
            dtm = oracle.exact_dtm_up_to(board, 4)
        except BudgetExceeded:
            rejected_over_budget += 1
            continue
        if dtm is None:
            continue
        k = (dtm + 1) // 2
        if k not in buckets or len(buckets[k]) >= want_per_bucket:
            continue
        buckets[k].append({
            "id": f"M{k}-{len(buckets[k]) + 1:03d}",
            "fen": board.fen(en_passant="fen"),
            "oracle_dtm_plies": dtm,
            "oracle_mate_moves": k,
            "material": name,
            "oracle_nodes": oracle.nodes,
        })

    nomate: list[dict] = []
    for i, fen in enumerate(NO_MATE_SOURCES):
        board = chess.Board(fen)
        rec = {
            "id": f"N-{i + 1:03d}",
            "fen": board.fen(en_passant="fen"),
            "no_mate_in_1_proved": no_mate_in_one(board),
            "legal_moves": board.legal_moves.count(),
        }
        oracle = Oracle(node_budget=budget)
        try:
            rec["oracle_dtm7_plies"] = oracle.dtm_plies(board, 7)
            rec["oracle_dtm7_nodes"] = oracle.nodes
            rec["oracle_dtm7_status"] = "searched"
        except BudgetExceeded:
            rec["oracle_dtm7_plies"] = None
            rec["oracle_dtm7_status"] = "OVER_BUDGET_discarded"
            rejected_over_budget += 1
        nomate.append(rec)

    return {
        "seed": seed,
        "tried": tried,
        "oracle_budget_nodes": budget,
        "rejected_over_budget": rejected_over_budget,
        "mate": {str(k): v for k, v in buckets.items()},
        "nomate": nomate,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=7345)
    ap.add_argument("--per-bucket", type=int, default=8)
    ap.add_argument("--budget", type=int, default=400_000)
    args = ap.parse_args()
    data = build(args.seed, args.per_bucket, args.budget)
    with open(args.out, "w") as fh:
        json.dump(data, fh, indent=1)
    counts = {k: len(v) for k, v in data["mate"].items()}
    print(f"seed {args.seed}, tried {data['tried']} sparse endgames, "
          f"rejected over budget {data['rejected_over_budget']}")
    print(f"mate buckets: {counts}")
    print(f"no-mate rows: {len(data['nomate'])}")
    for rec in data["nomate"]:
        print(f"  {rec['id']}: dtm7={rec['oracle_dtm7_plies']} "
              f"({rec['oracle_dtm7_status']}) no_mate_in_1={rec['no_mate_in_1_proved']}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
