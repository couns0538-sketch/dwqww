#!/usr/bin/env python3
"""f11_withdrawal.py OUTDIR

WITHDRAWAL of my own 21-F11, with the measurement that decides it.

21-F11 claimed `score mate 0` on a checkmated root is a fault. On reflection that is the UCI
convention, not a fault: `score mate <y>` means "mate in y moves for the side to move", so
y = 0 means the side to move is mated in zero moves — i.e. it is already checkmate. A mated
side has no move to play, so bestmove 0000 is right and mate 0 is right.

This script does not just assert that; it MEASURES the convention against the engine's own
behaviour on three roots whose truth python-chess establishes:

  A  side to move IS checkmated            -> expect score mate 0, bestmove 0000
  B  side to move CAN mate in 1            -> expect score mate 1, bestmove = the mating move
  C  side to move is stalemated            -> expect score cp 0, bestmove 0000

If A answers mate 0 and B answers mate 1, the engine is consistent with the convention and
21-F11 is WITHDRAWN. If A answered mate 0 but B answered something else, the score scale would
be broken and F11 would stand in a narrower form.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

import chess

CASES = {
    "A_mated_now": "4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60",
    "B_can_mate_in_1": "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60",
    "C_stalemated": "7k/5Q2/6K1/8/8/8/8/8 b - - 0 60",
}


def score(info):
    m = re.search(r"score (cp|mate) (-?\d+)", info)
    return (m.group(1), int(m.group(2))) if m else None


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    builds = [("base", os.path.expanduser("~/b/asan/forge")),
              ("pc", os.path.expanduser("~/b/pc_asan/forge"))]
    R = {}
    rows = ["| build | case | python truth | bestmove | score | matches convention |",
            "|---|---|---|---|---|---|"]
    expect = {"A_mated_now": ("mate", 0), "B_can_mate_in_1": ("mate", 1),
              "C_stalemated": ("cp", 0)}
    for bname, exe in builds:
        for case, fen in CASES.items():
            b = chess.Board(fen)
            truth = ("checkmate" if b.is_checkmate() else
                     "stalemate" if b.is_stalemate() else
                     "can mate in 1" if case.startswith("B") else "other")
            e = SafeEngine(exe, os.path.join(outdir, "%s_%s_raw.txt" % (bname, case)),
                           hash_mb=16, threads=1)
            e.position("position fen " + fen)
            lines = e.go("go depth 10")
            e.close()
            bm = bestmove_of(lines)
            sc = score(last_info(lines))
            ok = (sc == expect[case])
            R["%s|%s" % (bname, case)] = dict(bestmove=bm, score=sc, expect=expect[case], ok=ok)
            rows.append("| %s | %s | %s | %s | %s | %s |" % (
                bname, case, truth, bm, sc, "yes" if ok else "NO"))

    base_ok = all(v["ok"] for k, v in R.items() if k.startswith("base|"))
    pc_ok = all(v["ok"] for k, v in R.items() if k.startswith("pc|"))
    text = "\n".join(rows)
    text += ("\n\nThe convention check: a mated side scores mate 0, a side that can mate in 1 "
             "scores mate 1, a stalemated side scores cp 0.\n")
    text += "base build consistent: %s\npc build consistent: %s\n" % (base_ok, pc_ok)
    text += ("\n=> 21-F11 is %s\n" % ("WITHDRAWN (mate 0 is the correct UCI score for a side "
                                      "that is already mated)" if (base_ok and pc_ok)
                                      else "NOT withdrawn — the score scale is inconsistent"))
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()