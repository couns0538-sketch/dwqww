#!/usr/bin/env python3
"""Read the raw honesty files and write HONESTY_B.txt. Numbers come from the files."""
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
    raw = (here / f"honesty_B_{name}.txt").read_text()
    found = [int(m.group(1)) for m in re.finditer(r"nodes (\d+)", raw)]
    got = found[-1] if found else None
    match = got == want
    ok = ok and match
    lines.append(f"{name} nodes {got} expected {want} match {str(match).lower()}")
lines.append(f"all_match {str(ok).lower()}")
(here / "HONESTY_B.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
