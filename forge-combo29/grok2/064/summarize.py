#!/usr/bin/env python3
"""Print the honesty numbers and the three O-run rows from the raw files.

Reads only the text files this harness wrote. The known targets are the
constants from the swarm brief (arm 4, IdeaB8, source seat 028), printed beside
the measured values so a miss is visible.
"""

import os
import sys

EXPECTED_HONESTY = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}

# Arm 4, run (3): sum; first three; positions that differ from exe B.
EXPECTED_ON = (9718009, (17283, 17878, 31115), 200)
EXPECTED_OFF_SUM = 9500069
EXPECTED_OFF_FIRST = (41311, 24872, 28574)


def nodes_after(line):
    parts = line.split()
    return int(parts[parts.index("nodes") + 1])


def read_lines(path):
    with open(path, encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle]


def honesty_nodes(path, kind):
    lines = read_lines(path)
    if kind == "perft5":
        found = [nodes_after(line) for line in lines if line.startswith("nodes ")]
        if len(found) != 1:
            raise SystemExit(f"STOP {path} has {len(found)} perft node lines")
        return found[0]
    prefix = {
        "bench11": "info string bench depth 11 nodes ",
        "bench13": "info string bench depth 13 nodes ",
        "bench16": "info string bench depth 16 nodes ",
    }[kind]
    found = [nodes_after(line) for line in lines if line.startswith(prefix)]
    if len(found) != 1:
        raise SystemExit(f"STOP {path} has {len(found)} bench lines")
    return found[0]


def search_nodes(path):
    lines = read_lines(path)
    counts = []
    block = []
    for line in lines:
        block.append(line)
        if line.startswith("bestmove "):
            info = [item for item in block if item.startswith("info ")]
            if not info:
                raise SystemExit(f"STOP {path} bestmove {len(counts) + 1} has no info line")
            last = info[-1]
            if " nodes " not in last.split():
                # "nodes" as its own token
                if "nodes" not in last.split():
                    raise SystemExit(f"STOP {path} last info has no nodes: {last}")
            counts.append(nodes_after(last))
            block = []
    return counts


def main():
    folder = sys.argv[1]
    print("honesty")
    for tag in ("B", "P"):
        for kind, expected in EXPECTED_HONESTY.items():
            path = os.path.join(folder, f"honesty_{tag}_{kind}.txt")
            got = honesty_nodes(path, kind)
            print(f"{tag} {kind} {got} expected {expected} {'ok' if got == expected else 'MISS'}")
    off = search_nodes(os.path.join(folder, "o1_B.txt"))
    same = search_nodes(os.path.join(folder, "o2_off.txt"))
    on = search_nodes(os.path.join(folder, "o3_on.txt"))
    print(f"o1 positions {len(off)} sum {sum(off)} first {off[0]} {off[1]} {off[2]}")
    print(f"o1 expected sum {EXPECTED_OFF_SUM} first {' '.join(str(n) for n in EXPECTED_OFF_FIRST)}")
    differ_off = sum(1 for a, b in zip(off, same) if a != b)
    print(f"o2 positions {len(same)} sum {sum(same)} first {same[0]} {same[1]} {same[2]} differ_from_o1 {differ_off}")
    differ_on = sum(1 for a, b in zip(off, on) if a != b)
    print(f"o3 positions {len(on)} sum {sum(on)} first {on[0]} {on[1]} {on[2]} differ_from_o1 {differ_on}")
    exp_sum, exp_first, exp_differ = EXPECTED_ON
    print(f"o3 expected sum {exp_sum} first {' '.join(str(n) for n in exp_first)} differ {exp_differ}")
    print(f"o1_match {sum(off) == EXPECTED_OFF_SUM and tuple(off[:3]) == EXPECTED_OFF_FIRST}")
    print(f"o2_match {off == same}")
    print(f"o3_match {sum(on) == exp_sum and tuple(on[:3]) == exp_first and differ_on == exp_differ}")


if __name__ == "__main__":
    main()
