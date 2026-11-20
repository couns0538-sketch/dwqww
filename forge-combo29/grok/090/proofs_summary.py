#!/usr/bin/env python3
"""Print the proof numbers from the raw files in this folder."""
import pathlib
import subprocess

folder = pathlib.Path(__file__).resolve().parent


def nodes_of(name: str) -> str:
    found = None
    for line in (folder / name).read_text().splitlines():
        parts = line.split()
        if "nodes" in parts:
            i = parts.index("nodes")
            if i + 1 < len(parts) and parts[i + 1].isdigit():
                found = parts[i + 1]
    return str(found)


def row_sum(name: str) -> tuple[int, int]:
    rows = [line for line in (folder / name).read_text().splitlines() if line.strip()]
    return len(rows), sum(int(line.split()[1]) for line in rows)


print("honesty_p bench11", nodes_of("honesty_p_bench11.txt"))
print("honesty_p bench13", nodes_of("honesty_p_bench13.txt"))
print("honesty_p bench16", nodes_of("honesty_p_bench16.txt"))
print("honesty_p perft5", nodes_of("honesty_p_perft5.txt"))
script = folder / "compare_rows.py"
for left, right in (
    ("B_O_d12.rows", "P_off_O_d12.rows"),
    ("B_G_d12.rows", "P_off_G_d12.rows"),
    ("B_O_d12.rows", "P_on_O_d12.rows"),
):
    subprocess.run(["python3", str(script), left, right], check=True)
n, total = row_sum("P_on_O_d12.rows")
print(f"P_on_O_d12 positions {n} sum {total}")
meta = (folder / "asan_G100_d10.meta").read_text()
print("asan_G100_meta_has_nm", "nm_asan_count=" in meta)
for line in meta.splitlines():
    if line.startswith("nm_asan_count=") or line.startswith("exe="):
        print("asan_G100", line)
err = (folder / "asan_G100_d10.err").read_text()
print("asan_G100_err_bytes", len(err))
scratch = (folder / "asan_scratch.err").read_text()
print("asan_scratch_has_heap_overflow", "heap-buffer-overflow" in scratch)
print("asan_scratch_err_bytes", len(scratch))
uci = (folder / "uci_p.txt").read_text().splitlines()
for line in uci:
    if line.startswith("option name IdeaK1"):
        print(line)
