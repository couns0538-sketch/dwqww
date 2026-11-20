#!/usr/bin/env python3
"""honesty_table.py DIR TAG
Print bench/perft node counts from the raw honesty files.
"""
import sys
from pathlib import Path

DIR = Path(sys.argv[1])
TAG = sys.argv[2]
EXPECT = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}


def bench_nodes(text):
    found = None
    for line in text.splitlines():
        if "bench depth" in line and " nodes " in line:
            found = int(line.split(" nodes ", 1)[1].split()[0])
    if found is None:
        raise SystemExit("STOP: no bench nodes in file")
    return found


def perft_nodes(text):
    found = None
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == "nodes" and parts[1].isdigit():
            found = int(parts[1])
    if found is None:
        raise SystemExit("STOP: no perft nodes in file")
    return found


for label, expect in EXPECT.items():
    text = (DIR / f"honesty_{TAG}_{label}.txt").read_text(encoding="utf-8")
    got = perft_nodes(text) if label == "perft5" else bench_nodes(text)
    mark = "MATCH" if got == expect else "MISS"
    print(f"{TAG} {label} nodes {got} expect {expect} {mark}")
