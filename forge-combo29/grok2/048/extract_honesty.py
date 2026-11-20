#!/usr/bin/env python3
"""extract_honesty.py DIR : print the last nodes field of each honesty raw file."""
import re
import sys
from pathlib import Path

d = Path(sys.argv[1])
for p in sorted(d.glob("honesty_*.txt")):
    if p.name.endswith("_uci.txt") or "table" in p.name:
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    nodes = re.findall(r"nodes (\d+)", text)
    print(f"{p.name} nodes {nodes[-1] if nodes else 'NONE'}")
