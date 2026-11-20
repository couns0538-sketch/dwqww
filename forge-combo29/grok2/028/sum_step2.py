#!/usr/bin/env python3
"""sum_step2.py DIR

Reads the raw honesty and O-run files in DIR and prints the tables.
"""
import sys
from pathlib import Path


def nodes_of_info(line):
    parts = line.split()
    if "nodes" not in parts:
        return None
    i = parts.index("nodes")
    if i + 1 >= len(parts):
        return None
    return int(parts[i + 1])


def honesty_nodes(path, kind):
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if kind == "perft":
        hits = [int(line.split()[1]) for line in text if line.startswith("nodes ")]
        if len(hits) != 1:
            return f"MISS lines={len(hits)}"
        return str(hits[0])
    hits = []
    for line in text:
        if line.startswith("info string bench depth "):
            hits.append(nodes_of_info(line))
    if len(hits) != 1 or hits[0] is None:
        return f"MISS lines={len(hits)}"
    return str(hits[0])


def o_nodes(path):
    rows = []
    last_info = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None:
                rows.append(None)
            else:
                rows.append(nodes_of_info(last_info))
            last_info = None
    return rows


def main():
    d = Path(sys.argv[1])
    print("honesty")
    for tag in ("B", "P"):
        for name, kind in (("bench11", "bench"), ("bench13", "bench"), ("bench16", "bench"), ("perft5", "perft")):
            path = d / f"honesty_{tag}_{name}.txt"
            got = honesty_nodes(path, kind) if path.exists() else "MISSING FILE"
            print(f"  {tag} {name} {got}")
    print("o runs")
    b_path = d / "o_B.txt"
    off_path = d / "o_P_off.txt"
    on_path = d / "o_P_on.txt"
    if not b_path.exists():
        print("  o_B MISSING FILE")
        return
    b = o_nodes(b_path)
    print(f"  B positions {len(b)} sum {sum(x or 0 for x in b)} first {b[:3]}")
    if off_path.exists():
        off = o_nodes(off_path)
        differ = sum(1 for x, y in zip(b, off) if x != y)
        length_note = "" if len(off) == len(b) else f" length {len(off)}"
        print(f"  P_off positions {len(off)} sum {sum(x or 0 for x in off)} first {off[:3]} differ_from_B {differ}{length_note}")
    else:
        print("  o_P_off MISSING FILE")
    if on_path.exists():
        on = o_nodes(on_path)
        differ = sum(1 for x, y in zip(b, on) if x != y)
        length_note = "" if len(on) == len(b) else f" length {len(on)}"
        print(f"  P_on positions {len(on)} sum {sum(x or 0 for x in on)} first {on[:3]} differ_from_B {differ}{length_note}")
    else:
        print("  o_P_on MISSING FILE")


if __name__ == "__main__":
    main()
