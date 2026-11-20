#!/usr/bin/env python3
"""Append `nm -C <exe> | grep -c __asan_` to a .meta file."""
import subprocess
import sys

meta = sys.argv[1]
exe = sys.argv[2]
symbols = subprocess.check_output(["nm", "-C", exe], text=True, errors="replace")
count = sum(1 for line in symbols.splitlines() if "__asan_" in line)
with open(meta, "a", encoding="utf-8") as handle:
    handle.write(f"nm_command=nm -C {exe} | grep -c __asan_\n")
    handle.write(f"nm_asan_count={count}\n")
print(count)
