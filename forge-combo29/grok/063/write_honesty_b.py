#!/usr/bin/env python3
"""Build HONESTY_B.txt from the raw bench and perft files. Do not type the numbers."""
import pathlib
import re

here = pathlib.Path(__file__).resolve().parent
expected = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
lines = []
ok = True
for name, want in expected.items():
    text = (here / f"{name}.txt").read_text()
    found = [int(n) for n in re.findall(r"nodes (\d+)", text)]
    got = found[-1] if found else None
    match = got == want
    ok = ok and match
    lines.append(f"{name} nodes {got} expected {want} match {str(match).lower()}")
lines.append(f"honesty_b {str(ok).lower()}")
(here / "HONESTY_B.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
