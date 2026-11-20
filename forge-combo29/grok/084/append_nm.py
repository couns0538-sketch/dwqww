#!/usr/bin/env python3
"""Append `nm -C EXE | grep -c __asan_` to a .meta file. Usage: append_nm.py EXE META"""
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1])
meta = Path(sys.argv[2])
listed = subprocess.run(["nm", "-C", str(exe)], check=True, stdout=subprocess.PIPE, text=True)
count = sum(1 for line in listed.stdout.splitlines() if "__asan_" in line)
line = f"nm_asan_count: {count}\n"
meta.write_text(meta.read_text() + line)
print(line, end="")
if count <= 0:
    raise SystemExit("asan count is 0")
