#!/usr/bin/env python3
"""cexsum.py -- sum a job-5 .cex counters file and print the per-depth table.

Usage: cexsum.py COUNTERSFILE
Prints one line per depth: "d <D> reached <n> see_neg <n> ext <n> would2 <n> would8 <n>
beat <n> subnodes <n>", then "lines <N>", "mismatch <n>", the totals, and the two
shares the job asks for (ext at depth 2..7, sub_nodes at depth 2..7).
"""
import re
import sys

FIELD = re.compile(r"\bd(\d+) r (\d+) s (\d+) e (\d+) w2 (\d+) w8 (\d+) b (\d+) n (\d+)")
MISMATCH = re.compile(r"\bmismatch (\d+)")


def main():
    if len(sys.argv) < 2:
        print("usage: cexsum.py COUNTERSFILE", file=sys.stderr)
        return 64
    keys = ["r", "s", "e", "w2", "w8", "b", "n"]
    acc = {d: dict.fromkeys(keys, 0) for d in range(16)}
    mism = 0
    lines = 0
    for path in sys.argv[1:]:
        for line in open(path, encoding="utf-8"):
            if "cex" not in line:
                continue
            lines += 1
            for m in FIELD.finditer(line):
                d = int(m.group(1))
                if 1 <= d <= 15:
                    vals = [int(x) for x in m.groups()[1:]]
                    for k, v in zip(keys, vals):
                        acc[d][k] += v
            m = MISMATCH.search(line)
            if m:
                mism += int(m.group(1))
    for d in range(1, 16):
        a = acc[d]
        print("d %2d reached %8d see_neg %7d ext %7d would2 %7d would8 %7d beat %7d subnodes %10d"
              % (d, a["r"], a["s"], a["e"], a["w2"], a["w8"], a["b"], a["n"]))
    tot_ext = sum(acc[d]["e"] for d in range(1, 16))
    ext_27 = sum(acc[d]["e"] for d in range(2, 8))
    sub_27 = sum(acc[d]["n"] for d in range(2, 8))
    print("lines %d" % lines)
    print("mismatch %d" % mism)
    print("ext total %d" % tot_ext)
    print("ext at depth 2..7 %d (%.1f %% of ext)" % (ext_27, 100.0 * ext_27 / tot_ext if tot_ext else 0.0))
    print("ext at depth 2 alone %d (%.1f %% of ext)"
          % (acc[2]["e"], 100.0 * acc[2]["e"] / tot_ext if tot_ext else 0.0))
    print("subnodes depth 2..7 %d" % sub_27)
    for d in range(2, 8):
        a = acc[d]
        print("beat rate d%d %d/%d = %.1f %%" % (d, a["b"], a["e"], 100.0 * a["b"] / a["e"] if a["e"] else 0.0))
    sh_e = sum(acc[d]["e"] for d in range(2, 8))
    sh_b = sum(acc[d]["b"] for d in range(2, 8))
    dp_e = sum(acc[d]["e"] for d in range(8, 16))
    dp_b = sum(acc[d]["b"] for d in range(8, 16))
    print("beat rate shallow (d2..7) %d/%d = %.1f %%" % (sh_b, sh_e, 100.0 * sh_b / sh_e if sh_e else 0.0))
    print("beat rate deep (d8..15) %d/%d = %.1f %%" % (dp_b, dp_e, 100.0 * dp_b / dp_e if dp_e else 0.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
