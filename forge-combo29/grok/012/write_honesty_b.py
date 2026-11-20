#!/usr/bin/env python3
"""Assemble HONESTY_B.txt from the four raw honesty transcripts."""
from pathlib import Path

folder = Path(__file__).resolve().parent
parts = []
for name in ("honesty_b_bench11", "honesty_b_bench13", "honesty_b_bench16", "honesty_b_perft5"):
    text = (folder / f"{name}.txt").read_text().rstrip("\n")
    parts.append(f"## {name}\n{text}")
(folder / "HONESTY_B.txt").write_text("\n".join(parts) + "\n")
print((folder / "HONESTY_B.txt").read_text())
