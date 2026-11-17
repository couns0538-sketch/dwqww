"""Test 2: colour-mirror symmetry of the EVALUATION.

The brief states that search asymmetry across colour mirrors is fully
explained by move-generation order. This test isolates the evaluation from
move generation entirely: it calls the static `eval` command, which never
searches, so any asymmetry found here is an evaluation defect and cannot be a
movegen-order effect.

Every mirror is checked to be legal and to be an involution before it is used.
"""

from __future__ import annotations

import json
import sys

import chess

from harness import Forge, mirror_board, parse_fen, verify_mirror

# A spread of position types: opening, middlegame, endgame, bare endings,
# tactical, pawn structures, and both sides to move.
POSITIONS: list[tuple[str, str]] = [
    ("startpos", chess.STARTING_FEN),
    ("ruy lopez", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
    ("sicilian", "rnbqkb1r/pp2pppp/3p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("endgame rooks", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
    ("endgame pawns", "8/8/8/8/8/4k3/4p3/4K3 w - - 0 1"),
    ("queen vs rook", "8/8/4k3/8/8/8/4K3/3Q4 w - - 0 1"),
    ("opposite bishops", "8/8/8/3b4/8/2B5/4K1k1/8 w - - 0 1"),
    ("black to move", "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R b KQkq - 0 1"),
    ("promotion race", "8/P6k/8/8/8/8/6p1/K7 w - - 0 1"),
    ("dense middlegame", "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10"),
    ("pawn chain", "rnbqkbnr/ppp2ppp/8/3pp3/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 4"),
    ("knights", "8/8/4k3/8/2N1N3/8/4K3/8 w - - 0 1"),
    ("bare kings", "8/8/4k3/8/8/4K3/8/8 w - - 0 1"),
    ("bishop pair", "8/8/4k3/8/8/2BB4/4K3/8 w - - 0 1"),
    ("castled both", "r1bq1rk1/ppp2ppp/2n1bn2/3pp3/3PP3/2N1BN2/PPP2PPP/R2Q1RK1 w - - 0 8"),
    ("passed pawn", "8/5p2/4k3/8/4P3/8/4K3/8 w - - 0 1"),
    ("rooks open file", "2r3k1/5ppp/8/8/8/8/5PPP/2R3K1 w - - 0 1"),
    ("check", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
    ("stalemate-ish edge", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
]


def main() -> int:
    rows: list[dict] = []
    asymmetric: list[dict] = []
    invalid_mirrors: list[dict] = []

    with Forge() as f:
        for name, fen in POSITIONS:
            board = parse_fen(fen) if len(fen.split()) == 6 else chess.Board(fen)
            try:
                verify_mirror(board)
            except Exception as exc:  # noqa: BLE001
                invalid_mirrors.append({"name": name, "fen": fen, "error": str(exc)})
                print(f"  {name:22s} MIRROR INVALID: {exc}")
                continue

            mirrored = mirror_board(board)
            ev = f.evaluate(board)
            ev_m = f.evaluate(mirrored)

            row = {
                "name": name,
                "fen": board.fen(),
                "mirror_fen": mirrored.fen(),
                "hce": ev["hce"], "nnue": ev["nnue"], "total": ev["total"],
                "mirror_hce": ev_m["hce"], "mirror_nnue": ev_m["nnue"],
                "mirror_total": ev_m["total"],
                "symmetric_total": ev["total"] == ev_m["total"],
                "symmetric_hce": ev["hce"] == ev_m["hce"],
                "symmetric_nnue": ev["nnue"] == ev_m["nnue"],
            }
            rows.append(row)
            flag = "ok " if row["symmetric_total"] else "ASYM"
            print(f"  {flag} {name:22s} {ev['total']:7d} vs {ev_m['total']:7d}  "
                  f"(hce {ev['hce']:6d}/{ev_m['hce']:6d} nnue {ev['nnue']:6d}/{ev_m['nnue']:6d})")
            if not row["symmetric_total"]:
                asymmetric.append(row)

    total_pairs = len(rows)
    with open("out_symmetry.json", "w") as fh:
        json.dump({"positions": rows, "asymmetric": asymmetric,
                   "invalid_mirrors": invalid_mirrors,
                   "denominator": total_pairs}, fh, indent=2)

    print()
    print(f"compared_pairs={total_pairs}")
    print(f"asymmetric_pairs={len(asymmetric)}")
    print(f"ASYM_PAIRS {len(asymmetric)} / {total_pairs}")
    if invalid_mirrors:
        print(f"invalid_mirrors={len(invalid_mirrors)}")
    for row in asymmetric:
        print(f"  ASYM {row['name']}: {row['fen']}")
        print(f"       mirror {row['mirror_fen']}")
        print(f"       total {row['total']} vs {row['mirror_total']} "
              f"(hce {row['hce']} vs {row['mirror_hce']}, "
              f"nnue {row['nnue']} vs {row['mirror_nnue']})")
    return 0 if not asymmetric and not invalid_mirrors else 1


if __name__ == "__main__":
    sys.exit(main())
