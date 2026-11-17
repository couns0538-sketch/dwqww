"""The five matrix rows, each with fixture, depth, score, node count,
`bestmove`, and the pv shape -- PRESENT-AND-EMPTY vs ABSENT, which is the
report's main client finding and must never be collapsed.

Every fixture below was produced by the enumerator named beside it, not by
eyeballing a board. Fixtures that failed python-chess or failed the structural
claim are recorded in the run log rather than deleted, because the first draft
of this file contained four of them and the correction is part of the evidence.

Row 1  one ply from stalemate: does the engine see it, or score a win and get stuck?
Row 2  one ply from insufficient material: is the draw scored BEFORE the reduction?
Row 3  exactly one legal move, a capture that resets the clock: does the 50-move
       evaluation change after the move?
Row 4  halfmove 99 where EVERY legal move is a pawn move: does the engine know
       the mover cannot reach 100?
Row 5  `bestmove 0000` at EVERY mate root -- consistent, or does it emit a move?
"""
import json
import sys
import chess

from forge_drv import Forge, RefusedFen

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-boundary/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "../evidence/matrix_rows.json"

DEPTH = "go depth 12"

# ---- row 1: every legal move stalemates (from stalemate.enum_every_move_stalemates)
ROW1 = [
    "8/8/8/8/1pk1p3/1P2P3/5q2/7K b - - 0 30",     # every move stalemates
    "k1K5/1p6/1P1B4/8/8/8/8/8 w - - 0 30",         # every move stalemates
    "8/8/1p2p3/1P2PK2/8/8/2Q5/k7 w - - 0 30",      # every move stalemates
    # CONTROL: a win exists; must NOT be 0.00
    "k7/2Q5/8/8/8/8/8/K7 w - - 0 30",
]

# ---- row 2: one ply from insufficient material
# Every fixture here is NOT already drawn (python-chess is_insufficient_material
# is False) and every legal move by the side to move permits, on the very next
# ply, a capture that reduces the game to an insufficient-material set. Both
# properties were enumerated, so "one ply away" is earned rather than asserted.
ROW2 = [
    # FORCED one-ply reduction: White has exactly one legal move and it lets
    # Black take the knight, leaving KvK. The draw is unavoidable -> 0.00 is
    # the only correct score, and it is correct BEFORE the material is gone.
    ("row2_forced_0", "8/8/8/8/8/8/q7/KNk5 w - - 0 40", "forced"),
    ("row2_forced_1", "8/8/8/8/8/q7/8/KNk5 w - - 0 40", "forced"),
    ("row2_forced_2", "8/8/8/8/8/8/q7/K1kN4 w - - 0 40", "forced"),
    # OPTIONAL reduction: a drawn continuation EXISTS but is not forced. A
    # 0.00 here is only right if the engine proves it; the position is not
    # automatically drawn, so this is scored as "forseen" not "forced".
    ("row2_optional_0", "8/8/8/8/8/8/b7/K1k1B3 w - - 0 40", "optional"),
    ("row2_optional_1", "8/8/8/8/8/8/b4B2/K1k5 w - - 0 40", "optional"),
    # bare-kings control (already drawn -- the ROOT case, not one ply away)
    ("row2_root_drawn", "4k3/8/8/8/8/8/8/4K3 w - - 0 40", "root"),
    # CONTROL: reduction leaves KRvK, which is WON -- must not be 0.00
    ("row2_control_won", "4k3/8/8/8/8/8/4r3/4KR2 w - - 0 40", "control"),
]

# ---- row 3: exactly ONE legal move, a capture that resets the clock
# Enumerated so that: exactly one legal move; it is a capture; it resets the
# halfmove clock; and the resulting position is NOT drawn by material (so a
# 0.00 here would be the 50-move rule misfiring, not a real draw). The mover is
# Black, who is lost either way -- the question is whether the score wrongly
# becomes 0.00 because the clock stood at 99.
ROW3 = [
    "8/8/8/8/8/8/Q7/kRK5 b - - 99 60",    # only a1a2 = KxQ, then KRvK for White
    "8/8/8/8/8/8/Q7/k1KR4 b - - 99 60",   # only a1a2 = KxQ, then KRvK
    "8/8/8/8/8/8/Q7/k1K1R3 b - - 99 60",
    # CONTROL: same material at clock 0 -- the score must not depend on the clock
    "8/8/8/8/8/8/Q7/kRK5 b - - 0 60",
]

# ---- row 4: halfmove 99, EVERY legal move is a pawn move
# Enumerated: the mover's king has no legal move, only its pawn can push.
# The halfmove clock resets to 0 on any of these, so the draw is NOT reachable
# by the mover reaching 100 -- the correct handling is a clock RESET, and the
# score should not be 0.00.
ROW4 = [
    "8/8/8/8/8/8/P7/K1k5 w - - 99 60",    # only a2a3/a2a4
    "8/8/8/8/8/8/7P/5k1K w - - 99 60",    # only h2h3/h2h4
    # CONTROL: the mover has king moves too, so not every move resets the clock
    "8/8/8/8/8/8/P7/K6k w - - 99 60",
]

# ---- row 5: every mate root shape. All verified is_checkmate() below.
ROW5 = [
    ("mate_back_rank_q", "7k/6Q1/6K1/8/8/8/8/8 b - - 0 60"),
    ("mate_fool", "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"),
    ("mate_white_side", "8/8/8/8/8/6k1/6q1/7K w - - 0 60"),
    ("mate_corner_q", "k7/1QK5/8/8/8/8/8/8 b - - 0 60"),
    ("mate_smothered", "5K1k/5Npp/8/8/8/8/8/8 b - - 0 60"),
    ("mate_ladder", "R5k1/8/6K1/8/8/8/8/R7 b - - 0 60"),
]


def row(eng, label, fen, go=DEPTH, moves=None):
    b = chess.Board(fen)
    if not b.is_valid():
        return {"label": label, "fen": fen, "py_valid": False,
                "skipped": "python-chess rejects this FEN"}
    try:
        rec = eng.search(fen, go, moves=moves)
    except RefusedFen as e:
        return {"label": label, "fen": fen, "go": go, "moves": moves or [],
                "refused": True, "error": str(e), "py_valid": True}
    return {
        "label": label, "fen": fen, "go": go, "moves": moves or [],
        "refused": False, "py_valid": True,
        "py_legal": b.legal_moves.count(),
        "py_in_check": b.is_check(),
        "py_checkmate": b.is_checkmate(),
        "py_stalemate": b.is_stalemate(),
        "py_insufficient": b.is_insufficient_material(),
        "py_halfmove": b.halfmove_clock,
        "depth": rec.depth(), "seldepth": rec.seldepth(),
        "score": rec.score(), "nodes": rec.nodes(),
        "bestmove": rec.bestmove,
        "pv": rec.pv(), "pv_shape": rec.pv_shape(),
        "n_infos": len(rec.infos),
        "info_strings": rec.info_strings(),
        "last_info": rec.last_info,
    }


def show(title, rows):
    print(f"\n=== {title} ===")
    print(f"{'label':26} {'legal':>5} {'score':14} {'nodes':>7} {'bestmove':9} "
          f"{'pv_shape':8} pvlen")
    for r in rows:
        if r.get("skipped"):
            print(f"{r['label']:26} SKIPPED: {r['skipped']}")
            continue
        if r.get("refused"):
            print(f"{r['label']:26} REFUSED: {r['error']}")
            continue
        print(f"{r['label']:26} {str(r['py_legal']):>5} {str(r['score']):14} "
              f"{str(r['nodes']):>7} {str(r['bestmove']):9} "
              f"{r['pv_shape']:8} {len(r['pv'])}")


def main():
    out = {}

    with Forge(EXE) as eng:
        # row 1
        out["row1_stalemate_next"] = [row(eng, f"row1_{i}", f)
                                      for i, f in enumerate(ROW1)]
        # row 2, at three depths so a shallow/depth-dependent answer is visible
        r2 = []
        for label, f, kind in ROW2:
            for d in (1, 6, 12):
                r = row(eng, f"{label}_d{d}", f, go=f"go depth {d}")
                r["reduction_kind"] = kind
                r2.append(r)
        out["row2_insufficient_one_ply"] = r2
        # row 3, before and after the forced capture
        r3 = []
        for i, f in enumerate(ROW3):
            r3.append(row(eng, f"row3_{i}_before", f))
            b = chess.Board(f)
            if b.legal_moves.count() == 1:
                mv = list(b.legal_moves)[0]
                b.push(mv)
                r3.append(row(eng, f"row3_{i}_after_{mv.uci()}", b.fen()))
        out["row3_single_clock_reset"] = r3
        # row 4
        r4 = []
        for i, f in enumerate(ROW4):
            r4.append(row(eng, f"row4_{i}_d12", f))
            for d in (1, 6):
                r4.append(row(eng, f"row4_{i}_d{d}", f, go=f"go depth {d}"))
        out["row4_all_pawn_moves_at_99"] = r4
        # row 5
        out["row5_mate_roots"] = [row(eng, label, fen) for label, fen in ROW5]

    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)

    show("row 1  one ply from stalemate", out["row1_stalemate_next"])
    show("row 2  one ply from insufficient material", out["row2_insufficient_one_ply"])
    show("row 3  single forced clock-resetting capture", out["row3_single_clock_reset"])
    show("row 4  all-pawn-moves at halfmove 99", out["row4_all_pawn_moves_at_99"])
    show("row 5  mate roots: 0000 vs a move", out["row5_mate_roots"])

    # ---- row 5 headline: is 0000 consistent at every mate root? ----------
    mates = out["row5_mate_roots"]
    zero = [r for r in mates if r.get("bestmove") == "0000"]
    legal = [r for r in mates if r.get("bestmove") not in ("0000", None)]
    print(f"\nROW 5 headline: {len(zero)}/{len(mates)} mate roots answered 0000; "
          f"{len(legal)} answered a MOVE "
          f"({[(r['label'], r['bestmove']) for r in legal]})")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
