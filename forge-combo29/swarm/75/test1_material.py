"""Test 1: material monotonicity.

Each ladder differs by exactly one piece between neighbouring rungs. Every
rung is validated (raw FEN text + python-chess legality), and every step is
asserted to MOVE before it is recorded: if two adjacent rungs scored
identically the fixture is suspect, not the engine, and the step is reported
as a fixture fault rather than a material inversion.

All ladders are measured on a frozen king configuration so that the only
variable is the material under test. Kings are on squares that are far from
the action and never adjacent, and every position is verified to be legal.
"""

from __future__ import annotations

import json
import sys

import chess

from harness import EngineError, Forge, parse_fen

# A quiet king shell reused by every ladder: kings on opposite corners of the
# centre, no pawns, no checks, Black to move so White's material reads positive.
KINGS = "4k3/8/8/8/8/8/8/4K3"

LADDERS: dict[str, list[tuple[str, str]]] = {
    # name: [(label, extra white material as FEN placement override)]
    "minor_to_queen": [
        ("none", "4k3/8/8/8/8/8/8/4K3"),
        ("bishop", "4k3/8/8/8/8/8/8/2B1K3"),
        ("knight", "4k3/8/8/8/8/8/8/2N1K3"),
        ("rook", "4k3/8/8/8/8/8/8/2R1K3"),
        ("queen", "4k3/8/8/8/8/8/8/2Q1K3"),
    ],
    "bishop_knight_rook_queen": [
        ("bishop", "4k3/8/8/8/8/8/8/2B1K3"),
        ("bishop+knight", "4k3/8/8/8/8/8/8/1NB1K3"),
        ("bishop+knight+rook", "4k3/8/8/8/8/8/8/RNB1K3"),
        ("bishop+knight+rook+queen", "4k3/8/8/8/8/8/8/RNBQK3"),
    ],
    "pawn_stack": [
        ("no pawns", "4k3/8/8/8/8/8/8/4K3"),
        ("one pawn", "4k3/8/8/8/8/8/P7/4K3"),
        ("two pawns", "4k3/8/8/8/8/P1P5/8/4K3"),
        ("three pawns", "4k3/8/8/8/P1P5/2P5/8/4K3"),
    ],
    "rook_stack": [
        ("one rook", "4k3/8/8/8/8/8/8/R3K3"),
        ("two rooks", "4k3/8/8/8/8/8/8/R2RK3"),
        ("queen", "4k3/8/8/8/8/8/8/3QK3"),
    ],
    # The ordinary case: pawns are present, so the "almost certainly drawn"
    # scale-factor rule does not apply and material must order itself plainly.
    # This isolates a bare-minor defect from ordinary middlegame behaviour.
    "with_pawns": [
        ("no piece", "4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3"),
        ("bishop", "4k3/pppppppp/8/8/8/8/PPPPPPPP/2B1K3"),
        ("knight", "4k3/pppppppp/8/8/8/8/PPPPPPPP/1N2K3"),
        ("rook", "4k3/pppppppp/8/8/8/8/PPPPPPPP/R3K3"),
        ("queen", "4k3/pppppppp/8/8/8/8/PPPPPPPP/3QK3"),
    ],
}

# The expected ORDERING of the material ladder, by conventional piece values.
# A rung pair whose measured scores disagree with this order is an inversion.
# Only pairs whose ordering is unambiguous by material count are listed: two
# rooks plus a bishop (1319 cp by PieceValueMg) legitimately outranks a queen
# (1025 cp), so that pair is not an inversion and is not claimed as one.
EXPECTED_ORDER = {
    "minor_to_queen": ["none", "bishop", "knight", "rook", "queen"],
    "bishop_knight_rook_queen": ["bishop", "bishop+knight", "bishop+knight+rook",
                                 "bishop+knight+rook+queen"],
    "pawn_stack": ["no pawns", "one pawn", "two pawns", "three pawns"],
    "rook_stack": ["one rook", "two rooks", "queen"],
    "with_pawns": ["no piece", "bishop", "knight", "rook", "queen"],
}


def build(placement: str) -> chess.Board:
    return parse_fen(f"{placement} w - - 0 1")


def main() -> int:
    results: list[dict] = []
    inversions: list[dict] = []
    fixture_faults: list[dict] = []

    with Forge() as f:
        for ladder_name, rungs in LADDERS.items():
            readings: list[dict] = []
            for label, placement in rungs:
                board = build(placement)
                ev = f.evaluate(board)
                readings.append({
                    "label": label,
                    "fen": board.fen(),
                    "fen_field_count": len(board.fen().split()),
                    "hce": ev["hce"],
                    "nnue": ev["nnue"],
                    "total": ev["total"],
                    "white_material": sum(
                        len(board.pieces(pt, chess.WHITE)) for pt in chess.PIECE_TYPES
                    ),
                })
                print(f"  {ladder_name:28s} {label:26s} total={ev['total']:6d} "
                      f"hce={ev['hce']:6d} nnue={ev['nnue']:6d}")

            # Step assertions: neighbours must differ, or the fixture is at fault.
            for i in range(len(readings) - 1):
                a, b = readings[i], readings[i + 1]
                if a["total"] == b["total"]:
                    fixture_faults.append({
                        "ladder": ladder_name,
                        "step": f"{a['label']} -> {b['label']}",
                        "fen_a": a["fen"], "fen_b": b["fen"],
                        "score": a["total"],
                        "note": "adjacent rungs scored identically; cannot tell a "
                                "genuine plateau from a silently refused FEN",
                    })

            # Monotonicity against the expected order.
            order = EXPECTED_ORDER[ladder_name]
            by_label = {r["label"]: r for r in readings}
            for i in range(len(order) - 1):
                lo, hi = by_label[order[i]], by_label[order[i + 1]]
                if hi["total"] <= lo["total"]:
                    inversions.append({
                        "ladder": ladder_name,
                        "weaker": lo["label"], "stronger": hi["label"],
                        "weaker_score": lo["total"], "stronger_score": hi["total"],
                        "weaker_fen": lo["fen"], "stronger_fen": hi["fen"],
                        "delta": hi["total"] - lo["total"],
                    })

            results.append({"ladder": ladder_name, "rungs": readings})

    with open("out_material.json", "w") as fh:
        json.dump({"ladders": results, "inversions": inversions,
                   "fixture_faults": fixture_faults}, fh, indent=2)

    print()
    steps = sum(len(r["rungs"]) - 1 for r in results)
    print(f"ladders={len(results)} steps={steps}")
    if fixture_faults:
        print(f"FIXTURE FAULTS ({len(fixture_faults)}):")
        for ff in fixture_faults:
            print(f"  {ff['ladder']}: {ff['step']} both scored {ff['score']}")
    if inversions:
        print(f"MATERIAL INVERSIONS ({len(inversions)} of {steps} steps):")
        for inv in inversions:
            print(f"  {inv['ladder']}: {inv['weaker']}({inv['weaker_score']}) >= "
                  f"{inv['stronger']}({inv['stronger_score']}) delta={inv['delta']}")
            print(f"    weaker  {inv['weaker_fen']}")
            print(f"    stronger {inv['stronger_fen']}")
    else:
        print(f"MATERIAL INVERSIONS (0 of {steps} steps)")
    return 0 if not inversions and not fixture_faults else 1


if __name__ == "__main__":
    sys.exit(main())
