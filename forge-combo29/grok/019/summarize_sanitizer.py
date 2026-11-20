#!/usr/bin/env python3
"""Read the sanitizer raw files and print the two proofs."""
from pathlib import Path
S = Path("/home/ubuntu/grok_seat.txt").read_text().strip()
d = Path("/home/ubuntu/grok_repo.txt").read_text().strip()
d = Path(d) / "forge-combo29" / "grok" / S
real = (d / "asan_G100.raw.txt").read_text(errors="replace")
meta = (d / "asan_G100.raw.txt.meta").read_text()
scratch = (d / "asan_scratch.raw.txt").read_text(errors="replace")
smeta = (d / "asan_scratch.raw.txt.meta").read_text()
def count_hits(text):
    n = 0
    for line in text.splitlines():
        if "AddressSanitizer" in line or "UndefinedBehaviorSanitizer" in line or "runtime error:" in line:
            n += 1
    return n
nm = [ln for ln in meta.splitlines() if ln.startswith("nm_asan_count=")]
snm = [ln for ln in smeta.splitlines() if ln.startswith("nm_asan_count=")]
lines = [
    f"real nm {nm[0] if nm else 'MISSING'} asan_or_ubsan_lines {count_hits(real)}",
    f"scratch nm {snm[0] if snm else 'MISSING'} asan_or_ubsan_lines {count_hits(scratch)}",
    "scratch_has_heap_overflow " + ("YES" if "heap-buffer-overflow" in scratch else "NO"),
]
text = "\n".join(lines) + "\n"
(d / "SANITIZER.txt").write_text(text)
print(text, end="")
