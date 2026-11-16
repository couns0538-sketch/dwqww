#!/usr/bin/env python3
"""seat 17 area 7 job 1 finding S-F1: `searchmoves` that names no legal move makes the
engine answer `bestmove 0000` on a position that HAS legal moves.

UCI says bestmove 0000 means "no legal move exists". Here 29 legal moves exist, so a GUI
takes the 0000 as an illegal move from the side to move.

usage: finding_searchmoves.py <exe> <outdir>
Writes one log per case and a summary table, all as text.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci_driver import run_one

CASES = [
    # (label, position line, go line, what UCI should answer)
    ("startpos_illegal_only", "position startpos", "go depth 5 searchmoves e7e5",
     "a legal move (e2e4 etc.) - e7e5 is Black's move, so no legal root move matches"),
    ("startpos_garbage_name", "position startpos", "go depth 5 searchmoves zzzz",
     "a legal move or an error line, not an illegal 0000"),
    ("startpos_legal_control", "position startpos", "go depth 5 searchmoves e2e4",
     "e2e4 (control: the restriction is honoured and legal)"),
    ("mate_position_any", "position fen r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4",
     "go depth 5 searchmoves a7a6", "0000 is correct here: the position is mate"),
    ("black_to_move_illegal_only", "position fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
     "go depth 5 searchmoves e2e4", "a legal Black move, not 0000"),
]


def main():
    exe, outdir = sys.argv[1:3]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for label, position, goline, expect in CASES:
        log = os.path.join(outdir, label + ".log")
        info = run_one(exe, ["uci", "isready", position, "isready", goline], 60, log)
        text = open(log).read()
        info_lines = [ln for ln in text.splitlines() if ln.startswith("info string")]
        depths = [ln for ln in text.splitlines() if ln.startswith("info depth")]
        rows.append({
            "case": label,
            "position": position,
            "go": goline,
            "bestmove": info["bestmove"],
            "info_string": info_lines,
            "depth_lines": len(depths),
            "expected": expect,
        })
    for row in rows:
        print("%-30s %-52s -> %s   (%d info depth lines)%s"
              % (row["case"], row["go"], row["bestmove"], row["depth_lines"],
                 "" if not row["info_string"] else "  [" + row["info_string"][0] + "]"))
    with open(os.path.join(outdir, "summary.txt"), "w") as handle:
        for row in rows:
            handle.write("%s\n  position: %s\n  go: %s\n  bestmove: %s\n  info: %s\n  depth lines: %d\n  expected: %s\n\n"
                         % (row["case"], row["position"], row["go"], row["bestmove"],
                            row["info_string"], row["depth_lines"], row["expected"]))


if __name__ == "__main__":
    main()
