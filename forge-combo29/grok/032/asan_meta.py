#!/usr/bin/env python3
"""Append the AddressSanitizer symbol count to a depth_set meta file.

The count is the output of: nm -C EXE | grep -c __asan_
"""
import subprocess
import sys
from pathlib import Path

exe = sys.argv[1]
meta = Path(sys.argv[2])
raw = Path(sys.argv[3]) if len(sys.argv) > 3 else None
proc = subprocess.run(["nm", "-C", exe], text=True, capture_output=True, check=False)
count = sum(1 for line in proc.stdout.splitlines() if "__asan_" in line)
text = meta.read_text() if meta.exists() else ""
extra = [
    f"nm_command=nm -C {exe} | grep -c __asan_",
    f"nm_asan_count={count}",
]
if raw is not None and raw.exists():
    body = raw.read_text(errors="replace")
    hits = [line for line in body.splitlines() if "Sanitizer" in line or "runtime error" in line]
    extra.append(f"sanitizer_lines={len(hits)}")
    extra.extend(hits[:20])
meta.write_text(text + "\n".join(extra) + "\n")
print("\n".join(extra))
