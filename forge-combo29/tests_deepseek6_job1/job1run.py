#!/usr/bin/env python3
"""job1run.py -- the 70 runs of job 1 (35 settings x {-c,+c}) on one set.

Usage: job1run.py --set O|G [--only "Name1,Name2"] [--tag-suffix S]
Writes one rows file per run into runs/, and appends one summary line per run to
table_<set>.txt: "setting | value | c | -c | sum(-c) | nodes-eq(-c) | best-eq(-c)
| +c | sum(+c) | nodes-eq(+c) | best-eq(+c)". The base rows file is
O_S14_base.rows / G_S14_base.rows in this folder.
"""
import argparse
import os
import subprocess
import sys

# setting, value, c, run-at-minus, run-at-plus -- exactly job 1's table
TABLE = [
    ("LmrQuietBase", 93, 8, 85, 101),
    ("LmrQuietDivisor", 205, 12, 193, 217),
    ("LmrNoisyBase", 13, 6, 7, 19),
    ("LmrNoisyDivisor", 333, 20, 313, 353),
    ("NullMoveBase", 5, 1, 4, 6),
    ("NullMoveDepthDivisor", 3, 1, 2, 4),
    ("NullMoveEvalDivisor", 200, 20, 180, 220),
    ("RfpDepth", 8, 1, 7, 9),
    ("RfpMargin", 72, 6, 66, 78),
    ("RfpImproving", 40, 6, 34, 46),
    ("RazorBase", 150, 20, 130, 170),
    ("RazorMultiplier", 350, 25, 325, 375),
    ("FutilityDepth", 7, 1, 6, 8),
    ("FutilityBase", 100, 12, 88, 112),
    ("FutilityMultiplier", 110, 10, 100, 120),
    ("LmpBase", 8, 1, 7, 9),
    ("HistoryPruneMultiplier", 2220, 200, 2020, 2420),
    ("SeeQuietMultiplier", 24, 3, 21, 27),
    ("SeeNoisyMultiplier", 150, 12, 138, 162),
    ("SingularDepth", 6, 1, 5, 7),
    ("SingularMargin", 2, 1, 1, 3),
    ("IirDepth", 2, 1, 1, 3),
    ("ProbcutDepth", 5, 1, 4, 6),
    ("ProbcutMargin", 180, 15, 165, 195),
    ("QsFutilityMargin", 160, 14, 146, 174),
    ("QsSeeMargin", 40, 6, 34, 46),
    ("AspirationDelta", 18, 2, 16, 20),
    ("HistoryBonusQuadratic", 24, 3, 21, 27),
    ("HistoryBonusLinear", 54, 6, 48, 60),
    ("HistoryBonusMax", 2212, 180, 2032, 2392),
    ("LmrHistoryDivisor", 5643, 500, 5143, 6143),
    ("LmrCutoffThreshold", 3, 1, 2, 4),
    ("MaterialCorrectionWeight", 100, 10, 90, 110),
    ("CaptureFutilityMultiplier", 250, 25, 225, 275),
    ("CaptureFutilityDepth", 6, 1, 5, 7),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=["O", "G"])
    ap.add_argument("--exe", default="/agent/repos/work/build-base/forge")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--only", default="")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    setfile = "first200.fens" if args.set == "O" else "set_G.epd"
    base = "%s_S14_base.rows" % args.set
    s14 = open("s14.txt").read().strip()
    only = [x for x in args.only.split(",") if x]
    os.makedirs("runs", exist_ok=True)
    out = open("table_%s%s.txt" % (args.set, args.tag), "a", encoding="utf-8")

    for name, value, c, lo, hi in TABLE:
        if only and name not in only:
            continue
        cells = []
        for v in (lo, hi):
            tag = "%s_%s_%d%s" % (args.set, name, v, args.tag)
            rf = "runs/%s.rows" % tag
            opts = "%s;%s=%d" % (s14, name, v)
            subprocess.run([sys.executable, "rows.py", "--exe", args.exe, "--set", setfile,
                            "--out", rf, "--opts", opts, "--depth", str(args.depth)],
                           capture_output=True, text=True)
            s = subprocess.run([sys.executable, "sumrows.py", rf],
                               capture_output=True, text=True).stdout.strip()
            summ = s.split()[-1] if s else "REFUSED"
            cmp = subprocess.run([sys.executable, "cmp2.py", base, rf],
                                 capture_output=True, text=True).stdout.strip()
            ne = cmp.split("nodes-equal")[1].split("of")[0].strip() if "nodes-equal" in cmp else "?"
            be = cmp.split("bestmove-equal")[1].split("of")[0].strip() if "bestmove-equal" in cmp else "?"
            cells.append((v, summ, ne, be))
        line = "%s | %d | %d | %d | %s | %s | %s | %d | %s | %s | %s" % (
            name, value, c, cells[0][0], cells[0][1], cells[0][2], cells[0][3],
            cells[1][0], cells[1][1], cells[1][2], cells[1][3])
        print(line, flush=True)
        out.write(line + "\n")
        out.flush()
    out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
