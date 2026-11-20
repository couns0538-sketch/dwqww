#!/usr/bin/env python3
"""Count AddressSanitizer and UndefinedBehaviorSanitizer lines in a stderr file."""
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text(errors="replace").splitlines()
hits = [
    line
    for line in lines
    if "AddressSanitizer" in line or "UndefinedBehaviorSanitizer" in line or "runtime error:" in line
]
print(f"sanitizer_lines {len(hits)}")
for line in hits:
    print(line)
