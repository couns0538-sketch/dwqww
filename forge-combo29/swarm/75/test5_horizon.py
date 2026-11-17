"""Test 5: the horizon - does the score approach the true value with depth?

A fixed material imbalance is searched to increasing depth. If the evaluation
is sane and the search converges, the score should move toward the imbalance's
true value and then settle, rather than drift or oscillate wildly.

The reference value printed alongside is NOT a ground truth: bare chess has no
oracle for "the true value of a queen up". It is the material count in the
engine's own piece values, which is what the score should approach once search
has exhausted the tactical tricks available. Deviations are reported, not
asserted away.

Both sides are measured so a sign or tempo artefact cannot be mistaken for
convergence.
"""

from __future__ import annotations

import json
import sys

import chess

from harness import Forge, cold_search, parse_fen

DEPTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Piece values the engine itself uses for pruning (include/forge/eval.hpp).
PIECE_MG = {chess.PAWN: 82, chess.KNIGHT: 337, chess.BISHOP: 365,
            chess.ROOK: 477, chess.QUEEN: 1025}

POSITIONS = [
    # A clean imbalance with no immediate tactics: extra queen, pawns intact.
    ("white queen up",
     "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", chess.WHITE),
    # The mirror, so the ladder is measured from both sides.
    ("black queen up",
     "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1", chess.BLACK),
    # A smaller imbalance, to check the ladder scales rather than saturates.
    # Black's a8 rook is missing, so Black loses castling rights on that side
    # and the FEN says so; a FEN claiming Q or q here would be illegal.
    ("white rook up",
     "1nbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQk - 0 1", chess.WHITE),
]


def material_balance(board: chess.Board) -> int:
    total = 0
    for ptype, value in PIECE_MG.items():
        total += (len(board.pieces(ptype, chess.WHITE))
                  - len(board.pieces(ptype, chess.BLACK))) * value
    return total


def main() -> int:
    ladders: list[dict] = []

    with Forge() as f:
        for name, fen, strong in POSITIONS:
            board = parse_fen(fen)
            balance = material_balance(board)
            # Reference is from White's point of view; scores are side-to-move
            # relative, so convert before comparing.
            reference = balance if board.turn == chess.WHITE else -balance
            scores: list[dict] = []
            for depth in DEPTHS:
                # Cold per depth: a TT carried between depths changes the score
                # at fixed nominal depth, so the ladder would measure the TT
                # rather than the horizon.
                res = cold_search(board, depth)
                score = res["score"]
                scores.append({"depth": depth, "type": score["type"],
                               "value": score["value"], "nodes": res["nodes"],
                               "bestmove": res["bestmove"]})
                print(f"  {name:16s} d{depth:<2d} {score['type']} {score['value']:6d} "
                      f"nodes={res['nodes']}")

            cps = [s["value"] for s in scores if s["type"] == "cp"]
            converged = bool(cps) and len(cps) >= 4 and abs(cps[-1] - cps[-2]) <= 30
            last = cps[-1] if cps else None
            ladders.append({
                "name": name, "fen": board.fen(), "material_balance_white": balance,
                "reference_stm_relative": reference, "scores": scores,
                "final_cp": last, "converged_last_two": converged,
                "delta_from_reference": (last - reference) if last is not None else None,
            })
            print(f"    reference(stm)={reference} final={last} "
                  f"delta={last - reference if last is not None else None:+d} "
                  f"settled={converged}")
            print()

    with open("out_horizon.json", "w") as fh:
        json.dump({"depths": DEPTHS, "ladders": ladders}, fh, indent=2)

    print(f"ladders={len(ladders)} depths_each={len(DEPTHS)}")
    unstable = [l for l in ladders if not l["converged_last_two"]]
    print(f"unsettled_at_last_step={len(unstable)} / {len(ladders)}")
    for l in ladders:
        print(f"  {l['name']:16s} d{DEPTHS[0]}..d{DEPTHS[-1]}: "
              f"{l['scores'][0]['value']} -> {l['final_cp']} "
              f"(reference {l['reference_stm_relative']}, "
              f"delta {l['delta_from_reference']:+d})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
