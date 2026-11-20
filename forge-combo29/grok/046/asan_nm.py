#!/usr/bin/env python3
"""Append `nm -C exe | grep -c __asan_` to a .meta file."""
import subprocess
import sys
from pathlib import Path

exe = sys.argv[1]
meta = Path(sys.argv[2])
proc = subprocess.run(["nm", "-C", exe], capture_output=True, text=True, check=False)
count = sum(1 for line in proc.stdout.splitlines() if "__asan_" in line)
meta.write_text(meta.read_text() + f"nm_command=nm -C {exe} | grep -c __asan_\nnm_asan_count={count}\n")
print(count)
