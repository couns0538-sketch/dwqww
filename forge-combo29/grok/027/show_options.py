#!/usr/bin/env python3
"""Print the new option lines from a raw uci transcript."""
import sys
from pathlib import Path

want = ("IdeaS44", "IdeaS44_Depth", "IdeaS44_Margin", "IdeaS44_History")
text = Path(sys.argv[1]).read_text(encoding="utf-8")
found = {name: "" for name in want}
for line in text.splitlines():
    if line.startswith("<< "):
        line = line[3:]
    if not line.startswith("option name "):
        continue
    parts = line.split()
    if len(parts) < 3:
        continue
    name = parts[2]
    if name in found:
        found[name] = line
for name in want:
    print(found[name] if found[name] else f"MISSING {name}")
