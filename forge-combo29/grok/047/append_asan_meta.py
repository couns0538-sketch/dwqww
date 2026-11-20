#!/usr/bin/env python3
"""Append the AddressSanitizer symbol count to a .meta file."""
import subprocess
import sys

exe = sys.argv[1]
meta = sys.argv[2]
nm = subprocess.run(["nm", "-C", exe], text=True, capture_output=True, check=False)
count = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
with open(meta, "a") as handle:
    handle.write(f"nm_command=nm -C {exe} | grep -c __asan_\n")
    handle.write(f"nm_asan_count={count}\n")
print(f"nm_asan_count={count}")
