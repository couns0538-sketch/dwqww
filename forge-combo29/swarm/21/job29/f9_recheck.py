#!/usr/bin/env python3
"""f9_recheck.py OUTDIR

RE-TEST of my own 21-F9 under handoff file 6's rule, on both builds.

File 6 says a cp 0 at a high halfmove counter is a defect ONLY when a forced mate exists that
ends no later than the 100th half-move, i.e. when

        2N - 1 <= 100 - counter

where N comes from the SAME board with counter 0 at `go depth 20`+ and the board at the REAL
counter still scores cp 0 at that depth.

My 21-F9 tested counter 100 with a mate in 1. 2*1-1 = 1 > 100-100 = 0, so that is NOT a defect —
my F9 as originally stated was judged against the wrong standard. This script tests the window
where the rule actually bites: counters at which a mate DOES land by half-move 100.

Cases (each a mate-in-1 board at several counters, plus a mate-in-3 board):
  counter 99, mate 1   -> 2*1-1 = 1  = 100-99 = 1  -> AT the limit: a defect if cp 0
  counter 98, mate 1   -> 1 < 2                    -> a defect if cp 0
  counter 100, mate 1  -> 1 > 0                    -> NOT a defect, cp 0 is correct
  counter 96, mate 3   -> 5 > 4 (100-96=4)         -> NOT a defect
  counter 95, mate 3   -> 5 = 5                    -> at the limit: a defect if cp 0

For each case: read N on the counter-0 board at depth 20, print the inequality, then score the
REAL counter board at depth 20 and at depth 6.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

import chess

# a mate-in-1 for White: Re1-e8 ; a mate-in-3 for White: needs two preparatory moves
MATE1 = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - {hm} 60"
MATE3 = "6k1/5qpp/8/8/8/8/5PPP/3R2K1 w - - {hm} 60"


def score(info):
    m = re.search(r"score (cp|mate) (-?\d+)", info)
    return (m.group(1), int(m.group(2))) if m else None


def go(exe, outdir, tag, fen, depth):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    ans = e.position("position fen " + fen)
    if any("invalid FEN" in l for l in ans):
        e.close()
        raise AssertionError("%s refused" % tag)
    lines = e.go("go depth %d" % depth, timeout=300)
    e.close()
    return score(last_info(lines)), bestmove_of(lines), last_info(lines)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    builds = [("base", os.path.expanduser("~/b/asan/forge")),
              ("pc", os.path.expanduser("~/b/pc_asan/forge"))]
    R = {}
    rows = ["| build | board | counter | N (counter 0, d20) | 2N-1 | 100-counter | defect? | real score d20 | real score d6 |",
            "|---|---|---|---|---|---|---|---|---|"]

    plans = [("mate1", MATE1, [99, 98, 100]), ("mate3", MATE3, [95, 96])]
    for bname, exe in builds:
        for board_name, tmpl, counters in plans:
            zero_fen = tmpl.format(hm=0)
            sc0, bm0, info0 = go(exe, outdir, "%s_%s_c0" % (bname, board_name), zero_fen, 20)
            N = sc0[1] if sc0 and sc0[0] == "mate" and sc0[1] > 0 else None
            for c in counters:
                if N is None:
                    rows.append("| %s | %s | %d | NO MATE (%s) | – | – | cannot judge | – | – |"
                                % (bname, board_name, c, sc0))
                    continue
                need = 2 * N - 1
                left = 100 - c
                defect = need <= left
                f = tmpl.format(hm=c)
                sc20, bm20, i20 = go(exe, outdir, "%s_%s_%d_d20" % (bname, board_name, c), f, 20)
                sc6, bm6, i6 = go(exe, outdir, "%s_%s_%d_d6" % (bname, board_name, c), f, 6)
                R["%s|%s|%d" % (bname, board_name, c)] = dict(
                    N=N, need=need, left=left, defect=defect, sc20=sc20, sc6=sc6,
                    bm20=bm20, bm6=bm6)
                rows.append("| %s | %s | %d | %s | %d | %d | %s | %s | %s |" % (
                    bname, board_name, c, N, need, left,
                    "YES" if defect else "no", sc20, sc6))

    text = "\n".join(rows)
    # the verdict: is there any case where the rule says defect AND the engine answers cp 0?
    hits = [k for k, v in R.items() if v.get("defect") and v.get("sc20") == ("cp", 0)]
    text += ("\n\nCases where file 6's rule says a DEFECT and the engine still answers cp 0:\n")
    text += ("  none\n" if not hits else "".join("  %s\n" % h for h in hits))
    text += ("\n=> 21-F9 as I originally stated it (counter 100, mate in 1) is %s under file 6's "
             "rule: the mate would land at half-move 101.\n"
             % ("NOT a defect" if (100 + 1) > 100 else "a defect"))
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()