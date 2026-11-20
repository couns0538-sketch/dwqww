#!/usr/bin/env python3
"""Compare a run_set tsv with either another tsv or a one-number-per-line file."""
import sys
from pathlib import Path

def load(path):
    lines = [line for line in Path(path).read_text().splitlines() if line.strip()]
    if lines and lines[0].startswith("index\t"):
        rows = []
        for line in lines[1:]:
            if line.startswith("SUM"):
                continue
            rows.append(int(line.split("\t")[1]))
        return rows
    return [int(line.strip()) for line in lines]

a = load(sys.argv[1])
b = load(sys.argv[2])
n = min(len(a), len(b))
differ = sum(x != y for x, y in zip(a[:n], b[:n]))
print(f"file_a={sys.argv[1]}")
print(f"file_b={sys.argv[2]}")
print(f"positions_a={len(a)} positions_b={len(b)} compared={n} differ={differ} sum_a={sum(a)} sum_b={sum(b)}")
