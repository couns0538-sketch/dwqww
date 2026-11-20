#!/usr/bin/env python3
"""Print the evidence tables for REPORT.md from the raw files in this folder."""
import re
from pathlib import Path

here = Path(__file__).resolve().parent


def rows(name):
    return [int(x) for x in (here / name).read_text().split()]


def compare(left_name, right_name):
    left, right = rows(left_name), rows(right_name)
    n = min(len(left), len(right))
    differ = sum(1 for i in range(n) if left[i] != right[i])
    print(f"{left_name} count {len(left)} sum {sum(left)}")
    print(f"{right_name} count {len(right)} sum {sum(right)}")
    print(f"differ {differ} of {n}")


print("HONESTY_B")
print((here / "HONESTY_B.txt").read_text(), end="")
print("HONESTY_P")
expected = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}
for name, want in expected.items():
    raw = (here / f"honesty_P_{name}.txt").read_text()
    found = [int(m.group(1)) for m in re.finditer(r"nodes (\d+)", raw)]
    got = found[-1]
    print(f"{name} nodes {got} expected {want} match {str(got == want).lower()}")
print("OFF_O")
compare("B_O_d12.rows", "P_off_O_d12.rows")
print("OFF_G")
compare("B_G_d12.rows", "P_off_G_d12.rows")
print("ON_O")
compare("B_O_d12.rows", "P_on_O_d12.rows")
print("UCI")
for line in (here / "uci_P.txt").read_text().splitlines():
    if "IdeaS25" in line:
        print(line)
print("ASAN_NM")
print((here / "asan_G100_d10.meta").read_text().splitlines()[-2])
print("asan_G100_errors", len(re.findall(r"ERROR: AddressSanitizer|runtime error:", (here / "asan_G100_d10.txt").read_text())))
print("asan_scratch_errors", len(re.findall(r"ERROR: AddressSanitizer", (here / "asan_scratch.txt").read_text())))
print("MATCH")
print((here / "match_summary.txt").read_text(), end="")
print("PREDICTION")
print((here / "prediction.txt").read_text(), end="")
