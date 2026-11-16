#!/usr/bin/env python3
"""job2run.py -- the runs of job 2 (Part A: 4 settings x 4 steps x 2 sets; Part B: 5 settings x 2 sets).

Usage: job2run.py [--part A|B|both]
Writes runs/<set>_<tag>.rows and appends "tag | set | value | sum | nodes-eq | bm-eq" lines to
table_<part>.txt. Compare base: O_S14.rows / G_S14.rows for Part A, and for Part B the B0 rows
of the same set (Part B is also compared against S14, for the B0 row itself).
"""
import argparse
import os
import subprocess
import sys

PART_A = [
    ("NullMoveEvalDivisor", [160, 240, 120, 280]),
    ("RfpDepth", [6, 10, 4, 12]),
    ("FutilityDepth", [5, 9, 3, 11]),
    ("SeeNoisyMultiplier", [126, 174, 102, 198]),
]
PART_B = [
    ("B0", "CaptureFutilityBase=230"),
    ("B1", "CaptureFutilityBase=230;CaptureFutilityMultiplier=225"),
    ("B2", "CaptureFutilityBase=230;CaptureFutilityMultiplier=275"),
    ("B3", "CaptureFutilityBase=230;CaptureFutilityDepth=5"),
    ("B4", "CaptureFutilityBase=230;CaptureFutilityDepth=7"),
]


def run(exe, setfile, out, opts, depth):
    subprocess.run([sys.executable, "rows.py", "--exe", exe, "--set", setfile,
                    "--out", out, "--opts", opts, "--depth", str(depth)],
                   capture_output=True, text=True)


def summarize(base, rf):
    s = subprocess.run([sys.executable, "sumrows.py", rf], capture_output=True, text=True).stdout.strip()
    c = subprocess.run([sys.executable, "cmp2.py", base, rf], capture_output=True, text=True).stdout.strip()
    summ = s.split()[-1] if s and "sum" in s else "REFUSED"
    ne = c.split("nodes-equal")[1].split("of")[0].strip() if "nodes-equal" in c else "?"
    be = c.split("bestmove-equal")[1].split("of")[0].strip() if "bestmove-equal" in c else "?"
    return summ, ne, be


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="both")
    ap.add_argument("--exe", default="/agent/repos/work/build-base/forge")
    ap.add_argument("--depth", type=int, default=12)
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    os.makedirs("runs", exist_ok=True)
    s14 = open("s14.txt").read().strip()

    if args.part in ("A", "both"):
        out = open("table_A.txt", "w", encoding="utf-8")
        for name, values in PART_A:
            for setname in ("O", "G"):
                setfile = "first200.fens" if setname == "O" else "set_G.epd"
                base = "%s_S14.rows" % setname
                for v in values:
                    tag = "%s_A_%s_%d" % (setname, name, v)
                    rf = "runs/%s.rows" % tag
                    run(args.exe, setfile, rf, "%s;%s=%d" % (s14, name, v), args.depth)
                    summ, ne, be = summarize(base, rf)
                    line = "%s | %s | %d | %s | %s | %s" % (tag, setname, v, summ, ne, be)
                    print(line, flush=True)
                    out.write(line + "\n")
                    out.flush()
        out.close()

    if args.part in ("B", "both"):
        out = open("table_B.txt", "w", encoding="utf-8")
        for setname in ("O", "G"):
            setfile = "first200.fens" if setname == "O" else "set_G.epd"
            b0 = "runs/%s_B0.rows" % setname
            for tag, opts in PART_B:
                rf = "runs/%s_%s.rows" % (setname, tag)
                run(args.exe, setfile, rf, "%s;%s" % (s14, opts), args.depth)
                if tag == "B0":
                    summ, ne, be = summarize("%s_S14.rows" % setname, rf)
                    line = "%s | %s | vs S14 | %s | %s | %s" % (tag, setname, summ, ne, be)
                else:
                    summ, ne, be = summarize(b0, rf)
                    line = "%s | %s | vs B0 | %s | %s | %s" % (tag, setname, summ, ne, be)
                print(line, flush=True)
                out.write(line + "\n")
                out.flush()
        out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
