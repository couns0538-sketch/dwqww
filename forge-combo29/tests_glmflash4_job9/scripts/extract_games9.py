#!/usr/bin/env python3
"""Extract one line per game from a fastchess PGN, with the ending reason.

usage: extract_games9.py <match.pgn> <out_file>
line: round|white|black|result|how it ended|opening FEN
The ending comes from the game's LAST {...} comment: the text after its last
comma (e.g. "... 0.000s, Draw by fifty moves rule" -> "Draw by fifty moves
rule"). For decisive games with no reason comment the ending is "mate";
for draws without one, "draw (no reason comment)".
"""
import re
import sys

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    out = open(dst, "w")
    tags: dict[str, str] = {}
    moves: list[str] = []

    def last_reason(movetext: str, result: str) -> str:
        comments = re.findall(r"\{([^}]*)\}", movetext)
        if comments:
            tail = comments[-1]
            if "," in tail:
                reason = tail.rsplit(",", 1)[1].strip()
                if reason:
                    return reason
            low = tail.lower()
            if "draw" in low or "resign" in low or "time" in low or "disconnect" in low \
                    or "illegal" in low or "stall" in low or "abandon" in low:
                return tail.strip()
        if result in ("1-0", "0-1"):
            return "mate"
        if result == "1/2-1/2":
            return "draw (no reason comment)"
        return "unknown"

    def flush() -> None:
        if "White" in tags and "Black" in tags:
            fen = tags.get("FEN") or START_FEN
            result = tags.get("Result", "?")
            out.write("|".join([
                tags.get("Round", "?"), tags["White"], tags["Black"],
                result, last_reason(" ".join(moves), result), fen,
            ]) + "\n")

    with open(src) as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                if moves:
                    flush()
                    tags, moves = {}, []
                body = line[1:-1]
                key, _, val = body.partition(" ")
                tags[key] = val.strip('"')
            elif line:
                moves.append(line)
    if tags:
        flush()
    out.close()


if __name__ == "__main__":
    main()
