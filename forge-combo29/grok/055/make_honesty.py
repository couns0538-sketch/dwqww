#!/usr/bin/env python3
"""Print HONESTY_B.txt from the raw bench and perft files. Nothing is typed by hand."""
import pathlib
import re
import sys

folder = pathlib.Path(__file__).resolve().parent
expected = {
    "honesty_b_bench11.txt": 312866,
    "honesty_b_bench13.txt": 862329,
    "honesty_b_bench16.txt": 3024920,
    "honesty_b_perft5.txt": 4865609,
}
node_re = re.compile(r"nodes (\d+)")
failed = False
for name, want in expected.items():
    text = (folder / name).read_text()
    found = [int(n) for n in node_re.findall(text)]
    got = found[-1] if found else None
    status = "OK" if got == want else "MISS"
    if got != want:
        failed = True
    label = name.removeprefix("honesty_b_").removesuffix(".txt")
    print(f"{label} nodes {got} expected {want} {status}")
print("HONESTY_B " + ("PASS" if not failed else "FAIL"))
sys.exit(1 if failed else 0)
