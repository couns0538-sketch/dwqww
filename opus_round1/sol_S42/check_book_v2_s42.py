#!/usr/bin/env python3
"""Independent check of a built S42 book (read-only): python-chess parses every EPD line (6-field FEN, valid position,
side to move not in check, game not over); duplicates against the current book's EXITS (must be 0) and, for
information, against EVERY position along the current book's lines; repeats inside the new book; sha256 of the file;
abs(eval) of every line inside the band per the metadata CSV.
usage: python -I -B check_book_v2_s42.py CURRENT_BOOK.pgn NEW_BOOK.epd META.csv LO HI"""
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

import chess
import chess.pgn


def epd4(b):
    return " ".join(b.fen().split()[:4])


def main():
    book, epd, meta, lo, hi = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    exits, along = set(), set()
    n_lines = 0
    with open(book, encoding="utf-8-sig", errors="replace") as f:
        while True:
            g = chess.pgn.read_game(f)
            if g is None:
                break
            b = g.board(); along.add(epd4(b))
            for m in g.mainline_moves():
                b.push(m); along.add(epd4(b))
            exits.add(epd4(b)); n_lines += 1
    lines = epd.read_text(encoding="ascii").splitlines()
    bad, ids = [], []
    for i, fen in enumerate(lines):
        try:
            b = chess.Board(fen)
            if len(fen.split()) != 6 or not b.is_valid() or b.is_check() or b.is_game_over():
                bad.append(i)
            ids.append(epd4(b))
        except ValueError:
            bad.append(i); ids.append(None)
    rows = list(csv.DictReader(io.StringIO(meta.read_text(encoding="utf-8"))))
    out = {"current_book_lines": n_lines, "current_book_exits": len(exits), "current_book_positions_along_lines": len(along),
           "new_book_lines": len(lines), "sha256": hashlib.sha256(epd.read_bytes()).hexdigest(),
           "invalid_or_in_check_or_over": len(bad), "duplicates_with_current_book_exits": sum(i in exits for i in ids),
           "found_anywhere_along_current_book_lines": sum(i in along for i in ids), "repeats_inside_new_book": len(ids) - len(set(ids)),
           "meta_rows": len(rows), "meta_matches_epd": [r["fen"] for r in rows] == lines,
           "abs_eval_in_band": all(lo <= abs(int(r["eval_white_cp"])) <= hi for r in rows),
           "favored_white": sum(int(r["eval_white_cp"]) > 0 for r in rows), "plies": {}}
    for r in rows:
        k = str(r["deviation_ply"]); out["plies"][k] = out["plies"].get(k, 0) + 1
    ok = out["invalid_or_in_check_or_over"] == 0 and out["duplicates_with_current_book_exits"] == 0 and out["repeats_inside_new_book"] == 0 \
        and out["meta_matches_epd"] and out["abs_eval_in_band"]
    out["result"] = "PASS" if ok else "FAIL"
    print(json.dumps(out, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
