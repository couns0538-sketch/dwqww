#!/usr/bin/env python3
"""o_table.py RAW [RAW ...]

Reads engine transcripts. One search ends at a bestmove line. The nodes of a
search are the nodes field of the last info line before that bestmove.
Prints one row per position and a sum line. With two or more files, prints how
many positions differ from the first file.
"""
import re
import sys

NODE_RE = re.compile(r" nodes (\d+) ")
EXPECTED_OFF_SUM = 9500069
EXPECTED_OFF_FIRST = (41311, 24872, 28574)
EXPECTED_ON_SUM = 9547450
EXPECTED_ON_FIRST = (41442, 24989, 28711)
EXPECTED_ON_DIFFER = 200


def searches(path):
    nodes = []
    pending = []
    bestmoves = 0
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            text = line.rstrip("\n")
            if text.startswith("bestmove "):
                bestmoves += 1
                info = [item for item in pending if item.startswith("info ")]
                if not info:
                    sys.exit(f"{path}: bestmove {bestmoves} has no info line")
                match = NODE_RE.search(info[-1])
                if match is None:
                    sys.exit(f"{path}: last info before bestmove {bestmoves} has no nodes: {info[-1]}")
                nodes.append(int(match.group(1)))
                pending = []
            else:
                pending.append(text)
    if bestmoves != 200:
        sys.exit(f"{path}: expected 200 bestmove lines, got {bestmoves}")
    return nodes


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: o_table.py RAW [RAW ...]")
    series = [(path, searches(path)) for path in sys.argv[1:]]
    base_name, base = series[0]
    for path, nodes in series:
        print(f"file {path}")
        for index, value in enumerate(nodes, start=1):
            print(f"{index} {value}")
        print(f"sum {sum(nodes)} first {nodes[0]} {nodes[1]} {nodes[2]} count {len(nodes)}")
        if path != base_name:
            differ = sum(1 for a, b in zip(base, nodes) if a != b)
            print(f"differ_from {base_name} {differ}")
        print()
    if len(series) >= 1:
        nodes = series[0][1]
        off_ok = (
            sum(nodes) == EXPECTED_OFF_SUM
            and tuple(nodes[:3]) == EXPECTED_OFF_FIRST
        )
        print(f"known_off_match {str(off_ok).lower()} sum {sum(nodes)} first {nodes[0]} {nodes[1]} {nodes[2]}")
    if len(series) >= 2:
        same = series[0][1] == series[1][1]
        print(f"off_identical {str(same).lower()}")
    if len(series) >= 3:
        nodes = series[2][1]
        differ = sum(1 for a, b in zip(series[0][1], nodes) if a != b)
        on_ok = (
            sum(nodes) == EXPECTED_ON_SUM
            and tuple(nodes[:3]) == EXPECTED_ON_FIRST
            and differ == EXPECTED_ON_DIFFER
        )
        print(
            f"known_on_match {str(on_ok).lower()} sum {sum(nodes)} "
            f"first {nodes[0]} {nodes[1]} {nodes[2]} differ {differ}"
        )


if __name__ == "__main__":
    main()
