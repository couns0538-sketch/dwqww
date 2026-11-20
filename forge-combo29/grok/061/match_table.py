#!/usr/bin/env python3
"""Print the last fastchess results block from a raw log."""

import sys

lines = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
starts = [i for i, line in enumerate(lines) if line.startswith("Results of ")]
if not starts:
    print("NO_RESULTS")
    sys.exit(1)
for line in lines[starts[-1] : starts[-1] + 8]:
    if line.startswith("-----") and line != lines[starts[-1] + 1]:
        break
    print(line)
print("finished", sum(1 for line in lines if line.startswith("Finished game ")))
