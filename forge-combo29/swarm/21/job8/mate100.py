#!/usr/bin/env python3
"""mate100.py EXE OUTDIR

The sharpest case of area 1 job 2, done properly: positions where a mate in 1 EXISTS and the
halfmove counter is 100. Both colours, plus the same positions at counter 99 as the control
that the position is fine and only the counter matters.

The mate is verified independently with python-chess by COPYING the board for each candidate
move (a first version of this probe mutated the board in place and reported "no mate" when
there were twelve; that bug is why every check here builds a copy).

For each case: engine `go depth 5`, then `go nodes 100`, then `go movetime 50` — the three
searches area 1 job 2 asks for on terminal roots — all read to `bestmove`.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of, last_info  # noqa: E402

import chess

CASES = [
    ("white_mate_hm100", "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60"),
    ("white_mate_hm99", "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 99 60"),
    ("black_mate_hm100", "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 100 60"),
    ("black_mate_hm99", "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 99 60"),
]
SEARCHES = ["go depth 5", "go nodes 100", "go movetime 50"]


def mates_in_one(fen):
    b = chess.Board(fen)
    out = []
    for m in list(b.legal_moves):
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            out.append(m.uci())
    return out


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = ["| case | python-chess mate in 1 | search | engine bestmove | is it a mate? | last info |",
            "|---|---|---|---|---|---|"]
    for name, fen in CASES:
        mates = mates_in_one(fen)
        e = SafeEngine(exe, os.path.join(outdir, name + "_raw.txt"))
        ans = e.position("position fen " + fen)
        if any("invalid FEN" in l for l in ans):
            raise AssertionError("%s: the FEN was REFUSED (%s) — every search answer below "
                                 "would be about the stale board, not this position"
                                 % (name, [l for l in ans if "info string" in l]))
        for search in SEARCHES:
            try:
                lines = e.go(search, timeout=60)
                bm, info = bestmove_of(lines), last_info(lines)
            except Timeout:
                bm, info = "TIMEOUT", ""
            if bm in mates:
                verdict = "MATE FOUND"
            elif mates:
                verdict = "missed (a mate in 1 existed)"
            else:
                verdict = "n/a"
            rows.append("| %s | %s | %s | %s | %s | %s |" %
                        (name, ", ".join(mates) or "none", search, bm, verdict, info[-58:]))
        e.close()
    text = "\n".join(rows)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()