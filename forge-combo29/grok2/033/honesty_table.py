#!/usr/bin/env python3
"""Print the node line from each honesty raw file."""
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
for name in (
    "honesty_B_bench11.txt",
    "honesty_B_bench13.txt",
    "honesty_B_bench16.txt",
    "honesty_B_perft5.txt",
    "honesty_P_bench11.txt",
    "honesty_P_bench13.txt",
    "honesty_P_bench16.txt",
    "honesty_P_perft5.txt",
):
    text = (root / name).read_text(encoding="utf-8")
    hit = [ln for ln in text.splitlines() if "nodes " in ln]
    print(f"{name}: {hit[-1] if hit else 'MISSING'}")
