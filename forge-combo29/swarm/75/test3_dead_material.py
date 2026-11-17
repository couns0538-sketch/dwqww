"""Test 3: dead material.

Five bare endings with a known verdict. The engine is measured twice: the
static evaluation (what the evaluator believes) and a fixed-depth search (what
the engine actually plays with). These differ, and the difference matters, so
both are reported.

Verdicts are the standard results for the strong side:
  K vs K     draw   - nothing to mate with
  KB vs K    draw   - one bishop cannot mate
  KN vs K    draw   - one knight cannot mate
  KNN vs K   draw   - two knights cannot force mate against correct defence
  KBN vs K   win    - a forced mate exists
A score of 0 matches a draw; a clearly positive score matches a win. A DRAW
scored as a win, or the KBN WIN scored as 0, is an error.

Boards are built programmatically and validated, never hand-typed: hand-typed
FENs were the single largest source of fixture faults earlier in this audit.
"""

from __future__ import annotations

import json
import sys

import chess

from harness import Forge, cold_search, parse_fen

DEPTH = 6


def build(white: dict[str, chess.PieceType], black: dict[str, chess.PieceType],
          stm: chess.Color = chess.WHITE) -> chess.Board:
    board = chess.Board(None)  # empty board
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    for square, ptype in white.items():
        board.set_piece_at(chess.parse_square(square), chess.Piece(ptype, chess.WHITE))
    for square, ptype in black.items():
        board.set_piece_at(chess.parse_square(square), chess.Piece(ptype, chess.BLACK))
    board.turn = stm
    if not board.is_valid():
        raise SystemExit(f"invalid constructed board: {board.fen()} status={board.status()}")
    return board


K, Q, R, B, N, P = (chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP,
                    chess.KNIGHT, chess.PAWN)

# (label, white extras, black extras, theory verdict, expected score class)
CASES = [
    ("K vs K", {}, {}, "draw", "zero"),
    ("KB vs K", {"c1": B}, {}, "draw", "zero"),
    ("KN vs K", {"b1": N}, {}, "draw", "zero"),
    ("KNN vs K", {"b1": N, "d1": N}, {}, "draw", "zero"),
    ("KBN vs K", {"b1": N, "c1": B}, {}, "win", "positive"),
    # Controls on the other side of the board, to prove the sign is not
    # accidentally tied to White.
    ("K vs KB", {}, {"c8": B}, "draw", "zero"),
    ("K vs KBN", {}, {"b8": N, "c8": B}, "win", "positive"),
]


def classify(score: int) -> str:
    if score == 0:
        return "zero"
    return "positive" if score > 0 else "negative"


def main() -> int:
    rows: list[dict] = []
    errors: list[dict] = []

    with Forge() as f:
        for label, white, black, verdict, expected in CASES:
            board = build(white, black)
            static = f.evaluate(board)
            # Cold: a warm TT shifts fixed-depth scores (see harness.cold_search).
            searched = cold_search(board, DEPTH)

            score_type = searched["score"]["type"]
            score_value = searched["score"]["value"]
            # A "mate 0" would be a different bug class entirely; keep it out of
            # the centipawn comparison rather than letting it read as 0.
            search_class = classify(score_value) if score_type == "cp" else "mate"

            strong_side = "White" if white else ("Black" if black else "neither")
            if expected == "zero":
                static_ok = classify(static["total"]) == "zero"
                search_ok = search_class == "zero"
            else:  # positive for the strong side
                sign_ok = (static["total"] > 0) if strong_side == "White" else (static["total"] < 0)
                static_ok = sign_ok and abs(static["total"]) > 100
                if strong_side == "White":
                    search_ok = search_class == "positive" or (score_type == "mate" and score_value > 0)
                else:
                    search_ok = search_class == "negative" or (score_type == "mate" and score_value < 0)

            row = {
                "case": label, "fen": board.fen(), "verdict": verdict,
                "strong_side": strong_side,
                "static_hce": static["hce"], "static_nnue": static["nnue"],
                "static_total": static["total"], "static_class": classify(static["total"]),
                "search_depth": DEPTH, "search_score": searched["score"],
                "search_class": search_class,
                "insufficient_material_flag": board.is_insufficient_material(),
                "static_matches_verdict": static_ok,
                "search_matches_verdict": search_ok,
            }
            rows.append(row)
            print(f"  {label:12s} verdict={verdict:5s} "
                  f"static={static['total']:6d} (hce {static['hce']:5d} nnue {static['nnue']:6d}) "
                  f"[{row['static_class']:8s}] "
                  f"d{DEPTH}={score_type} {score_value:5d} [{search_class:8s}]  "
                  f"{'ok' if static_ok and search_ok else 'ERROR'}")

            if not static_ok:
                errors.append({**row, "where": "static evaluation",
                               "why": f"scored {static['total']} ({row['static_class']}) "
                                      f"where theory says {verdict}"})
            if not search_ok:
                errors.append({**row, "where": f"search depth {DEPTH}",
                               "why": f"scored {score_type} {score_value} ({search_class}) "
                                      f"where theory says {verdict}"})

    with open("out_dead_material.json", "w") as fh:
        json.dump({"depth": DEPTH, "cases": rows, "errors": errors}, fh, indent=2)

    static_errors = [e for e in errors if e["where"] == "static evaluation"]
    search_errors = [e for e in errors if e["where"] != "static evaluation"]
    print()
    print(f"cases={len(rows)}")
    print(f"static_mismatches={len(static_errors)} / {len(rows)}")
    print(f"search_mismatches={len(search_errors)} / {len(rows)}")
    for err in errors:
        print(f"  ERROR [{err['where']}] {err['case']}: {err['why']}")
        print(f"        fen {err['fen']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
