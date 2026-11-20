#!/usr/bin/env python3
"""Record the sanitizer proofs from the raw files and from nm."""
import subprocess
import sys
from pathlib import Path

folder = Path(sys.argv[1])
exe = Path(sys.argv[2])
nm = subprocess.run(["nm", "-C", str(exe)], check=True, capture_output=True, text=True)
count = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
meta = folder / "asan_G100_d10.txt.meta"
text = meta.read_text()
line = f"nm_command=nm -C {exe} | grep -c __asan_\nnm_asan_count={count}\n"
if "nm_asan_count=" not in text:
    meta.write_text(text + line)
clean = (folder / "asan_G100_d10.txt.stderr").read_text()
scratch = (folder / "asan_scratch.txt.stderr").read_text()
print(f"nm_asan_count={count}")
print(f"g100_stderr_bytes={len(clean)}")
print(f"g100_stderr_empty={clean.strip() == ''}")
print(f"scratch_has_heap_buffer_overflow={'heap-buffer-overflow' in scratch}")
print(f"scratch_stderr_bytes={len(scratch)}")
