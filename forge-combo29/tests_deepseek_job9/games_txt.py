#!/usr/bin/env python3
"""Job 9: one line per game for a match, from its PGN.

Format: round | side with white (cand/base) | opening (FEN from the SetUp header) | result
For each game the 'cand' score is also included so a reader can total it without parsing.

Usage: games_txt.py <pgn> <out.txt>
"""
import re
import sys


def main():
    pgn, out = sys.argv[1], sys.argv[2]
    text = open(pgn, errors="replace").read()
    blocks = [b for b in re.split(r'(?=\[Event )', text) if "[Event" in b]
    lines = ["# round | white | opening FEN | result | cand score (1 = cand won)"]
    for block in blocks:
        rnd = re.search(r'\[Round "([^"]+)"\]', block)
        white = re.search(r'\[White "([^"]+)"\]', block)
        fen = re.search(r'\[FEN "([^"]+)"\]', block)
        result = re.search(r'\[Result "([^"]+)"\]', block)
        if not (rnd and white and result):
            continue
        w = white.group(1)
        r = result.group(1)
        if r == "1/2-1/2":
            cand_pts = "0.5"
        elif r == "1-0":
            cand_pts = "1" if w == "cand" else "0"
        elif r == "0-1":
            cand_pts = "1" if w == "base" else "0"
        else:
            cand_pts = "?"
        lines.append(f"{rnd.group(1)} | {w} | {fen.group(1) if fen else '-'} | {r} | {cand_pts}")
    open(out, "w").write("\n".join(lines) + "\n")
    print(f"{out}: {len(lines)-1} games")


if __name__ == "__main__":
    main()
