#!/usr/bin/env python3
"""o_table.py one RAW.txt
   o_table.py compare RAW_A.txt RAW_B.txt

Reads harness transcripts. One row per position: its number and the nodes of
the last info line before bestmove. compare counts positions whose nodes differ.
"""
import re
import sys


def rows(path):
    found = []
    last_info = None
    go_seen = False
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if line == ">> go depth 12":
            go_seen = True
            last_info = None
            continue
        if not go_seen:
            continue
        if line.startswith("info "):
            last_info = line
            continue
        if line.startswith("bestmove "):
            if last_info is None:
                sys.exit(f"STOP: bestmove with no info line in {path} position {len(found) + 1}")
            match = re.search(r" nodes (\d+)", last_info)
            if not match:
                sys.exit(f"STOP: last info has no nodes in {path} position {len(found) + 1}: {last_info}")
            found.append(int(match.group(1)))
            go_seen = False
            last_info = None
    if not found:
        sys.exit(f"STOP: no positions in {path}")
    return found


def show(path):
    got = rows(path)
    print(f"file {path}")
    print(f"positions {len(got)}")
    print(f"sum {sum(got)}")
    print("first " + " ".join(str(n) for n in got[:3]))
    for i, n in enumerate(got, start=1):
        print(f"{i} {n}")
    return got


def main():
    if sys.argv[1] == "one":
        show(sys.argv[2])
    elif sys.argv[1] == "compare":
        a = rows(sys.argv[2])
        b = rows(sys.argv[3])
        if len(a) != len(b):
            sys.exit(f"STOP: length {len(a)} != {len(b)}")
        differ = [i for i, (x, y) in enumerate(zip(a, b), start=1) if x != y]
        print(f"positions {len(a)}")
        print(f"differ {len(differ)}")
        print("equal" if not differ else "not_equal")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
