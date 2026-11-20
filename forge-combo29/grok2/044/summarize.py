#!/usr/bin/env python3
"""Read raw honesty and O-run files. Print the numbers. Nothing is typed by hand."""
import sys
from pathlib import Path


def honesty_nodes(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    found = None
    for line in text.splitlines():
        parts = line.split()
        if "bench" in parts and "nodes" in parts:
            found = parts[parts.index("nodes") + 1]
        elif parts[:1] == ["nodes"] and len(parts) >= 2:
            found = parts[1]
    return found


def o_nodes(path):
    nodes = []
    last_info = None
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            parts = (last_info or "").split()
            if "nodes" not in parts:
                nodes.append(None)
            else:
                nodes.append(int(parts[parts.index("nodes") + 1]))
            last_info = None
    return nodes


def show_o(label, path, base=None):
    nodes = o_nodes(path)
    missing = sum(1 for n in nodes if n is None)
    total = sum(n for n in nodes if n is not None)
    first = nodes[:3]
    print(f"{label} positions {len(nodes)} missing {missing} sum {total} first {first[0]} {first[1]} {first[2]}")
    if base is not None:
        differ = sum(1 for a, b in zip(base, nodes) if a != b)
        print(f"{label} differ_from_B {differ}")
    return nodes


def main():
    folder = Path(sys.argv[1])
    print("honesty")
    for tag in ("b", "p"):
        for stem, expect in (
            ("bench11", "312866"),
            ("bench13", "862329"),
            ("bench16", "3024920"),
            ("perft5", "4865609"),
        ):
            got = honesty_nodes(folder / f"honesty_{tag}_{stem}.txt")
            print(f"  {tag} {stem} {got} expected {expect} {'ok' if got == expect else 'MISS'}")
    print("O")
    base = show_o("B", folder / "o_b.txt")
    off = show_o("OFF", folder / "o_off.txt", base)
    show_o("ON", folder / "o_on.txt", base)
    same = off == base
    print(f"OFF_identical_to_B {same}")


if __name__ == "__main__":
    main()
