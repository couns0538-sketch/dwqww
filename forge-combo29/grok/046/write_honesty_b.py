#!/usr/bin/env python3
"""Paste the four honesty raw files into HONESTY_B.txt."""
from pathlib import Path

here = Path(__file__).resolve().parent
parts = []
for name in ("bench11", "bench13", "bench16", "perft5"):
    parts.append(f"===== {name} =====\n")
    text = (here / f"honesty_b_{name}.txt").read_text()
    parts.append(text)
    if not text.endswith("\n"):
        parts.append("\n")
(here / "HONESTY_B.txt").write_text("".join(parts))
print((here / "HONESTY_B.txt").read_text())
