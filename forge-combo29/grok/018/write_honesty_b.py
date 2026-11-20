#!/usr/bin/env python3
"""Paste the honesty lines from the raw bench and perft files."""
import pathlib
import sys

folder = pathlib.Path(sys.argv[1])
parts = []
for name in ("honesty_b_bench11.txt", "honesty_b_bench13.txt", "honesty_b_bench16.txt", "honesty_b_perft5.txt"):
    text = (folder / name).read_text(encoding="utf-8")
    parts.append("===== " + name + " =====\n" + text)
    if not text.endswith("\n"):
        parts.append("\n")
(folder / "HONESTY_B.txt").write_text("".join(parts), encoding="utf-8")
for line in (folder / "HONESTY_B.txt").read_text(encoding="utf-8").splitlines():
    if "nodes " in line and ("bench depth" in line or line.startswith("nodes ")):
        print(line)
