#!/usr/bin/env python3
"""sancount.py -- count sanitizer lines in a sanrun.py rows file or raw log.

Usage: sancount.py FILE [FILE...]
For a rows file (from sanrun.py) it prints per-position and total sanitizer counts.
For a raw log it counts matching lines directly.
Prints exactly one summary line per file: "<file>: sanlines N (positions M)".
"""
import re
import sys

SAN_PAT = re.compile(r"AddressSanitizer|LeakSanitizer|SUMMARY:|runtime error|UndefinedBehaviorSanitizer")


def count_rows(path):
    total = 0
    positions = 0
    worst = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("# totals:"):
                continue
            if not line or line.startswith("#"):
                continue
            p = [x.strip() for x in line.split("|")]
            if len(p) < 5:
                continue
            positions += 1
            n = int(p[3])
            total += n
            if n:
                worst.append((p[0], n, p[4]))
    return total, positions, worst


def count_raw(path):
    total = 0
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if SAN_PAT.search(line):
                total += 1
    return total


def main():
    if len(sys.argv) < 2:
        print("usage: sancount.py FILE [FILE...]", file=sys.stderr)
        return 64
    for path in sys.argv[1:]:
        try:
            total, positions, worst = count_rows(path)
            if positions == 0:
                total = count_raw(path)
                print("%s: sanlines %d (raw log)" % (path, total))
            else:
                print("%s: sanlines %d (positions %d)" % (path, total, positions))
                if worst:
                    print("  positions with reports: %s" % worst[:10])
        except (ValueError, IndexError):
            print("%s: sanlines %d (raw log)" % (path, count_raw(path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
