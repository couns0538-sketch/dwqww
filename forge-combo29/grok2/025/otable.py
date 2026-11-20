#!/usr/bin/env python3
"""otable.py BASE.txt OFF.txt ON.txt
Reads raw orun transcripts. One row per position: index and the nodes of
the last info line before bestmove. Prints sums, the first three, and how
many ON rows differ from BASE.
"""
import sys


def rows(path):
    found = []
    last_info = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith(">> "):
            continue
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None or " nodes " not in last_info:
                sys.exit(f"STOP: no info nodes before bestmove in {path}")
            nodes = int(last_info.split(" nodes ")[1].split()[0])
            found.append(nodes)
            last_info = None
    return found


def show(name, vals):
    head = " / ".join(str(v) for v in vals[:3])
    print(f"{name}: n {len(vals)} sum {sum(vals)} first {head}")


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: otable.py BASE.txt OFF.txt ON.txt")
    base, off, on = (rows(p) for p in sys.argv[1:])
    if not (len(base) == len(off) == len(on) == 200):
        sys.exit(f"STOP: expected 200 rows, got {len(base)} {len(off)} {len(on)}")
    show("B", base)
    show("Poff", off)
    show("Pon", on)
    same = sum(1 for a, b in zip(base, off) if a == b)
    differ = sum(1 for a, b in zip(base, on) if a != b)
    print(f"off_identical {same} of {len(base)}")
    print(f"on_differ {differ} of {len(base)}")


if __name__ == "__main__":
    main()
