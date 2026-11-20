#!/usr/bin/env python3
"""Print the proof numbers from the raw files in this folder. No hand-typed results."""
import sys
from pathlib import Path

folder = Path(sys.argv[1])

def bench_nodes(path):
    line = path.read_text().strip().splitlines()[-1]
    parts = line.split()
    return int(parts[parts.index("nodes") + 1])

def perft_nodes(path):
    for line in path.read_text().splitlines():
        if line.startswith("nodes "):
            return int(line.split()[1])
    return -1

def sum_file(path):
    text = path.read_text()
    out = {}
    for line in text.splitlines():
        key, value = line.split("=", 1)
        out[key] = value
    return out

def differ_line(path):
    for line in path.read_text().splitlines():
        if line.startswith("positions="):
            return line
    return "missing"

print("honesty_B")
for name, expect, kind in (
    ("honesty_b_bench11.txt", 312866, "bench"),
    ("honesty_b_bench13.txt", 862329, "bench"),
    ("honesty_b_bench16.txt", 3024920, "bench"),
    ("honesty_b_perft5.txt", 4865609, "perft"),
):
    got = perft_nodes(folder / name) if kind == "perft" else bench_nodes(folder / name)
    print(f"  {name} {got} {'OK' if got == expect else 'MISS'}")

print("honesty_P")
for name, expect, kind in (
    ("P_bench11.txt", 312866, "bench"),
    ("P_bench13.txt", 862329, "bench"),
    ("P_bench16.txt", 3024920, "bench"),
    ("P_perft5.txt", 4865609, "perft"),
):
    got = perft_nodes(folder / name) if kind == "perft" else bench_nodes(folder / name)
    print(f"  {name} {got} {'OK' if got == expect else 'MISS'}")

for label in ("B_O_d12", "B_G_d12", "P_off_O_d12", "P_off_G_d12", "P_on_O_d12"):
    info = sum_file(folder / f"{label}.sum")
    print(f"{label} sum={info['sum']} first3={info['first3']} n={info['positions']}")

print("off_O", differ_line(folder / "proof_off_O.txt"))
print("off_G", differ_line(folder / "proof_off_G.txt"))
print("on_O", differ_line(folder / "proof_on_O.txt"))

uci = (folder / "P_uci.txt").read_text().splitlines()
for line in uci:
    if "IdeaA7" in line:
        print("uci", line)

meta = (folder / "asan_G100.meta").read_text()
for line in meta.splitlines():
    if line.startswith("nm_asan_count="):
        print("asan", line)
scratch = (folder / "asan_scratch.txt").read_text().splitlines()
hits = [line for line in scratch if "runtime error" in line or "AddressSanitizer" in line]
print("scratch_sanitizer_lines", len(hits))
if hits:
    print("scratch_first", hits[0][3:] if hits[0].startswith("<< ") else hits[0])
real = (folder / "asan_G100.txt").read_text().splitlines()
real_hits = [line for line in real if "runtime error" in line or "AddressSanitizer" in line or "UndefinedBehaviorSanitizer" in line]
print("asan_G100_sanitizer_lines", len(real_hits))
