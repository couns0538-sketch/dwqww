#!/usr/bin/env python3
"""job1table.py -- print the job-1 tables straight from the rows files.

Usage: job1table.py [O|G]
For every setting in job 1's table it reads runs/<set>_<name>_<value>.rows for the
two ends, sums the nodes with sumrows.py's rule, and compares with the S14 base
rows through cmp2.py's rule. Nothing is typed by hand: this command is the source
of every table cell in REPORT_deepseek6_job1.md.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from job1run import TABLE  # the single definition of the job's table, reused


def sum_nodes(path):
    total = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            p = [x.strip() for x in line.split("|")]
            if len(p) >= 3:
                total += int(p[1])
    return total


def cmp_counts(base, test):
    def load(p):
        d = {}
        for line in open(p, encoding="utf-8"):
            if line.startswith("#") or not line.strip():
                continue
            f = [x.strip() for x in line.split("|")]
            if len(f) >= 3:
                d[int(f[0])] = (f[1], f[2])
        return d
    a, b = load(base), load(test)
    common = [k for k in a if k in b]
    ne = sum(1 for k in common if a[k][0] == b[k][0])
    be = sum(1 for k in common if a[k][1] == b[k][1])
    return ne, be, len(common)


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "O"
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    base = "%s_S14_base.rows" % which
    print("| setting | value | c | -c | %s -c sum | nodes-eq | bm-eq | +c | %s +c sum | nodes-eq | bm-eq |"
          % (which, which))
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    n_equal = 0
    for name, value, c, lo, hi in TABLE:
        cells = []
        for v in (lo, hi):
            f = "runs/%s_%s_%d.rows" % (which, name, v)
            if not os.path.exists(f):
                cells.append((v, "MISSING", "?", "?"))
                continue
            ne, be, tot = cmp_counts(base, f)
            cells.append((v, "{:,}".format(sum_nodes(f)), str(ne), str(be)))
        both = cells[0][2] == cells[1][2] and cells[0][2].isdigit() and cells[0][3] == cells[1][3] and cells[0][3].isdigit()
        if cells[0][2] == cells[1][2] == "200" or cells[0][2] == cells[1][2] == "353":
            n_equal += 1
        print("| %s%s | %d | %d | %d | %s | %s | %s | %d | %s | %s | %s |"
              % (name, "**" if (cells[0][2] in ("200", "353") and cells[1][2] in ("200", "353")) else "",
                 value, c, cells[0][0], cells[0][1], cells[0][2], cells[0][3],
                 cells[1][0], cells[1][1], cells[1][2], cells[1][3]))
    print()
    print("settings equal at both ends on %s: %d" % (which, n_equal))
    return 0


if __name__ == "__main__":
    sys.exit(main())
