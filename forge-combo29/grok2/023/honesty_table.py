#!/usr/bin/env python3
import glob, os, sys
folder = sys.argv[1]
paths = sorted(glob.glob(os.path.join(folder, "honesty_*.txt")))
for path in paths:
    base = os.path.basename(path)
    if base == "honesty_table.txt" or path.endswith(".meta"):
        continue
    last = None
    for line in open(path, encoding="utf-8"):
        if line.startswith("info string bench ") or line.startswith("nodes "):
            last = line.rstrip("\n")
    print("%s %s" % (os.path.basename(path), last))
