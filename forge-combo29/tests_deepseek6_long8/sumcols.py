#!/usr/bin/env python3
"""sumcols.py -- sum the nodes column (field 2) of sanrun.py rows files.

Usage: sumcols.py FILE [FILE...]
Prints "<file> rows N sum S sanlines K" per file. One committed command.
"""
import sys

def main():
    for path in sys.argv[1:]:
        n = s = k = 0
        for line in open(path, encoding="utf-8"):
            if line.startswith("#") or not line.strip():
                continue
            p = [x.strip() for x in line.split("|")]
            if len(p) < 4:
                continue
            n += 1; s += int(p[1]); k += int(p[3])
        print("%s rows %d sum %d sanlines %d" % (path, n, s, k))
    return 0

if __name__ == "__main__":
    sys.exit(main())
