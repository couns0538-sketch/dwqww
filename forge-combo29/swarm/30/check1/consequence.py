#!/usr/bin/env python3
"""consequence.py -- does removing the halfmove>=100 root shortcut break the real fifty-move draw?

Synchronised like check_s01f5.py: one process per case, wait for each search's own bestmove.
Compares the base release build with the SAME build carrying seat 01's patch.

usage: consequence.py BASE_EXE PATCHED_EXE OUTDIR
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "check_s01f5.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

CASES = [
    # a genuine fifty-move draw: kings and a rook, no mate, counter far past 100
    ("draw_claimable_hm120", "6k1/5ppp/8/8/8/8/5PPP/6K1 w - - 120 1"),
    ("draw_claimable_hm150", "6k1/5ppp/8/8/8/8/5PPP/6K1 w - - 150 1"),
    ("draw_claimable_hm99", "6k1/5ppp/8/8/8/8/5PPP/6K1 w - - 99 1"),
    # a KN v K insufficient material at a huge counter
    ("insufficient_hm150", "8/8/8/4k3/8/8/8/4K1N1 w - - 150 1"),
    # a real fifty-move situation with a WIN on the board (KQ v K): the win is still there
    ("kqvk_hm120", "8/8/8/4k3/8/8/8/K1Q5 w - - 120 1"),
]


def main():
    base, patched, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    print("%-22s %-28s %-28s" % ("case", "BASE (unpatched)", "PATCHED (seat 01 fix)"))
    for name, fen in CASES:
        rb = mod.run_case(base, fen, go="go depth 6")
        rp = mod.run_case(patched, fen, go="go depth 6")
        row = {"case": name, "fen": fen,
               "base": {"score": rb["score"], "bestmove": rb["bestmove"], "nodes": rb["nodes"]},
               "patched": {"score": rp["score"], "bestmove": rp["bestmove"], "nodes": rp["nodes"]}}
        rows.append(row)
        print("%-22s %-28s %-28s" % (
            name,
            "score=%s bm=%s n=%s" % (rb["score"], rb["bestmove"], rb["nodes"]),
            "score=%s bm=%s n=%s" % (rp["score"], rp["bestmove"], rp["nodes"])))
    with open(os.path.join(outdir, "consequence.json"), "w") as f:
        json.dump({"base_exe": os.path.realpath(base),
                   "patched_exe": os.path.realpath(patched),
                   "go": "go depth 6", "rows": rows}, f, indent=1)


if __name__ == "__main__":
    main()
