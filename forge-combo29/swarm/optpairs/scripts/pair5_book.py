"""Pair 5: Book Depth x OwnBook x Book Variety.

The audit already measured the part that reproduces as an RNG problem: the book's
move comes from a clock-seeded RNG (`uci.cpp:161-162`,
`steady_clock::now()`), with `Book Variety` defaulting to 30, so it varies between
runs at Threads 1 too (3 of 5 vary at Threads 1, 0 of 5 at Book Variety 0). What
it does NOT have is the 2x2x2 that says which of the three options actually
decides whether a book move is played at all, and which merely decides which one.

The three options are not parallel:
  OwnBook      gates the whole path (`game_search && own_book && !book.empty()`)
  Book Depth   gates it by `game_ply(board) < book_depth` (game_ply = 2*(fullmove-1)
               + side, uci.cpp:141-143) -- so it is a PLY comparison against
               something a GUI reads out of the FEN, not a move number
  Book Variety 0..100, only chooses among entry candidates within a weight band

Grid: OwnBook {t,f} x Book Depth {0, 20, 30, 100} x Book Variety {0, 30} on a
book-hit position, 3 repeats, 2 positions. The two positions differ only in
fullmove counter, so the Depth boundary is measured rather than assumed.

`info string book move` is the positive signal; the four-field signature is NOT
usable for a book cell because a book move emits no `info depth` line at all
(§3, trap 19), which is itself recorded per row.
"""
import json
import os
import sys

import grid
import uci

# startpos and the same board at three fullmove counters. game_ply = 2*(fm-1).
POS = [
    ("fm1", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("fm11", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 11"),
    ("fm16", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 16"),
]
GO = "go wtime 60000 btime 60000 winc 1000 binc 1000"   # the book needs a clock form
REPEATS = 3

BASE = []   # nothing inherited: OwnBook is a grid axis here
ARM = []
for own in ("true", "false"):
    for depth in ("0", "20", "30", "100"):
        for variety in ("0", "30"):
            ARM.append((f"own{own[0]}_d{depth}_v{variety}",
                        {"OwnBook": own, "Book Depth": depth, "Book Variety": variety}))


def main():
    r = grid.grid("pair5-book", ARM, POS, GO, repeats=REPEATS, base=BASE)
    out = {"go": GO, "repeats": REPEATS, "acceptance_failures": grid.acceptance(r), "rows": {}}
    for label in r["cells"]:
        per = {}
        for p, row in r["rows"][label].items():
            books = [x["book"] for x in row["runs"]]
            moves = sorted({x["bestmove"] for x in row["runs"]})
            per[p] = {
                "book_played": sum(1 for b in books if b),
                "repeats": len(books),
                "distinct_moves": len(moves),
                "moves": moves,
                "info_depth_lines": [x["infos"] for x in row["runs"]],
                "nodes": [x["nodes"] for x in row["runs"]],
                "self_differs": row["self_differs"],
            }
        out["rows"][label] = per
    with open(os.path.join(grid.EVID, "pair5-analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"Book grid, {GO}, {REPEATS} repeats")
    print("acceptance failures:", out["acceptance_failures"] or "none")
    hdr = "  cell".ljust(22) + "".join(f"{p:>26s}" for p, _ in POS)
    print(hdr)
    print("  " + "".ljust(20) + "".join(f"{'book/reps moves':>26s}" for _ in POS))
    for label in r["cells"]:
        line = f"  {label:<20s}"
        for p, _ in POS:
            v = out["rows"][label][p]
            line += f"{v['book_played']}/{v['repeats']} {v['distinct_moves']}mv".rjust(26)
        print(line)


if __name__ == "__main__":
    sys.exit(main())
