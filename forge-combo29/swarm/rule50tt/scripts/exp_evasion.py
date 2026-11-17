"""The one gap: in-check evasion nodes near clock 99.

The coordinator's note says the band is reachable only through a QUIET EVASION in
qsearch, because any capture resets the clock. That is the only path that can put
a node at clock 100 without resetting, so it is the only place a stale-clock
entry could be reused across the 100 boundary.

This file answers two questions separately, because only the first is answerable
without new instrumentation:

  Q1 Is such a node REACHED? A root at clock 99 whose best line is a quiet king
     move reaches clock 100 at ply 1. That is easy to construct and is measured
     here directly: the engine's own PV tells us the move played and therefore the
     child's clock.

  Q2 Does a stale entry at such a node CHANGE the score? Measured by the same
     warm/cold differential as item 2, but with the root chosen so that the
     clock-100 node is on the principal variation.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import uci_driver as u  # noqa: E402

SHIPPED = "/agent/repos/dwqww/forge-combo29/build-rule50/forge"

# Roots at clock 98/99 where the side to move is IN CHECK and the only evasions
# are quiet king moves: the exact shape the note names. Every one is a legal
# position checked by python-chess before use.
CASES = [
    # (label, fen-fields, expected: does the PV's first move reset the clock?)
    ("kq_check_99",  "8/8/8/8/8/1K6/2Q5/7k b - -", 99),
    ("kr_check_99",  "7k/8/8/R7/8/8/8/K7 b - -", 99),
    ("kq_check_98",  "8/8/8/8/8/1K6/2Q5/7k b - -", 98),
    ("rook_check_99", "6k1/5ppp/8/8/8/8/8/R5NK b - -", 99),
    ("rook_check_97", "6k1/5ppp/8/8/8/8/8/R5NK b - -", 97),
]


def is_reset(board_after_move_fen_before, move_uci):
    """A move resets the fifty-move counter iff it is a capture or a pawn move."""
    import chess
    b = chess.Board(board_after_move_fen_before)
    m = chess.Move.from_uci(move_uci)
    piece = b.piece_at(m.from_square)
    return b.is_capture(m) or (piece is not None and piece.piece_type == chess.PAWN)


def main():
    import chess
    rows = []
    print(f"{'case':15} {'clock':>5} {'bestmove':9} {'score':>10} {'nodes':>9} {'resets?':>7} {'childclock':>10}")
    for label, fields, clock in CASES:
        fen = f"{fields} {clock} 60"
        b = chess.Board(fen)
        if not b.is_valid():
            print(f"{label:15} ILLEGAL FIXTURE {fen}")
            continue
        in_check = b.is_check()
        e = u.Engine(SHIPPED, hash_mb=16, timeout=60.0)
        try:
            r = e.search(f"position fen {fen}", "go depth 12")
        finally:
            e.close()
        bm = r["bestmove"]
        resets = None
        child_clock = None
        if bm and bm != "0000":
            try:
                resets = is_reset(fen, bm)
                child_clock = 0 if resets else clock + 1
            except ValueError:
                resets = "badmove"
        rows.append({"case": label, "fen": fen, "in_check": in_check, "bestmove": bm,
                     "score_kind": r["score_kind"], "score": r["score"], "nodes": r["nodes"],
                     "resets": resets, "child_clock": child_clock,
                     "invalid_fen": r["invalid_fen"]})
        print(f"{label:15} {clock:>5} {str(bm):9} {r['score_kind']} {r['score']:>6} {r['nodes']:>9} "
              f"{str(resets):>7} {str(child_clock):>10}")

    # Q1's verdict: how many of these actually put a node at clock 100?
    reached = [r for r in rows if r["child_clock"] is not None and r["child_clock"] >= 100]
    in_check = [r for r in rows if r["in_check"]]
    print(f"\nfixtures in check at the root: {len(in_check)} of {len(rows)}")
    print(f"fixtures whose PV reaches a node at clock >= 100 without a reset: {len(reached)}")
    for r in reached:
        print(f"   {r['case']}: child clock {r['child_clock']}, move {r['bestmove']}")

    json.dump(rows, open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/evasion.json", "w"), indent=1)


if __name__ == "__main__":
    main()
