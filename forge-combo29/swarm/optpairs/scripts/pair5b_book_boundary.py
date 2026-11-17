"""Pair 5b: the exact Book Depth boundary, measured on a line that is IN the book.

Pair 5 compared Book Depth 0/20/30/100 and found the boundary between fullmove 11
and 16 for depth 30, but a fullmove counter is a coarse lever: it moves game_ply
by 2 per fullmove and the side to move adds 1. Worse, a real book line has finite
depth -- walking the Ruy Lopez mainline shows entries only at plies 0..6
(evidence/pair5b-hits.json), so varying the FEN's fullmove counter on an OPENING
board tests the depth gate on a board the book still knows, not on a long line.

This walks a line that IS in the book and sets Book Depth across the boundary, so
the rule `book plays iff game_ply(board) < Book Depth` is tested at consecutive
ply values rather than at fullmove steps.

Boundary test: for a board at game_ply p, Book Depth d plays iff p < d. So
(d, p) pairs (7,6) play and (6,6) do not, for a position whose entry exists.
"""
import json
import os
import sys

import grid
import uci

LINE = ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"]   # game_ply 6 at the end
GO = "go wtime 60000 btime 60000 winc 1000 binc 1000"
REPEATS = 3


def position_after(n):
    return "position startpos" + ((" moves " + " ".join(LINE[:n])) if n else "")


def main():
    rows = []
    for n in (0, 3, 6):
        ply = n  # game_ply for startpos + n moves, White moving = n
        for depth in (0, ply, ply + 1, 100):
            for variety in ("0", "30"):
                r = uci.run(options=[("OwnBook", "true"), ("Book Depth", str(depth)),
                                     ("Book Variety", variety)],
                            position=position_after(n), go=GO)
                rows.append({"plies_sent": n, "game_ply": ply, "book_depth": depth,
                             "variety": variety, "book_played": bool(r["book"]),
                             "bestmove": r["bestmove"], "accepted": r["accepted"]})
    # The rule. A cell is predictable iff book_played == (game_ply < depth).
    mismatched = [r for r in rows if r["depth_ok"] is False] if rows and "depth_ok" in rows[0] else []
    for r in rows:
        r["depth_ok"] = r["book_played"] == (r["game_ply"] < r["book_depth"])
    mismatched = [r for r in rows if not r["depth_ok"]]
    out = {"rule": "book plays iff game_ply(board) < Book Depth", "go": GO, "rows": rows,
           "mismatched": mismatched, "acceptance_failures": [r for r in rows if not r["accepted"]]}
    with open(os.path.join(grid.EVID, "pair5b-boundary.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("Book Depth boundary on a line that is in the book")
    print(f"  {'ply':>4s} {'depth':>6s} {'variety':>8s}  book?  rule-ok")
    for r in rows:
        print(f"  {r['game_ply']:4d} {r['book_depth']:6d} {r['variety']:>8s}  {str(r['book_played']):5s}  {r['depth_ok']}")
    print("mismatches:", len(mismatched), "of", len(rows))


if __name__ == "__main__":
    sys.exit(main())
