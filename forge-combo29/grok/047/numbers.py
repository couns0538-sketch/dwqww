#!/usr/bin/env python3
"""Print the measured numbers from the raw files in this folder."""
from pathlib import Path

here = Path(__file__).resolve().parent

def read(name):
    return (here / name).read_text()

def nodes_sum(name):
    vals = [int(x) for x in (here / name).read_text().split() if x]
    return len(vals), sum(vals), vals[:3]

print("HONESTY_B")
print(read("HONESTY_B.txt"), end="")
print("HONESTY_P")
print(read("HONESTY_P.txt"), end="")
print("UCI_OPTIONS")
for line in read("uci_p.txt").splitlines():
    if "IdeaK8" in line:
        print(line)
print("COMPARE_OFF_O")
print(read("compare_off_O.txt"), end="")
print("COMPARE_OFF_G")
print(read("compare_off_G.txt"), end="")
print("COMPARE_ON_O")
print(read("compare_on_O.txt"), end="")
n, total, first = nodes_sum("P_on_O_d12.nodes")
print(f"P_ON_O positions {n} sum {total} first3 {' '.join(str(x) for x in first)}")
print("ASAN_META")
for line in read("asan_g100.meta").splitlines():
    if line.startswith("nm_") or line.startswith("positions") or line.startswith("option IdeaK8"):
        print(line)
print("asan_g100_stderr_bytes", (here / "asan_g100.stderr").stat().st_size)
stderr = read("asan_scratch.stderr")
print("asan_scratch_has_heap_buffer_overflow", "heap-buffer-overflow" in stderr)
print("MATCH_R_LAST")
rlines = read("match_r.txt").splitlines()
rstart = 0
for i, line in enumerate(rlines):
    if line.startswith("Results of"):
        rstart = i
print("\n".join(rlines[rstart:]))
print("PARTNER")
print(read("partner.txt"), end="")
print("APPLY_CHECK")
print(read("apply_check.txt"), end="")
print("MATCH_LAST")
lines = read("match_og.txt").splitlines()
for line in lines:
    if line.startswith("Results of") or line.startswith("Elo:") or line.startswith("Games:") or line.startswith("Total Time"):
        last = line
print("--- final block ---")
start = 0
for i, line in enumerate(lines):
    if line.startswith("Results of"):
        start = i
print("\n".join(lines[start:]))
