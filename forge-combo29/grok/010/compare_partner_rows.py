#!/usr/bin/env python3
"""Compare my measure_depth .rows nodes to a partner tsv (index, nodes, ...)."""
import sys

def nodes(path, col):
    out = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= col or not parts[col].isdigit():
                continue
            out.append(int(parts[col]))
    return out

def main():
    mine = nodes(sys.argv[1], 1)
    theirs = nodes(sys.argv[2], 1)
    n = min(len(mine), len(theirs))
    differ = sum(1 for i in range(n) if mine[i] != theirs[i])
    print("mine %d theirs %d compared %d differ %d" % (len(mine), len(theirs), n, differ))
    print("mine_sum %d theirs_sum %d" % (sum(mine), sum(theirs)))
    if mine[:3] or theirs[:3]:
        print("mine_first %s" % " ".join(str(x) for x in mine[:3]))
        print("theirs_first %s" % " ".join(str(x) for x in theirs[:3]))
    return 0 if len(mine) == len(theirs) else 1

if __name__ == "__main__":
    sys.exit(main())
