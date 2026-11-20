#!/usr/bin/env python3
"""Print the honesty node lines from the saved engine transcripts."""
from pathlib import Path

for path in sorted(Path(".").glob("honesty_*.txt")):
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("info string bench ") or line.startswith("nodes "):
            print(f"{path.name}: {line}")
