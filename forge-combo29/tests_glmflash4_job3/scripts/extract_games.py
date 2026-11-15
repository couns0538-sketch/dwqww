#!/usr/bin/env python3
"""Extract one line per game from a fastchess PGN.

usage: extract_games.py <match.pgn> <out_file>
line format: round|white|black|result|opening FEN
"""
import sys

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    out = open(dst, "w")
    tags: dict[str, str] = {}

    def flush() -> None:
        if "White" in tags and "Black" in tags:
            fen = tags.get("FEN") or START_FEN
            out.write("|".join([
                tags.get("Round", "?"), tags["White"], tags["Black"],
                tags.get("Result", "?"), fen,
            ]) + "\n")

    with open(src) as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                body = line[1:-1]
                key, _, val = body.partition(" ")
                val = val.strip('"')
                tags[key] = val
            elif line == "":
                if tags:
                    flush()
                    tags = {}
    if tags:
        flush()
    out.close()


if __name__ == "__main__":
    main()
