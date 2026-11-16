#!/usr/bin/env python3
"""check_findings.py — validate that every finding row in FINDINGS.md has the right cell count.

The table header declares 5 columns: | id | area | finding | evidence | state |
A check row (S-C) may use 5 cells too, with the verdict in the second cell.

A cell may contain a literal pipe only if it is escaped as \\| ; an unescaped one starts a new cell.
This script counts ONLY unescaped pipes, which is what a markdown renderer does.

Usage: python3 check_findings.py PATH [--fix]
  --fix  escapes the single extra unescaped pipe in any row that has exactly 7, choosing the one that is
         NOT one of the six structural delimiters.
"""
import re
import sys

HEADER_CELLS = 5


def unescaped_pipes(line):
    return [m.start() for m in re.finditer(r"(?<!\\)\|", line)]


def main():
    path = sys.argv[1]
    do_fix = "--fix" in sys.argv
    lines = open(path).read().splitlines(True)
    out = []
    bad = []
    fixed = 0
    for i, raw in enumerate(lines, 1):
        if not raw.startswith("| 04-"):
            out.append(raw)
            continue
        core = raw.rstrip("\n")
        idx = unescaped_pipes(core)
        # A well-formed row: opening pipe, then (cells-1) interior pipes, then closing pipe
        # = 1 + (HEADER_CELLS - 1) + 1 = HEADER_CELLS + 1 unescaped pipes.
        want = HEADER_CELLS + 1
        if len(idx) == want:
            out.append(raw)
            continue
        if do_fix and len(idx) == want + 1:
            # The structural pipes are the first (opening + 5) and the last (closing).
            # With one extra, the stray is the one that is NOT first, second..., penultimate, last.
            structural = [idx[0], idx[1], idx[2], idx[3], idx[4], idx[5], idx[6]] if len(idx) == 7 else idx
            # for 7 pipes on a 5-cell row, structural = idx[0], idx[1], idx[2], idx[3], idx[5], idx[6]
            if len(idx) == 7:
                structural = [idx[0], idx[1], idx[2], idx[3], idx[5], idx[6]]
            stray = [p for p in idx if p not in structural]
            if len(stray) == 1:
                e = stray[0]
                core = core[:e] + "\\" + core[e:]
                out.append(core + "\n")
                fixed += 1
                continue
        bad.append((i, core.split("|")[1].strip(), len(idx)))
        out.append(raw)
    if do_fix and fixed:
        open(path, "w").write("".join(out))
    print("rows checked: %d" % sum(1 for l in lines if l.startswith("| 04-")))
    if fixed:
        print("rows fixed: %d" % fixed)
    if bad:
        print("MALFORMED (unescaped pipe count != %d):" % (HEADER_CELLS + 1))
        for i, ident, n in bad:
            print("   line %d  %s  pipes=%d" % (i, ident, n))
        sys.exit(1)
    print("OK: every row has %d unescaped pipes (5 cells)" % (HEADER_CELLS + 1))


if __name__ == "__main__":
    main()
